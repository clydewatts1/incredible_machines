"""
M23: Data Generators & External Ingestion

Extensible generator engine registry for fetching data from external sources
(CSV files, MCP servers, etc.) and packaging it into physics payloads.

Thread-safe design: fetch_next() runs in background threads; results are
queued to the main Pygame thread via thread-safe queue.Queue().
"""

import csv
import json
import os
import queue
import threading
import asyncio
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class GeneratorExhausted(Exception):
    """Raised when a generator has no more data (e.g., CSV EOF with loop=false)."""
    pass


class BaseGenerator(ABC):
    """
    Base interface for all data generators.
    
    Subclasses must implement fetch_next() and optionally cleanup().
    """
    
    @abstractmethod
    def fetch_next(self, instructions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch one item from the data source.
        
        Args:
            instructions: Engine-specific configuration dict.
        
        Returns:
            dict: Raw data (e.g., CSV row as {"name": ..., "age": ...}).
            None: Source is empty or in "empty" state (not an error; retry later).
        
        Raises:
            Exception: On unrecoverable error (file not found, connection drop, timeout, JSON parse).
        """
        raise NotImplementedError()
    
    def cleanup(self):
        """Gracefully release resources (files, network connections, etc.)."""
        pass


class NullGenerator(BaseGenerator):
    """
    No-op generator; used as fallback for unknown engine types.
    Always returns None (empty data).
    """
    
    def fetch_next(self, instructions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return None; always empty."""
        return None
    
    def cleanup(self):
        """Nothing to clean up."""
        pass


class CSVEngine(BaseGenerator):
    """
    CSV file data generator.
    
    Reads rows from a CSV file and yields one row per fetch_next() call.
    Supports looping (restart at EOF) or exhaustion (stop at EOF).
    """
    
    def __init__(self):
        self.file_handle = None
        self.reader = None
        self.filepath = None
        self.resolved_filepath = None
        self.loop = False
        self.skip_header = True
        self.delimiter = ","
        self.debug = False
        self.rows_read = 0

    def _debug_log(self, message: str):
        if self.debug:
            print(f"[CSVEngine] {message}")
    
    def fetch_next(self, instructions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch next row from CSV file.
        
        Instructions schema:
        {
            "filepath": "data/users.csv",
            "loop": False,           # if True, restart at EOF; if False, exhaust
            "skip_header": True,     # skip first row (default True)
            "delimiter": ","         # CSV delimiter (default ",")
        }
        """
        # Initialize on first call
        if self.reader is None:
            self.filepath = instructions.get("filepath", "data.csv")
            self.resolved_filepath = os.path.abspath(self.filepath)
            self.loop = instructions.get("loop", False)
            self.skip_header = instructions.get("skip_header", True)
            self.delimiter = instructions.get("delimiter", ",")
            self.debug = bool(instructions.get("debug", False))

            self._debug_log(
                f"Initializing CSV source: filepath={self.filepath}, resolved={self.resolved_filepath}, "
                f"exists={os.path.exists(self.resolved_filepath)}, delimiter={self.delimiter!r}, loop={self.loop}"
            )
            
            try:
                self.file_handle = open(self.filepath, 'r', encoding='utf-8')
                self.reader = csv.DictReader(
                    self.file_handle,
                    delimiter=self.delimiter
                )
                self._debug_log(f"Opened CSV successfully. Fieldnames={self.reader.fieldnames}")
                # Skip header if configured
                if self.skip_header and self.reader.fieldnames:
                    pass  # DictReader automatically uses first row as fieldnames
            except FileNotFoundError as e:
                parent_dir = os.path.dirname(self.resolved_filepath) or os.getcwd()
                nearby_files = []
                if os.path.isdir(parent_dir):
                    try:
                        nearby_files = sorted(os.listdir(parent_dir))
                    except OSError:
                        nearby_files = []
                raise IOError(
                    f"CSV file not found: {self.filepath} "
                    f"(resolved: {self.resolved_filepath}; cwd: {os.getcwd()}; nearby files: {nearby_files})"
                ) from e
            except Exception as e:
                raise IOError(f"Failed to open CSV file {self.filepath}: {e}") from e
        
        try:
            # Try to read next row
            row = next(self.reader)
            self.rows_read += 1
            self._debug_log(f"Read row #{self.rows_read}: {dict(row)}")
            return dict(row)
        except StopIteration:
            # EOF reached
            if self.loop:
                self._debug_log("Reached EOF, rewinding to start because loop=true")
                # Restart from top
                self.file_handle.seek(0)
                self.reader = csv.DictReader(
                    self.file_handle,
                    delimiter=self.delimiter
                )
                try:
                    row = next(self.reader)
                    self.rows_read += 1
                    self._debug_log(f"Read row #{self.rows_read} after rewind: {dict(row)}")
                    return dict(row)
                except StopIteration:
                    # File is truly empty after restart (shouldn't happen)
                    self._debug_log("CSV is empty after rewind")
                    raise GeneratorExhausted("CSV file is empty")
            else:
                # Exhaustion: signal via exception
                self._debug_log("Reached EOF and loop=false; marking generator exhausted")
                raise GeneratorExhausted("CSV file exhausted (loop=false)")
        except Exception as e:
            raise IOError(f"Error reading CSV file: {e}") from e
    
    def cleanup(self):
        """Close the CSV file handle."""
        if self.file_handle:
            try:
                self.file_handle.close()
            except Exception:
                pass
            self._debug_log(f"Closed CSV file handle for {self.resolved_filepath or self.filepath}")
            self.file_handle = None
            self.reader = None


class MCPEngine(BaseGenerator):
    """
    MCP (Model Context Protocol) client data generator.
    
    Connects to an MCP server, invokes a tool (get_incredible_machine_data),
    and packages the returned JSON response as payload data.
    
    Supports both SSE (Server-Sent Events) and stdio transports.
    """
    
    def __init__(self):
        self.session = None
        self.session_task = None
        self.transport = None
        self.initialized = False
    
    def _get_event_loop(self):
        """Get or create event loop for current thread."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    
    def _run_async_init(self, instructions: Dict[str, Any]):
        """
        Initialize MCP session in a background event loop.
        This is called once per DataSource instance.
        """
        async def _init_async():
            try:
                transport_type = instructions.get("transport", "sse")
                
                if transport_type == "sse":
                    from mcp.client.sse import SSEClientTransport
                    url = instructions.get("url", "http://localhost:8000/sse")
                    self.transport = SSEClientTransport(url)
                elif transport_type == "stdio":
                    from mcp.client.stdio import StdioClientTransport
                    command = instructions.get("command", "mcp-server")
                    args = instructions.get("args", [])
                    self.transport = StdioClientTransport(command, args)
                else:
                    raise ValueError(f"Unknown MCP transport: {transport_type}")
                
                from mcp.client.session import ClientSession
                self.session = ClientSession(self.transport)
                await self.session.initialize()
                self.initialized = True
            except Exception as e:
                self.initialized = False
                raise e
        
        # Get event loop for this thread and run initialization
        loop = self._get_event_loop()
        loop.run_until_complete(_init_async())
    
    def fetch_next(self, instructions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch next data item from MCP server.
        
        Instructions schema:
        {
            "transport": "sse" | "stdio",     # Connection type
            "url": "http://localhost:8000/sse",  # For SSE
            "command": "mcp-server",          # For stdio
            "args": ["--config", "..."],      # For stdio
            "tool_name": "get_incredible_machine_data",
            "timeout": 5                      # Request timeout (seconds)
        }
        
        Response schema from tool:
        {
            "status": "success" | "empty" | "error",
            "data": { ... },
            "message": "..." (optional, for error context)
        }
        """
        # Initialize session on first call
        if not self.initialized:
            self._run_async_init(instructions)
        
        if not self.initialized or not self.session:
            raise RuntimeError("MCP session not initialized")
        
        # Fetch data via async call
        async def _fetch_async():
            try:
                tool_name = instructions.get("tool_name", "get_incredible_machine_data")
                timeout = float(instructions.get("timeout", 5))
                
                # Call the tool with no arguments
                result = await asyncio.wait_for(
                    self.session.call_tool(tool_name, {}),
                    timeout=timeout
                )
                
                # Parse tool response (should be JSON string in result.content[0].text)
                if result.content:
                    content_block = result.content[0]
                    if hasattr(content_block, 'text'):
                        response_json = json.loads(content_block.text)
                    else:
                        raise ValueError("Tool response missing text content")
                else:
                    raise ValueError("Tool returned empty response")
                
                # Check response status
                status = response_json.get("status", "error")
                
                if status == "success":
                    data = response_json.get("data", {})
                    return data
                elif status == "empty":
                    # AI has no new data right now; not an error
                    return None
                elif status == "error":
                    message = response_json.get("message", "Unknown error")
                    raise RuntimeError(f"Tool returned error: {message}")
                else:
                    raise ValueError(f"Unknown tool response status: {status}")
            
            except asyncio.TimeoutError:
                raise TimeoutError(f"MCP request timeout after {instructions.get('timeout', 5)}s")
            except json.JSONDecodeError as e:
                raise ValueError(f"MCP tool response JSON parse error: {e}")
            except Exception as e:
                raise e
        
        # Run async fetch in thread-local event loop
        loop = self._get_event_loop()
        return loop.run_until_complete(_fetch_async())
    
    def cleanup(self):
        """Gracefully close the MCP session."""
        if self.session:
            try:
                async def _close_async():
                    await self.session.close()
                
                loop = self._get_event_loop()
                loop.run_until_complete(_close_async())
            except Exception:
                pass
            finally:
                self.session = None
        
        if self.transport:
            try:
                self.transport.close()
            except Exception:
                pass
            self.transport = None


# Generator Registry
GENERATOR_REGISTRY = {
    "csv": CSVEngine,
    "mcp": MCPEngine,
    "null": NullGenerator,
}


def get_generator(engine_type: str, instructions: Dict[str, Any] = None) -> BaseGenerator:
    """
    Factory function to instantiate a data generator.
    
    Args:
        engine_type: "csv", "mcp", or custom registered type.
        instructions: Engine-specific configuration (optional; can be passed to fetch_next).
    
    Returns:
        BaseGenerator: Instantiated generator; NullGenerator if type unknown.
    """
    engine_class = GENERATOR_REGISTRY.get(engine_type, NullGenerator)
    return engine_class()
