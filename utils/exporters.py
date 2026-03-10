"""
M24: Data exporters and registry.

Provides file exporters (CSV/JSON/YAML) with strict rotation and an MCP exporter
for external egestion. Exporters are intentionally isolated from Pygame/Pymunk
state and are safe to execute only from background worker threads.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Type

import yaml

import constants


class BaseExporter(ABC):
    """Standard interface contract for all exporters."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def export(self, data_item: Dict[str, Any]) -> None:
        raise NotImplementedError()

    def flush(self) -> None:
        """Flush any buffered writes."""

    def cleanup(self) -> None:
        """Release resources such as file handles or network sessions."""

    def validate_config(self) -> bool:
        return True


class NullExporter(BaseExporter):
    """No-op exporter used as a graceful fallback."""

    def export(self, data_item: Dict[str, Any]) -> None:
        return


class BaseFileExporter(BaseExporter):
    """Shared file rotation behavior for local file exporters."""

    file_extension = "txt"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.directory = str(self.config.get("directory", constants.SINK_EXPORT_DIR))
        self.file_prefix = str(self.config.get("file_prefix", "sink_output"))
        self.max_objects = int(self.config.get("max_objects", constants.SINK_ROTATION_MAX_OBJECTS))
        self.rotation_seconds = float(self.config.get("rotation_seconds", constants.SINK_ROTATION_SECONDS))

        if self.max_objects <= 0:
            raise ValueError("max_objects must be > 0")
        if self.rotation_seconds <= 0.0:
            raise ValueError("rotation_seconds must be > 0")

        self.file_handle = None
        self.current_path = None
        self.object_count = 0
        self.file_start_time = 0.0
        self.rotation_index = 0

        self._ensure_directory()
        self._open_new_file()

    def _ensure_directory(self) -> None:
        try:
            os.makedirs(self.directory, exist_ok=True)
        except Exception as exc:
            raise OSError(f"Failed to create export directory '{self.directory}': {exc}") from exc

        if not os.access(self.directory, os.W_OK):
            raise PermissionError(f"Export directory is not writable: {self.directory}")

    def _build_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"{self.rotation_index:03d}"
        return f"{self.file_prefix}_{timestamp}_{suffix}.{self.file_extension}"

    def _open_new_file(self) -> None:
        self.rotation_index += 1
        filename = self._build_filename()
        self.current_path = os.path.join(self.directory, filename)
        try:
            self.file_handle = open(self.current_path, "a", encoding="utf-8", newline="")
        except Exception as exc:
            raise OSError(f"Failed to open export file '{self.current_path}': {exc}") from exc
        self.object_count = 0
        self.file_start_time = time.time()
        self._on_file_opened()

    def _on_file_opened(self) -> None:
        """Hook for subclasses when a new rotated file is opened."""

    def _close_file(self) -> None:
        if self.file_handle is None:
            return
        try:
            self.file_handle.flush()
        finally:
            self.file_handle.close()
            self.file_handle = None

    def _should_rotate(self, now_secs: float) -> bool:
        return (
            self.object_count >= self.max_objects
            or (now_secs - self.file_start_time) >= self.rotation_seconds
        )

    def _rotate_if_needed(self) -> None:
        now_secs = time.time()
        if self._should_rotate(now_secs):
            self._close_file()
            self._open_new_file()

    def flush(self) -> None:
        if self.file_handle:
            self.file_handle.flush()

    def cleanup(self) -> None:
        self._close_file()


class CSVExporter(BaseFileExporter):
    file_extension = "csv"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._fieldnames = None
        self._writer = None
        super().__init__(config)

    def _on_file_opened(self) -> None:
        self._writer = None

    @staticmethod
    def _to_row(data_item: Dict[str, Any]) -> Dict[str, Any]:
        row: Dict[str, Any] = {}
        for key, value in data_item.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value, ensure_ascii=True)
            else:
                row[key] = value
        return row

    def export(self, data_item: Dict[str, Any]) -> None:
        self._rotate_if_needed()
        row = self._to_row(data_item)

        if self._fieldnames is None:
            self._fieldnames = sorted(row.keys())

        if any(k not in self._fieldnames for k in row.keys()):
            # Promote new keys by rotating to a fresh file with a stable header.
            self._fieldnames = sorted(set(self._fieldnames).union(row.keys()))
            self._close_file()
            self._open_new_file()

        if self._writer is None:
            self._writer = csv.DictWriter(self.file_handle, fieldnames=self._fieldnames, extrasaction="ignore")
            self._writer.writeheader()

        self._writer.writerow(row)
        self.object_count += 1


class JSONExporter(BaseFileExporter):
    file_extension = "jsonl"

    def export(self, data_item: Dict[str, Any]) -> None:
        self._rotate_if_needed()
        self.file_handle.write(json.dumps(data_item, ensure_ascii=True) + "\n")
        self.object_count += 1


