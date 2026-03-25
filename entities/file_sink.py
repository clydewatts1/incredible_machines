import os
import json
import time
from typing import Any, Dict, List, Optional
import pymunk

import constants
from entities.base import GamePart, FlowEntity

class FileSink(FlowEntity):
    """
    Milestone 40: Data Exporter Sink.
    Writes payload data to JSON files in a specified directory.
    """
    can_accept_input = True
    can_provide_output = False

    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "file_sink"):
        super().__init__(space, x, y, variant_name)
        
        # Default Properties
        self.properties.setdefault("output_directory", "exports/synthetic_data")
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)
        self.visual_state = "IDLE"

    def ingest_payload(self, payload_entity: GamePart, active_instances: Dict[str, Any] = None, **kwargs) -> bool:
        print(f"DEBUG: FileSink {self.uuid} Ingesting payload {payload_entity.uuid}...")
        # 1. Get properties
        out_dir = str(self.get_property("output_directory", "exports/synthetic_data"))
        
        # 2. Extract Data
        data = {}
        if hasattr(payload_entity, "payload"):
            # If payload has a nested 'data' field (common for processed records), use that.
            # Otherwise, use the top-level payload dict.
            data = payload_entity.payload.get("data", payload_entity.payload)
            print(f"DEBUG: FileSink {self.uuid} Extracted data: {data}")
            
        # 3. Write to File
        try:
            os.makedirs(out_dir, exist_ok=True)
            # Use UUID for unique filenames to avoid collisions
            filename = f"record_{payload_entity.uuid}.json"
            filepath = os.path.join(out_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
            print(f"DEBUG: FileSink {self.uuid} Successfully exported to {filepath}")
            self.flash_timer = 15
        except Exception as e:
            print(f"ERROR: FileSink {self.uuid} failed to export: {e}")
            self.visual_state = "FATAL"
            
        # 4. Consume the ball (remove from world)
        payload_entity.to_delete = True
        return True

    def draw(self, surface, camera=None, **kwargs):
        super().draw(surface, camera, **kwargs)
        # Optional overlay: "EXPORT" text
        pass
