
import os
import sys
import pygame
import pymunk
import yaml

# Mocking some parts of the environment
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Add project root to sys.path
sys.path.append(os.getcwd())

import constants
from entities.base import GamePart
from entities.sink import DataSink
from entities.payloadball import PayloadBallPart
from utils.physics_events import CollisionManager
from utils.level_manager import LevelManager
# Note: create_part in main.py uses absolute imports that might be tricky if not careful
# but we are in the same environment.
from main import create_part

def test_repro():
    pygame.init()
    space = pymunk.Space()
    space.gravity = (0, 900)
    
    entities = []
    active_instances = {}
    signal_queue = []
    
    collision_manager = CollisionManager(entities, active_instances, signal_queue)
    collision_manager.setup(space)
    
    level_manager = LevelManager()
    yaml_path = r"c:\Users\cw171001\OneDrive - Teradata\Documents\GitHub\incredible_machines\saves\defect_source_to_sink_drop\defect_source_to_sink_drop.yaml"
    
    level_data, constraints_data, connections_data, metadata = level_manager.load_level(yaml_path)
    
    for data in level_data:
        variant_key = data.get("entity_id")
        pos = data.get("position")
        new_part = create_part(space, pos["x"], pos["y"], variant_key)
        new_part.uuid = data.get("uuid")
        if "overrides" in data:
            new_part.apply_draft_overrides(data["overrides"])
        if variant_key == "data_sink_csv":
             new_part.overrides["accepts_types"] = ["bouncy_ball", "payload_ball"]
             new_part.overrides["active_sides"] = ["top"]
        entities.append(new_part)
        active_instances[new_part.uuid] = new_part
        # print(f"Created {variant_key} at {pos}")

    # Find the sink and ball
    sink = next(e for e in entities if isinstance(e, DataSink))
    # Ball is bouncy_ball in YAML but could be payload_ball
    balls = [e for e in entities if isinstance(e, (PayloadBallPart, GamePart)) and e.variant_key in ("bouncy_ball", "payload_ball")]
    if not balls:
        print("No balls found in YAML.")
        return False
    ball = balls[0]
    
    print(f"Sink UUID: {sink.uuid}, Ball UUID: {ball.uuid}, Ball variant: {ball.variant_key}")
    print(f"Sink visual state: {sink.visual_state}")
    
    # Run simulation
    dt = 1/60.0
    for i in range(200): # 3.3 seconds
        if i == 0:
            ball.body.position = (sink.body.position.x, sink.body.position.y - 120)
            ball.body.velocity = (0, 0)
            print(f"Repositioned ball to {ball.body.position} (above sink)")

        for e in entities:
            if hasattr(e, 'update_logic'):
                e.update_logic(dt, {"mode": "PLAY"}, entities, active_instances)
        
        space.step(dt)
        
        if getattr(ball, 'is_hidden', False):
            print(f"SUCCESS: Ball ingested at step {i}!")
            print(f"Sink visual state: {sink.visual_state}")
            return True
            
        if i % 20 == 0:
            pass # print(f"Step {i}: Ball pos={ball.body.position}, Sink state={sink.visual_state}")

    print("FAILURE: Ball was not ingested.")
    print(f"Final Ball pos: {ball.body.position}, Sink top sensor expected at roughly {sink.body.position.y - 50}")
    return False

if __name__ == "__main__":
    test_repro()