class YAMLExporter(BaseFileExporter):
    file_extension = "yaml"

    def export(self, data_item: Dict[str, Any]) -> None:
        self._rotate_if_needed()
        self.file_handle.write("---\n")
        yaml.safe_dump(data_item, self.file_handle, sort_keys=False)
        self.object_count += 1


class MCPExporter(BaseExporter):
    """Official MCP exporter supporting SSE and stdio transports."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.transport_type = str(self.config.get("transport", "sse")).lower()
        self.tool_name = str(self.config.get("tool_name", "post_incredible_machine_data"))
        self.timeout = float(self.config.get("timeout", constants.SINK_MCP_TIMEOUT_SECONDS))

        self.session = None
        self.transport = None
        self.loop = asyncio.new_event_loop()
        self.initialized = False

        # Keep import local and optional so file exporters work even if mcp is unavailable.
        try:
            from mcp.client.session import ClientSession  # type: ignore

            self._client_session_class = ClientSession
        except Exception as exc:
            raise RuntimeError(f"Failed to import MCP ClientSession: {exc}") from exc

        try:
            from mcp.shared.exceptions import McpError  # type: ignore

            self._mcp_error_type = McpError
        except Exception:
            self._mcp_error_type = Exception

    def _run(self, coro):
        asyncio.set_event_loop(self.loop)
        return self.loop.run_until_complete(coro)

    async def _initialize_async(self) -> None:
        if self.initialized:
            return

        try:
            if self.transport_type == "sse":
                from mcp.client.sse import SSEClientTransport  # type: ignore

                url = str(self.config.get("url", "")).strip()
                if not url:
                    raise ValueError("MCP SSE transport requires 'url'")
                self.transport = SSEClientTransport(url)
            elif self.transport_type == "stdio":
                from mcp.client.stdio import StdioClientTransport  # type: ignore

                command = str(self.config.get("command", "")).strip()
                if not command:
                    raise ValueError("MCP stdio transport requires 'command'")
                args = self.config.get("args", [])
                if not isinstance(args, list):
                    raise ValueError("MCP stdio 'args' must be a list")
                self.transport = StdioClientTransport(command, args)
            else:
                raise ValueError(f"Unsupported MCP transport: {self.transport_type}")

            self.session = self._client_session_class(self.transport)
            await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
            self.initialized = True
        except Exception as exc:
            raise RuntimeError(f"MCP initialization failed: {exc}") from exc

    @staticmethod
    def _extract_status(result: Any) -> str:
        if isinstance(result, dict):
            return str(result.get("status", "success")).lower()

        content = getattr(result, "content", None)
        if isinstance(content, list) and content:
            first = content[0]
            text = getattr(first, "text", None)
            if isinstance(text, str):
                try:
                    parsed = json.loads(text)
                    return str(parsed.get("status", "success")).lower()
                except json.JSONDecodeError:
                    pass

        is_error = bool(getattr(result, "isError", False))
        return "error" if is_error else "success"

    async def _export_async(self, data_item: Dict[str, Any]) -> None:
        await self._initialize_async()

        payload_data = data_item.get("data", {})
        if not isinstance(payload_data, dict):
            payload_data = {"value": payload_data}

        try:
            result = await asyncio.wait_for(
                self.session.call_tool(self.tool_name, payload_data),
                timeout=self.timeout,
            )
            status = self._extract_status(result)
            if status not in ("success", "ok"):
                raise RuntimeError(f"MCP tool returned non-success status: {status}")
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"MCP export timeout after {self.timeout}s") from exc
        except self._mcp_error_type as exc:  # type: ignore[misc]
            raise RuntimeError(f"MCP export failed: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"MCP export failed: {exc}") from exc

    def export(self, data_item: Dict[str, Any]) -> None:
        self._run(self._export_async(data_item))

    def flush(self) -> None:
        # No buffered batch in current implementation.
        return

    async def _cleanup_async(self) -> None:
        if self.session is not None:
            close_fn = getattr(self.session, "close", None)
            if callable(close_fn):
                await close_fn()
            self.session = None

        if self.transport is not None:
            close_fn = getattr(self.transport, "close", None)
            if callable(close_fn):
                maybe_coro = close_fn()
                if asyncio.iscoroutine(maybe_coro):
                    await maybe_coro
            self.transport = None

    def cleanup(self) -> None:
        try:
            self._run(self._cleanup_async())
        finally:
            if not self.loop.is_closed():
                self.loop.close()
            self.initialized = False


EXPORTER_REGISTRY: Dict[str, Type[BaseExporter]] = {
    "csv": CSVExporter,
    "json": JSONExporter,
    "yaml": YAMLExporter,
    "mcp": MCPExporter,
    "null": NullExporter,
}


def get_exporter(exporter_type: str, config: Optional[Dict[str, Any]] = None) -> BaseExporter:
    exporter_class = EXPORTER_REGISTRY.get(str(exporter_type).lower(), NullExporter)
    return exporter_class(config or {})
