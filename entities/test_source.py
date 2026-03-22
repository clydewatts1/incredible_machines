import json
import os
import copy
import pymunk
from typing import Any, Dict, List, Optional
from entities.source import DataSource

class TestSourcePart(DataSource):
    """
    Specialized data source for automated testing.
    Reads inputs.json and emits payloads at specific physics ticks.
    """
    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "test_source"):
        super().__init__(space, x, y, variant_name)
        self.scheduled_inputs = []
        self.last_tick_processed = -1
        self.test_dir = None

    def load_inputs(self, test_dir: str):
        self.test_dir = test_dir
        input_path = os.path.join(test_dir, "inputs.json")
        if os.path.exists(input_path):
            try:
                with open(input_path, "r") as f:
                    data = json.load(f)
                    # Milestone 35 Refinement: Support nested payload_events or flat list
                    if isinstance(data, dict):
                        self.scheduled_inputs = data.get("payload_events", [])
                    else:
                        self.scheduled_inputs = data
                print(f"TestSource {self.uuid}: Loaded {len(self.scheduled_inputs)} scheduled inputs from {input_path}")
            except Exception as e:
                print(f"TestSource {self.uuid}: Error loading inputs.json: {e}")
        else:
            print(f"TestSource {self.uuid}: No inputs.json found in {test_dir}")

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[Any], active_instances: Optional[Dict[str, Any]] = None):
        if game_state.get("mode") != "PLAY":
            return

        current_tick = game_state.get("tick", 0)
        
        # Check for scheduled inputs at this tick
        # Note: multiple inputs can happen at the same tick
        for entry in self.scheduled_inputs:
            target_tick = entry.get("tick", 0)
            if target_tick == current_tick and current_tick > self.last_tick_processed:
                payload_data = entry.get("payload", {})
                print(f"TestSource {self.uuid}: Emitting scheduled payload at tick {current_tick}")
                self._emit_scheduled_payload(payload_data, entities, active_instances or {})
        
        # update last_tick_processed after the loop to allow multiple entries at same tick
        if current_tick > self.last_tick_processed:
            self.last_tick_processed = current_tick
                
        # We don't call super().update_logic to bypass timer-based emission
        if self.visual_state == "EMITTING":
            # Just a short flash or similar, usually handled by update_visual
            pass 

    def _emit_scheduled_payload(self, payload_data: Dict[str, Any], entities: List[Any], active_instances: Dict[str, Any]):
        from main import create_part
        
        variant = str(self.get_property("output_variant", "payload_ball"))
        ball = create_part(self.space, self.body.position.x, self.body.position.y, variant)
        
        if ball:
            # Inject the test data
            if hasattr(ball, "payload"):
                ball.payload = copy.deepcopy(payload_data)
                ball.payload["origin_uuid"] = self.uuid
            
            entities.append(ball)
            if hasattr(ball, 'uuid'):
                active_instances[ball.uuid] = ball
            
            # Hybrid Routing: Pipe > Vector fallback
            # Uses state '10' for standardized emission
            self.resolve_exit_path(ball, 10, entities, active_instances)

            # Recording Hook
            import builtins
            if hasattr(builtins, "register_record_input"):
                builtins.register_record_input(ball.payload)
                
        self.visual_state = "EMITTING"
