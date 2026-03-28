import pygame
import pymunk
import sys
import os
import math
import tkinter as tk
from tkinter import filedialog
import argparse
import time
import glob
import json
import copy
import csv
import pygame_gui
from pygame_gui.windows import UIMessageWindow

import constants
from agent_engine import FactoryPart

# --- Register Collision Types Dynamically if missing ---
if not hasattr(constants, 'COLLISION_TYPE_WAREHOUSE'):
    constants.COLLISION_TYPE_WAREHOUSE = 10
if not hasattr(constants, 'COLLISION_TYPE_PORTAL'):
    constants.COLLISION_TYPE_PORTAL = 11

from entities.base import GamePart

from entities.source import DataSource
from entities.mechanicalpart import MechanicalPart
from entities.sink import DataSink
from entities.guard import GuardPart
from entities.data_pipe import DataPipePart, get_pipe_curve_point
from entities.axle import AxlePart
from entities.brain import BrainPart
from entities.warehouse import WarehousePart
from entities.portal import PortalPart
from entities.payloadball import PayloadBallPart
from entities.textbox import TextBoxPart
from entities.splitter import SmartSplitterPart
from entities.test_source import TestSourcePart
from entities.faker_source import FakerSource
from entities.file_sink import FileSink
from entities.effect_box import EffectBoxPart
from entities.pressure_plate import PressurePlatePart
from entities.avatar import AvatarPart

from utils.sound_manager import sound_manager
from utils.environment_manager import env_manager
from utils.config_loader import load_all_variants
from utils.level_manager import LevelManager
from utils.camera import Camera
from utils.physics_events import CollisionManager
from utils.editor_ui import EditorUI, create_icon_surface
from utils.asset_manager import asset_manager
from utils.visual_fx_manager import visual_fx_manager
from utils.icon_manager import icon_manager
from utils.sprite_manager import sprite_manager
from utils.controller import controller_manager

UI_TOP_HEIGHT = 50
UI_BOTTOM_HEIGHT = 40
UI_SIDE_WIDTH = 260
UI_RIGHT_SIDE_WIDTH = 320
payload_pool = [] # Milestone 34: Global Object Pool for Payload Recycling

def create_boundaries(space, world_width, world_height, playable_rect=None):
    static_body = space.static_body
    thickness = 50.0  # Thick walls prevent high-speed balls from tunneling through

    # Milestone 35 Fix: Boundaries are now at the WORLD limits, not the viewport.
    left = 0
    right = world_width
    top = 0
    bottom = world_height
    
    segments = [
        pymunk.Segment(static_body, (left, bottom + thickness), (right, bottom + thickness), thickness), 
        pymunk.Segment(static_body, (left - thickness, top), (left - thickness, bottom), thickness), 
        pymunk.Segment(static_body, (right + thickness, top), (right + thickness, bottom), thickness), 
        pymunk.Segment(static_body, (left, top - thickness), (right, top - thickness), thickness)  
    ]
    
    for s in segments:
        s.elasticity = 0.8
        s.friction = 0.5
        space.add(s)

def create_icon_surface(variant_key, variant_data):
    # Try to use the new IconManager, fallback if not fully linked
    try:
        from utils.icon_manager import icon_manager
        label = variant_data.get("label", variant_key.replace("_", " ").title())
        return icon_manager.get_icon(variant_key, label)
    except ImportError:
        from utils.asset_manager import asset_manager
        label = variant_data.get("label", variant_key.replace("_", " ").title())
        icon_path = f"assets/icons/{variant_key}_button.png"
        
        if variant_data.get("template") == "Circle" and not os.path.exists(icon_path):
            return asset_manager.get_image(icon_path, fallback_size=(40, 40), text_label="⚙")
        return asset_manager.get_image(icon_path, fallback_size=(40, 40), text_label=label)

def create_part(space, x, y, variant_key):
    if variant_key == "logic_factory":
        part = FactoryPart(space, x, y, variant_key)
        if hasattr(part, 'shape') and part.shape:
            part.shape.collision_type = constants.COLLISION_TYPE_FACTORY_TOP
        return part
    elif variant_key == "ai_brain":
        part = BrainPart(space, x, y, variant_key)
        if hasattr(part, 'shape') and part.shape:
            part.shape.collision_type = constants.COLLISION_TYPE_FACTORY_TOP
        return part
    elif variant_key == "smart_splitter" or variant_key.startswith("smart_splitter"):
        return SmartSplitterPart(space, x, y, variant_key)
    elif variant_key == "warehouse" or variant_key.startswith("warehouse"):
        part = WarehousePart(space, x, y, variant_key)
        if hasattr(part, 'shape') and part.shape:
            part.shape.collision_type = constants.COLLISION_TYPE_WAREHOUSE
        return part
    elif variant_key == "portal" or variant_key.startswith("portal"):
        part = PortalPart(space, x, y, variant_key)
        if hasattr(part, 'shape') and part.shape:
            part.shape.collision_type = constants.COLLISION_TYPE_PORTAL
        return part
    elif variant_key == "payload_ball":
        if payload_pool:
            ball = payload_pool.pop(0)
            ball.body.position = (x, y)
            ball.body.velocity = (0, 0)
            ball.body.angular_velocity = 0
            ball.is_hidden = False
            ball.to_delete = False
            if hasattr(ball, 'payload'):
                if isinstance(ball.payload, dict):
                    ball.payload.clear()
                else:
                    ball.payload = {}
            if hasattr(ball, 'trace_history'):
                ball.trace_history.clear()
            if hasattr(ball, 'trace_timer'):
                ball.trace_timer = 0.0
            # Re-add to space
            if ball.body not in space.bodies:
                space.add(ball.body)
            if hasattr(ball, 'shape') and ball.shape not in space.shapes:
                space.add(ball.shape)
            return ball
        return PayloadBallPart(space, x, y, variant_key)
    elif variant_key == "data_source" or variant_key == "data_source_csv" or variant_key == "data_source_mcp":
        return DataSource(space, x, y, variant_key)
    elif variant_key == "faker_source":
        return FakerSource(space, x, y, variant_key)
    elif variant_key == "test_source":
        return TestSourcePart(space, x, y, variant_key)
    elif variant_key == "file_sink" or variant_key.startswith("data_sink"):
        if variant_key == "file_sink":
            return FileSink(space, x, y, variant_key)
        return DataSink(space, x, y, variant_key)
    elif variant_key in ("gear_driver", "gear_follower"):
        return MechanicalPart(space, x, y, variant_key) 
    elif variant_key == "axle":
        return AxlePart(space, x, y, variant_key)
    elif variant_key == "data_pipe":
        return DataPipePart(space, x, y, variant_key)
    elif variant_key == "guard":
        return GuardPart(space, x, y, variant_key)
    elif variant_key == "faker_factory":
        return FactoryPart(space, x, y, variant_key)
    elif variant_key == "text_box":
        return TextBoxPart(space, x, y, variant_key)
    elif variant_key == "effect_box":
        return EffectBoxPart(space, x, y, variant_key)
    elif variant_key == "pressure_plate":
        return PressurePlatePart(space, x, y, variant_key)
    elif variant_key == "avatar":
        return AvatarPart(space, x, y, variant_key)
        
    return GamePart(space, x, y, variant_key)

def sweep_orphaned_connections(deleted_uuid, entities):
    """Milestone 34: Global Garbage Collection for machine connections."""
    if not deleted_uuid:
        return
        
    for entity in entities:
        # 1. Handshake Sweep
        if hasattr(entity, 'connected_uuids') and isinstance(entity.connected_uuids, list):
            if deleted_uuid in entity.connected_uuids:
                entity.connected_uuids.remove(deleted_uuid)
                
        # 2. Routing/Pipe Sweep
        if hasattr(entity, 'target_uuid') and entity.target_uuid == deleted_uuid:
            entity.target_uuid = None
            
        # 3. Property-based UUID Sweep (strings)
        if hasattr(entity, 'properties') and isinstance(entity.properties, dict):
            for key, value in entity.properties.items():
                if value == deleted_uuid:
                    entity.properties[key] = ""

from utils.visual_utils import get_wire_curve_point


def snap_to_grid(world_x, world_y):
    snapped_x = round(world_x / constants.GRID_SIZE) * constants.GRID_SIZE
    snapped_y = round(world_y / constants.GRID_SIZE) * constants.GRID_SIZE
    return (snapped_x, snapped_y)

def parse_args():
    parser = argparse.ArgumentParser(description="Incredible Machines Clone CLI")
    parser.add_argument("-l", "--load", type=str, help="Path to a YAML model file to load on startup")
    parser.add_argument("-s", "--state", type=str, choices=["PLAY", "EDIT"], default="EDIT", help="Initial game state mode (default: EDIT)")
    parser.add_argument("--timeout", type=float, help="Countdown timer in minutes. If reached, the game triggers the quit sequence.")
    parser.add_argument("-d", "--dump", type=str, help="Filename to save the current world configuration upon exit.")
    parser.add_argument("-t", "--test", type=str, help="Run automated test(s). Supports wildcards (e.g. 'sort_*' or 'all').")
    parser.add_argument("-v", "--visible", action="store_true", help="Make tests visible (render Pygame window).")
    parser.add_argument("--replay", type=str, help="Replay a failure trace from a specific test.")
    return parser.parse_args()

def resolve_test_paths(pattern: str) -> list[str]:
    """Resolves wildcard patterns against the tests/ directory."""
    if pattern.lower() == "all":
        pattern = "*"
    
    search_path = os.path.join("tests", pattern)
    matches = glob.glob(search_path)
    return [m for m in matches if os.path.isdir(m) and any(f.endswith('.yaml') for f in os.listdir(m))]

def main():
    global UI_TOP_HEIGHT, UI_BOTTOM_HEIGHT, UI_SIDE_WIDTH, UI_RIGHT_SIDE_WIDTH

    args = parse_args()

    # Milestone 35: Headless Execution
    if args.test and not args.visible:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        print("CLI: Running in HEADLESS mode.")

    pygame.init()
    
    # Milestone 42 Fix: Initialize and hide Tkinter root window
    # This prevents TclError when calling modal dialogs like filedialog
    root = tk.Tk()
    root.withdraw()

    try:
        pygame.joystick.init()
        controller_manager.init_joystick()
    except pygame.error as e:
        print(f"Controller: Joystick system could not be initialized: {e}")
    sound_manager.initialize()
    env_manager.initialize(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)

    window_width = env_manager.get_int("window_width", constants.WINDOW_WIDTH)
    window_height = env_manager.get_int("window_height", constants.WINDOW_HEIGHT)
    world_width = env_manager.get_int("world_width", constants.WORLD_WIDTH)
    world_height = env_manager.get_int("world_height", constants.WORLD_HEIGHT)
    
    # Milestone 42 Follow-up: Initialize camera early but update its dimensions later
    camera = Camera(world_width, world_height, window_width, window_height)
    
    UI_TOP_HEIGHT = env_manager.get_int("ui_top_height", UI_TOP_HEIGHT)
    UI_BOTTOM_HEIGHT = env_manager.get_int("ui_bottom_height", UI_BOTTOM_HEIGHT)
    UI_SIDE_WIDTH = env_manager.get_int("ui_left_panel_width", UI_SIDE_WIDTH)
    UI_RIGHT_SIDE_WIDTH = env_manager.get_int("ui_right_panel_width", UI_RIGHT_SIDE_WIDTH)
    
    all_variants = load_all_variants()
    
    if "payload_ball" not in all_variants:
        all_variants["payload_ball"] = {
            "label": "Payload Ball",
            "category": "payloads",
            "template": "Circle"
        }
    
    if "wire_tool" not in all_variants:
        all_variants["wire_tool"] = {
            "label": "Wire Logic",
            "category": "logic",
            "template": "Rectangle",
            "color": [255, 255, 0]
        }
    if "belt_tool" not in all_variants:
        all_variants["belt_tool"] = {
            "label": "Belt Connector",
            "category": "mechanical",
            "template": "Rectangle",
            "color": [60, 60, 60]
        }
    # === ADD THE DATA PIPE TO THE PALETTE ===
    if "pipe_tool" not in all_variants:
        all_variants["pipe_tool"] = {
            "label": "Data Pipe",
            "category": "logic",
            "template": "Rectangle",
            "color": [100, 200, 255]
        }

    categories = sorted({
        str(variant_data.get("category", "other")).lower()
        for variant_data in all_variants.values()
    })
    
    screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption("Fuath an Mhadra (Wolf Bane):  Mechanical 2 D Simulated Agentic Workflow")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 16)

    w, h = window_width, window_height
    game_state = {
        "mode": args.state,
        "active_tool": None,
        "snap_to_grid": False,
        "show_grid": True,
        "show_traces": False,
        "selected_instance": None,
        "selected_category": "all",
        "wiring_source": None,
        "belt_source": None,
        "pipe_source": None,
        "name": "New Flow",
        "description": "Initial flow description.",
        "speed_multiplier": 1.0,
        "is_dirty": False,
        "last_change_time": 0, # Initialized here
        "gravity": [0, 900],
        "damping": 0.99,
        "wind": [0, 0],
        "tick": 0,                      # Milestone 35: Deterministic tick counter
        "test_mode": False,             # Flag for test-specific logic
        "active_test_name": ""          # Name of current test running
    }

    level_manager = LevelManager()

    def run_replay_mode(test_name):
        """Milestone 35: Replay frame-by-frame physics trace."""
        test_dir = os.path.join("tests", test_name)
        yaml_path = os.path.join(test_dir, f"{test_name}.yaml")
        trace_path = os.path.join(test_dir, "failure_trace.json")
        
        if not os.path.exists(yaml_path) or not os.path.exists(trace_path):
            print(f"REPLAY Error: Missing YAML or trace JSON in {test_dir}")
            return
            
        with open(trace_path, "r") as f:
            trace_data = json.load(f)
            
        # Load Level
        level_data, c_data, conn_data, meta = level_manager.load_level(yaml_path)
        apply_level_data(level_data, c_data, conn_data, meta)
        
        game_state["mode"] = "PAUSE"
        print(f"REPLAY: Loaded trace for '{test_name}' ({len(trace_data)} frames). Press SPACE to step.")
        
        frame_idx = 0
        running = True
        while running:
            # 1. Handle Events
            for event in pygame.event.get():
                # Milestone 42 Resizing Fix: Intelligent Capping
                if event.type == pygame.VIDEORESIZE:
                    # User clarification: Cap size at (world_width or 5000) + panels
                    limit_w = min(5000, world_width)
                    limit_h = min(5000, world_height)
                    
                    panels_w = editor_ui.side_w + editor_ui.right_w
                    panels_h = editor_ui.top_h + editor_ui.bot_h
                    
                    target_w = min(event.w, limit_w + panels_w)
                    target_h = min(event.h, limit_h + panels_h)
                    
                    # Re-apply mode to resize/cap the window if needed
                    if (target_w, target_h) != (window_width, window_height):
                        screen = pygame.display.set_mode((target_w, target_h), pygame.RESIZABLE)
                        window_width, window_height = target_w, target_h
                        editor_ui.update_resolution(window_width, window_height)
                        camera.screen_width = editor_ui.playable_rect.width
                        camera.screen_height = editor_ui.playable_rect.height
                    continue

                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: frame_idx = (frame_idx + 1) % len(trace_data)
                    if event.key == pygame.K_r: frame_idx = 0

            # 2. Update existing entities from trace
            current_frame = trace_data[frame_idx]
            trace_uuids = {snap["uuid"] for snap in current_frame}
            
            # Sync existing
            for e in list(entities):
                snap = next((s for s in current_frame if s["uuid"] == str(getattr(e, "uuid", ""))), None)
                if snap:
                    e.body.position = tuple(snap["pos"])
                    e.body.angle = snap["angle"]
                    e.visual_state = snap["state"]
                    e.is_hidden = snap.get("is_hidden", False)
                elif hasattr(e, "uuid") and str(e.uuid) not in trace_uuids:
                    # Not in this frame's trace (e.g. dynamic part not yet spawned or already deleted)
                    e.is_hidden = True 

            # Create missing (payloads spawned mid-sim)
            for snap in current_frame:
                if snap["uuid"] not in active_instances:
                    new_part = create_part(space, snap["pos"][0], snap["pos"][1], snap["variant"])
                    if new_part:
                        new_part.uuid = snap["uuid"]
                        new_part.body.angle = snap["angle"]
                        new_part.visual_state = snap["state"]
                        new_part.is_hidden = snap["is_hidden"]
                        entities.append(new_part)
                        active_instances[new_part.uuid] = new_part

            # 3. Draw
            screen.fill((20, 20, 35))
            for entity in entities:
                if not getattr(entity, 'is_hidden', False):
                    if hasattr(entity, 'update_visual'):
                        entity.update_visual(screen, camera=camera)
            
            # Overlay info
            info_text = font.render(f"REPLAY: {test_name} | Frame: {frame_idx}/{len(trace_data)} (SPACE: Step, R: Reset)", True, (255, 255, 0))
            screen.blit(info_text, (UI_SIDE_WIDTH + 20, UI_TOP_HEIGHT + 20))
            
            pygame.display.flip()
            clock.tick(30)
    
    def handle_flow_settings():
        game_state["selected_instance"] = "GLOBAL_FLOW"
        game_state["is_creating_new"] = False
        editor_ui.rebuild_left_inspector()

    def handle_save_flow(name, desc, gravity=[0, 900], damping=0.99, wind=[0, 0]):
        if not name or name.strip() == "":
            print("Save Flow Error: Name cannot be empty.")
            return

        # If we were in "NEW" mode, clear the canvas now that we have a name
        if game_state.get("is_creating_new"):
            handle_clear()
            game_state["is_creating_new"] = False

        game_state["name"] = name
        game_state["description"] = desc
        game_state["gravity"] = gravity
        game_state["damping"] = damping
        game_state["wind"] = wind
        
        env_manager.active_project = name.replace(" ", "_")
        env_manager.active_flow_name = name
        env_manager.active_flow_description = desc
        
        # Apply physics to space
        space.gravity = tuple(gravity)
        space.damping = damping
        
        # Sync UI then save
        editor_ui.sync_ui_to_state()
        handle_quick_save()
        game_state["selected_instance"] = None
        editor_ui.rebuild_left_inspector()
        editor_ui.rebuild_top_panel()

    recorded_inputs = []
    recorded_outputs = []

    import builtins
    def register_record_input(payload):
        if game_state.get("record_mode"):
            recorded_inputs.append({
                "tick": game_state.get("tick", 0),
                "payload": copy.deepcopy(payload)
            })
    def register_record_output(data):
        if game_state.get("record_mode"):
            recorded_outputs.append(data)
            
    builtins.register_record_input = register_record_input
    builtins.register_record_output = register_record_output

    def handle_record_test():
        if not game_state.get("record_mode"):
            # Start Recording
            from tkinter import simpledialog
            test_name = simpledialog.askstring("Record Test", "Enter Test Name (e.g. basic_sort):", parent=root)
            if not test_name: return
            
            game_state["active_test_name"] = test_name
            game_state["record_mode"] = True
            game_state["tick"] = 0
            recorded_inputs.clear()
            recorded_outputs.clear()
            
            handle_play()
            print(f"TEST RECORDER: Recording started for '{test_name}'")
        else:
            # Stop Recording
            game_state["record_mode"] = False
            test_name = game_state.get("active_test_name")
            test_dir = os.path.join("tests", test_name)
            os.makedirs(test_dir, exist_ok=True)
            
            # 1. Save YAML Layout
            yaml_path = os.path.join(test_dir, f"{test_name}.yaml")
            metadata = {
                "name": test_name,
                "description": f"Automated test recorded via UI",
                "gravity": game_state.get("gravity", [0, 900]),
                "damping": game_state.get("damping", 0.99)
            }
            level_manager.save_level(entities, filepath=yaml_path, metadata=metadata)
            
            # 2. Save Inputs JSON
            with open(os.path.join(test_dir, "inputs.json"), "w") as f:
                json.dump(recorded_inputs, f, indent=4)
                
            # 3. Save Expected Output CSV
            exp_path = os.path.join(test_dir, "expected_output.csv")
            if recorded_outputs:
                import csv
                keys = sorted(recorded_outputs[0].keys())
                with open(exp_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(recorded_outputs)
            
            print(f"TEST RECORDER: Saved test suite to {test_dir}")
            handle_edit()

    def handle_open_debug(entity):
        if not entity:
            return
        
        # Gather detailed state
        lines = []
        lines.append(f"<b><u>Entity: {entity.variant_key}</u></b>")
        lines.append(f"<b>UUID:</b> {getattr(entity, 'uuid', 'N/A')}")
        lines.append(f"<b>Visual State:</b> {getattr(entity, 'visual_state', 'N/A')}")
        lines.append(f"<b>Internal Logic Paused:</b> {getattr(entity, 'is_paused', False)}")
        
        # Timers & Counters
        for attr in ["shoot_timer", "shoot_count", "cooldown_timer", "flash_timer", "floating_timer"]:
            if hasattr(entity, attr):
                lines.append(f"<b>{attr}:</b> {getattr(entity, attr)}")
        
        # Physics
        if hasattr(entity, "body") and entity.body:
            pos = entity.body.position
            vel = entity.body.velocity
            lines.append(f"<b>Position:</b> ({pos.x:.2f}, {pos.y:.2f})")
            lines.append(f"<b>Velocity:</b> ({vel.x:.2f}, {vel.y:.2f})")
            lines.append(f"<b>Angle:</b> {math.degrees(entity.body.angle):.2f}°")
        
        # Payload
        if hasattr(entity, "payload") and entity.payload:
            lines.append("<br><b>--- Payload Data ---</b>")
            try:
                # Pretty print with indentation
                p_text = json.dumps(entity.payload, indent=2)
                # HTML escape/formatting
                p_text = p_text.replace("\n", "<br>").replace(" ", "&nbsp;")
                lines.append(f"<font face='mono'>{p_text}</font>")
            except:
                lines.append(str(entity.payload))
        
        message = "<br>".join(lines)
        
        UIMessageWindow(
            rect=pygame.Rect(window_width // 2 - 250, window_height // 2 - 200, 500, 400),
            html_message=message,
            manager=editor_ui.ui_manager,
            window_title=f"Debug: {entity.variant_key}"
        )

    callbacks = {
        "play": lambda: handle_play(),
        "pause": lambda: handle_pause(),
        "edit": lambda: handle_edit(),
        "new": lambda: handle_new_flow(),
        "snap": lambda: toggle_snap_to_grid(),
        "trace": lambda: toggle_traces(),
        "q_save": lambda: handle_quick_save(),
        "q_load": lambda: handle_quick_load(),
        "save": lambda: handle_save(),
        "load": lambda: handle_load(),
        "quit": lambda: handle_quit(),
        "flow_settings": handle_flow_settings,
        "save_flow": handle_save_flow,
        "open_debug": handle_open_debug,

        "record_test": lambda: handle_record_test(),
        "camera": lambda: camera,
        "dirty_callback": lambda: game_state.update({"is_dirty": True, "last_change_time": time.time()})
    }
    
    editor_ui = EditorUI(
        window_width, window_height, 
        {
            "ui_top_height": UI_TOP_HEIGHT,
            "ui_bottom_height": UI_BOTTOM_HEIGHT,
            "ui_left_panel_width": UI_SIDE_WIDTH,
            "ui_right_panel_width": UI_RIGHT_SIDE_WIDTH
        },
        all_variants, categories, game_state, callbacks
    )
    
    # Milestone 42: Define gamepad callbacks (M42 Redux)
    def next_palette_cb():
        editor_ui.palette_page = (editor_ui.palette_page + 1) % ((len(editor_ui.palette_items) + editor_ui.items_per_page - 1) // editor_ui.items_per_page)
        editor_ui.rebuild_palette()
    def prev_palette_cb():
        editor_ui.palette_page = (editor_ui.palette_page - 1) % ((len(editor_ui.palette_items) + editor_ui.items_per_page - 1) // editor_ui.items_per_page)
        editor_ui.rebuild_palette()
    ctrl_callbacks = {"next_palette": next_palette_cb, "prev_palette": prev_palette_cb}
    playable_rect = editor_ui.playable_rect
    # Milestone 42 Follow-up: Update camera to only care about the playable area viewport
    camera.screen_width = playable_rect.width
    camera.screen_height = playable_rect.height
    camera.display_offset_x = playable_rect.x
    camera.display_offset_y = playable_rect.y
    
    def apply_level_data(level_data, constraints_data=None, connections_data=None, metadata=None):
        if not level_data:
            return
            
        if metadata:
            game_state["gravity"] = metadata.get("gravity", [0, 900])
            game_state["damping"] = metadata.get("damping", 0.99)
            game_state["wind"] = metadata.get("wind", [0, 0])
            space.gravity = tuple(game_state["gravity"])
            space.damping = game_state["damping"]
            
        for entity in list(entities):
            if hasattr(entity, 'cleanup'):
                entity.cleanup()
            if getattr(entity, 'body', None):
                for constraint in list(entity.body.constraints):
                    if constraint in space.constraints:
                        space.remove(constraint)
            for shape in getattr(entity, 'shapes', [getattr(entity, 'shape', None)]):
                if shape and shape in space.shapes:
                    space.remove(shape)
            if hasattr(entity, 'body') and entity.body:
                if entity.body != space.static_body and entity.body in space.bodies:
                    space.remove(entity.body)
        entities.clear()
        active_instances.clear()
        
        for data in level_data:
            variant_key = data.get("entity_id") or data.get("variant_key")
            pos = data.get("position", {"x": 0, "y": 0})
            rot = data.get("rotation", 0)
            
            new_part = create_part(space, pos["x"], pos["y"], variant_key)
            if "uuid" in data:
                new_part.uuid = data["uuid"]
            if "properties" in data:
                new_part.apply_draft_overrides(data["properties"])
            if "overrides" in data:
                new_part.apply_draft_overrides(data["overrides"])
            if hasattr(new_part, 'body') and new_part.body:
                new_part.body.angle = rot
                space.reindex_shapes_for_body(new_part.body)
            entities.append(new_part)
            active_instances[new_part.uuid] = new_part
            
        if constraints_data:
            for c_data in constraints_data:
                c_type = c_data.get("type")
                uid_a = c_data.get("target_uuid_a")
                uid_b = c_data.get("target_uuid_b")
                
                if uid_a in active_instances and uid_b in active_instances:
                    body_a = active_instances[uid_a].body
                    body_b = active_instances[uid_b].body
                    anch_a = c_data.get("anchor_a", [0, 0])
                    anch_b = c_data.get("anchor_b", [0, 0])
                    
                    if c_type == "PivotJoint":
                        joint = pymunk.PivotJoint(body_a, body_b, tuple(anch_a), tuple(anch_b))
                        space.add(joint)
                    elif c_type == "PinJoint":
                        joint = pymunk.PinJoint(body_a, body_b, tuple(anch_a), tuple(anch_b))
                        space.add(joint)
                    elif c_type == "SlideJoint":
                        min_d = c_data.get("min_dist", 0)
                        max_d = c_data.get("max_dist", 100)
                        joint = pymunk.SlideJoint(body_a, body_b, tuple(anch_a), tuple(anch_b), min_d, max_d)
                        space.add(joint)
                        
        if connections_data:
            for conn in connections_data:
                sender_uid = conn.get("sender")
                receiver_uid = conn.get("receiver")
                if sender_uid in active_instances and receiver_uid in active_instances:
                    active_instances[sender_uid].connected_uuids.append(receiver_uid)
        
        # --- Belt Restoration Pass ---
        for entity in entities:
            # Axles and Gears store their belt targets in overrides
            belt_targets = entity.overrides.get("connected_belts", [])
            for target_uuid in belt_targets:
                if target_uuid in active_instances:
                    target_entity = active_instances[target_uuid]
                    if hasattr(entity, 'connect_belt'):
                        # Re-create the physics joint (connect_belt handles the space.add)
                        entity.connect_belt(target_entity)
            
    def handle_quick_save():
        editor_ui.sync_ui_to_state()
        metadata = {
            "name": game_state.get("name", ""),
            "description": game_state.get("description", ""),
            "gravity": game_state.get("gravity", [0, 900]),
            "damping": game_state.get("damping", 0.99),
            "wind": game_state.get("wind", [0, 0])
        }
        current_name = game_state.get("name", "Untitled")
        level_manager.save_level(entities, flow_name=current_name, metadata=metadata)
        env_manager.active_project = current_name.replace(" ", "_")
        game_state["is_dirty"] = False
        
    def handle_quick_load():
        handle_clear()
        level_data, constraints_data, connections_data, metadata = level_manager.load_level()
        apply_level_data(level_data, constraints_data, connections_data, metadata=metadata)
        game_state["name"] = metadata.get("name", metadata.get("flow_name", "Untitled"))
        game_state["description"] = metadata.get("description", metadata.get("flow_description", ""))
        env_manager.active_project = game_state["name"].replace(" ", "_")
        game_state["mode"] = "EDIT"
        editor_ui.rebuild_top_panel()

    def handle_save():
        filepath = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
            initialdir=os.path.abspath("saves"),
            title="Save Level As...",
            parent=root
        )
        if filepath:
            editor_ui.sync_ui_to_state()
            metadata = {
                "name": game_state.get("name", ""),
                "description": game_state.get("description", ""),
                "gravity": game_state.get("gravity", [0, 900]),
                "damping": game_state.get("damping", 0.99),
                "wind": game_state.get("wind", [0, 0])
            }
            level_manager.save_level(entities, filepath=filepath, metadata=metadata)
            env_manager.active_project = game_state.get("name", "").replace(" ", "_")
            
    def handle_load():
        filepath = filedialog.askopenfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
            initialdir=os.path.abspath("saves"),
            title="Load Level",
            parent=root
        )
        if filepath:
            handle_clear()
            level_data, constraints_data, connections_data, metadata = level_manager.load_level(filepath)
            apply_level_data(level_data, constraints_data, connections_data, metadata=metadata)
            game_state["name"] = metadata.get("name", metadata.get("flow_name", "Untitled"))
            game_state["description"] = metadata.get("description", metadata.get("flow_description", ""))
            env_manager.active_project = game_state["name"].replace(" ", "_")
            game_state["mode"] = "EDIT"
            editor_ui.rebuild_top_panel()

    def handle_new_flow():
        """Refines the NEW workflow: prompt first, clear later."""
        game_state["is_creating_new"] = True
        game_state["selected_instance"] = "GLOBAL_FLOW"
        # Reset physics to defaults for a new flow
        game_state["gravity"] = [0, 900]
        game_state["damping"] = 0.99
        game_state["wind"] = [0, 0]
        editor_ui.rebuild_left_inspector()

    def handle_clear():
        for entity in list(entities):
            if hasattr(entity, 'cleanup'):
                entity.cleanup()
            if getattr(entity, 'body', None):
                for constraint in list(entity.body.constraints):
                    if constraint in space.constraints:
                        space.remove(constraint)
            for shape in getattr(entity, 'shapes', [getattr(entity, 'shape', None)]):
                if shape and shape in space.shapes:
                    space.remove(shape)
            if hasattr(entity, 'body') and entity.body:
                if entity.body != space.static_body and entity.body in space.bodies:
                    space.remove(entity.body)
        entities.clear()
        active_instances.clear()
        signal_queue.clear()
        active_signals.clear()
        game_state["selected_instance"] = None
        game_state["wiring_source"] = None
        
        if "TEST_OUTPUT_DIR" in os.environ:
            del os.environ["TEST_OUTPUT_DIR"]
        game_state["belt_source"] = None
        game_state["pipe_source"] = None
        game_state["is_dirty"] = False
        game_state["last_change_time"] = time.time() # Update last_change_time on clear
        print("LevelManager: Canvas cleared.")

    def handle_play():
        game_state["mode"] = "PLAY"
        for entity in entities:
            if hasattr(entity, 'reset_logic'):
                entity.reset_logic()
        
        # Milestone 35: Clear recording buffer
        import builtins
        if hasattr(builtins, "captured_test_outputs"):
            builtins.captured_test_outputs = []
            
        editor_ui.rebuild_top_panel()

    def handle_record():
        """Milestone 35: Toggle Recording Mode"""
        game_state["record_mode"] = not game_state.get("record_mode", False)
        if game_state["record_mode"]:
            print("Recorder: Enabled. Start simulation to capture output.")
        else:
            print("Recorder: Disabled.")
        editor_ui.rebuild_top_panel()

    def handle_pause():
        if game_state["mode"] == "PLAY":
            game_state["mode"] = "PAUSE"
        elif game_state["mode"] == "PAUSE":
            game_state["mode"] = "PLAY"
        editor_ui.rebuild_top_panel()

    def handle_stop():
        """Milestone 35: Stop and potentially save recorded test."""
        if game_state.get("record_mode") and game_state["mode"] in ("PLAY", "PAUSE"):
            import builtins
            captured = getattr(builtins, "captured_test_outputs", [])
            if captured:
                from tkinter import simpledialog
                import tkinter as tk
                import json # Added import for json
                test_name = simpledialog.askstring("Save Test", "Enter name for this test case:", parent=root)
                
                if test_name:
                    test_dir = os.path.join("tests", test_name.replace(" ", "_"))
                    os.makedirs(test_dir, exist_ok=True)
                    
                    # 1. Save YAML
                    yaml_path = os.path.join(test_dir, f"{os.path.basename(test_dir)}.yaml")
                    metadata = {
                        "name": game_state.get("name", "Recorded Test"),
                        "description": game_state.get("description", "Auto-recorded"),
                        "gravity": game_state.get("gravity", [0, 900]),
                        "damping": game_state.get("damping", 0.99),
                        "wind": game_state.get("wind", [0, 0])
                    }
                    level_manager.save_level(entities, filepath=yaml_path, metadata=metadata)
                    
                    # 2. Save Expected Output (CSV)
                    csv_path = os.path.join(test_dir, "expected_output.csv")
                    with open(csv_path, "w", newline="") as f:
                        if captured:
                            import csv
                            header = sorted(captured[0].keys())
                            writer = csv.DictWriter(f, fieldnames=header)
                            writer.writeheader()
                            for row in captured:
                                writer.writerow(row)
                    
                    # 3. Create rich inputs.json
                    input_path = os.path.join(test_dir, "inputs.json")
                    if not os.path.exists(input_path):
                        meta = {
                            "test_name": test_name,
                            "test_description": "Automatically recorded test case.",
                            "evaluator": "strict_csv",
                            "payload_events": captured_test_inputs
                        }
                        with open(input_path, "w") as f:
                            json.dump(meta, f, indent=2)
                    
                    print(f"Recorder: Test '{test_name}' saved to {test_dir}")
                    game_state["record_mode"] = False
        
        handle_edit()

    def handle_edit():
        import gc
        game_state["mode"] = "EDIT"
        
        # Milestone 34: Mode Transition Garbage Collection
        # Clear all existing PayloadBallPart entities immediately
        to_remove = [e for e in entities if isinstance(e, PayloadBallPart)]
        for e in to_remove:
            e.to_delete = True # Flag for logic consistency
            if hasattr(e, 'cleanup'):
                e.cleanup()
            if getattr(e, 'body', None):
                for constraint in list(e.body.constraints):
                    if constraint in space.constraints:
                        space.remove(constraint)
            for shape in getattr(e, 'shapes', [getattr(e, 'shape', None)]):
                if shape and shape in space.shapes:
                    space.remove(shape)
            if hasattr(e, 'body') and e.body:
                if e.body != space.static_body and e.body in space.bodies:
                    space.remove(e.body)
            if e in entities:
                entities.remove(e)
            if hasattr(e, 'uuid') and e.uuid in active_instances:
                del active_instances[e.uuid]
        
        # New M35/M32 Reset Hook: Clear queues and threads for Logic & I/O
        for entity in entities:
            if hasattr(entity, 'reset_flow_logic'):
                entity.reset_flow_logic()

        gc.collect() # Force immediate reclamation
        editor_ui.rebuild_top_panel()
    def handle_status_panels():
        # Placeholders for any status bar updates if needed
        pass

    # Initial UI Build
    editor_ui.rebuild_top_panel()
    editor_ui.rebuild_category_tabs()
    editor_ui.rebuild_right_palette()
    editor_ui.rebuild_left_inspector()
    
    def handle_quit():
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def toggle_snap_to_grid():
        game_state["snap_to_grid"] = not game_state.get("snap_to_grid", False)
        editor_ui.rebuild_top_panel()

    def toggle_traces():
        game_state["show_traces"] = not game_state.get("show_traces", False)
        editor_ui.rebuild_top_panel()

    def run_single_test(test_dir, visible=False):
        """Milestone 35: Standardized Test Orchestrator"""
        test_name = os.path.basename(test_dir)
        yaml_path = os.path.join(test_dir, f"{test_name}.yaml")
        if not os.path.exists(yaml_path):
            # Fallback to first .yaml found
            yaml_files = [f for f in os.listdir(test_dir) if f.endswith(".yaml")]
            if not yaml_files: 
                print(f"  [Error] No .yaml found in {test_dir}")
                return False
            yaml_path = os.path.join(test_dir, yaml_files[0])
                  # 1. Standard Setup
        print(f"\n--- STARTING TEST SUITE ('{test_name}') ---")
        handle_clear() # Mandatory: shutdown previous threads before touching files
        
        # 2. Clear previous outputs
        cwd = os.getcwd()
        output_dir = os.path.join(cwd, test_dir, "output")
        output_dir = os.path.abspath(output_dir)
        
        # Milestone 35 Fix: Stable directory cleanup for Windows
        if os.path.exists(output_dir):
            import shutil, time as _time
            for _retry in range(5):
                try: 
                    shutil.rmtree(output_dir)
                    break
                except: 
                    _time.sleep(0.1) # Help Windows release folder locks
        os.makedirs(output_dir, exist_ok=True)

        os.environ["TEST_OUTPUT_DIR"] = output_dir
        
        # 3. Load Level
        # No handle_clear() here - it would wipe TEST_OUTPUT_DIR
        level_data, constraints_data, connections_data, metadata = level_manager.load_level(yaml_path)
        apply_level_data(level_data, constraints_data, connections_data, metadata)
        
        game_state["mode"] = "PLAY"
        game_state["tick"] = 0
        game_state["test_mode"] = True
        game_state["active_test_name"] = test_name
        
        # Notify TestSources to load their inputs
        for entity in entities:
            if isinstance(entity, TestSourcePart):
                entity.load_inputs(test_dir)
        
        max_ticks = 1200 # 20 seconds
        dt = 1.0 / 60.0
        
        print(f"  > Executing {test_name} for {max_ticks} ticks...")
        simulation_trace = []
        
        for tick in range(max_ticks):
            game_state["tick"] = tick
            if tick % 100 == 0:
                print(f"  [Tick {tick}]")
                import sys
                sys.stdout.flush()
            
            # 1. Update logic
            for entity in list(entities):
                if hasattr(entity, 'update_logic'):
                    entity.update_logic(dt, game_state, entities, active_instances)
            
            # 2. Update physics
            space.step(dt)
            
            # 3. Clean up deleted entities
            to_remove = [e for e in entities if getattr(e, 'to_delete', False)]
            for e in to_remove:
                if hasattr(e, 'cleanup'): e.cleanup()
                if e in entities: entities.remove(e)
                if hasattr(e, 'uuid') and e.uuid in active_instances:
                    del active_instances[e.uuid]
            
            # Milestone 35: Black Box Snapshots (Always capture for potential failure)
            snapshot = []
            for e in entities:
                # Milestone 38: Skip diagnostic entities without physics bodies (like labels)
                if not getattr(e, "body", None):
                    continue
                    
                snapshot.append({
                    "uuid": str(getattr(e, "uuid", "unknown")),
                    "pos": [float(e.body.position.x), float(e.body.position.y)],
                    "angle": float(e.body.angle),
                    "state": str(getattr(e, "visual_state", "IDLE")),
                    "variant": str(getattr(e, "variant_key", "unknown")),
                    "is_hidden": bool(getattr(e, "is_hidden", False)),
                    "flash_timer": float(getattr(e, "flash_timer", 0.0)),
                    "stored_payload_uuids": list(getattr(e, "stored_payload_uuids", []))
                })
            simulation_trace.append(snapshot)

            # 4. Optional Rendering (Visible mode)
            if visible:
                # Basic event pump to keep OS happy
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: return False
                
                screen.fill((30, 30, 30))
                # Viewport culling draw (simplified for test)
                for entity in entities:
                    if not getattr(entity, 'is_hidden', False):
                        if hasattr(entity, 'update_visual'):
                            entity.update_visual(screen, camera=camera)
                pygame.display.flip()
                # clock.tick(60) # Don't cap speed unless user wants to watch at real-time
                
        # Milestone 35: Finalize & Flush (mandatory for async Sinks)
        print(f"  > Finalizing entities and flushing sinks...")
        for entity in list(entities):
            if hasattr(entity, 'cleanup'):
                entity.cleanup()
        
        # Give async Sinks a moment to finish disk writes
        print(f"  > Waiting for async workers to settle...")
        time.sleep(2.0)

        # Assertion Logic
        success = perform_test_assertion(test_dir)
        
        # Milestone 35: Black Box Failure Dump
        if not success:
            trace_path = os.path.join(test_dir, "failure_trace.json")
            try:
                import json
                with open(trace_path, "w") as f:
                    json.dump(simulation_trace, f)
                print(f"  [Black Box] Failure trace dumped to {trace_path}")
            except Exception as e:
                print(f"  [Error] Failed to dump failure trace: {e}")

        return success

    def perform_test_assertion(test_dir):
        """Milestone 35: Auto-Assertion via CSV comparison."""
        test_name = os.path.basename(test_dir)
        expected_path = os.path.join(test_dir, "expected_output.csv")
        
        # Milestone 35 Fix: Robust path derivation from test_dir
        cwd = os.getcwd()
        output_dir = os.path.join(cwd, test_dir, "output")
        output_dir = os.path.abspath(output_dir)
        print(f"  DEBUG: perform_test_assertion using path: {output_dir}")
        
        # Milestone 35 Fix: Filesystem stabilization
        import time as _time
        all_files = []
        for attempt in range(10):
            if os.path.exists(output_dir):
                all_files = os.listdir(output_dir)
                if any(f.startswith("result") and f.endswith(".csv") for f in all_files):
                    break
            _time.sleep(0.5)
            
        print(f"  DEBUG: perform_test_assertion looking in {output_dir}")
        print(f"  DEBUG: Final Files found: {all_files}")
        output_files = [f for f in all_files if f.startswith("result") and f.endswith(".csv")]
        if not output_files:
            print(f"  [FAIL] {test_name}: No output CSV generated in {output_dir}. Found: {all_files}")
            return False
            
        latest_file = sorted(output_files)[-1]
        actual_path = os.path.join(output_dir, latest_file)
        print(f"  DEBUG: Comparing against {actual_path}")
        
        # Milestone 35 Refinement: Root metadata discovery for Evaluator selection
        evaluator_type = "strict_csv"
        input_path = os.path.join(test_dir, "inputs.json")
        if os.path.exists(input_path):
            try:
                with open(input_path, "r") as f:
                    meta = json.load(f)
                    if isinstance(meta, dict):
                        evaluator_type = meta.get("evaluator", "strict_csv")
            except: pass

        if evaluator_type == "llm_semantic":
            from utils.evaluators import evaluate_llm_semantic
            return evaluate_llm_semantic(actual_path, expected_path)

        # Milestone 35 Fix: High-frequency polling to overcome async disk writing delays
        import time as _time
        exp_lines = []
        act_lines = []
        
        for attempt in range(10):
            try:
                with open(expected_path, "r") as f_exp, open(actual_path, "r") as f_act:
                    exp_lines = [l.strip() for l in f_exp.readlines() if l.strip()]
                    act_lines = [l.strip() for l in f_act.readlines() if l.strip()]
                
                if len(act_lines) >= (len(exp_lines) if exp_lines else 1):
                    break # Found what we need
            except Exception:
                pass
            _time.sleep(0.5)
                
        print(f"  DEBUG: Row count - Expected (inc header): {len(exp_lines)}, Actual: {len(act_lines)}")
        try:
            if len(exp_lines) != len(act_lines):
                print(f"  [FAIL] {test_name}: Row count mismatch (Exp: {len(exp_lines)}, Act: {len(act_lines)})")
                print(f"  DEBUG: Actual lines: {act_lines}")
                return False
                
            for i, (exp, act) in enumerate(zip(exp_lines, act_lines)):
                if exp.strip() != act.strip():
                    print(f"  [FAIL] {test_name}: Mismatch at row {i+1}")
                    print(f"    Expected: {exp.strip()}")
                    print(f"    Actual:   {act.strip()}")
                    return False
            
            print(f"  [PASS] {test_name}")
            return True
        except Exception as e:
            print(f"  [ERROR] {test_name}: Assertion failed with error: {e}")
            return False

    
    space = pymunk.Space()
    space.gravity = constants.GRAVITY
    create_boundaries(space, world_width, world_height, playable_rect)

    entities = []
    active_instances = {}
    signal_queue = []
    active_signals = [] 
    
    collision_manager = CollisionManager(entities, active_instances, signal_queue)
    collision_manager.setup(space)
    
    # --- Handle CLI Load Argument ---
    if args.load:
        load_path = os.path.abspath(args.load)
        if os.path.exists(load_path):
            level_data, constraints_data, connections_data, metadata = level_manager.load_level(load_path)
            apply_level_data(level_data, constraints_data, connections_data)
            game_state["flow_name"] = metadata.get("flow_name", "Untitled")
            game_state["flow_description"] = metadata.get("flow_description", "")
            env_manager.active_project = game_state["flow_name"].replace(" ", "_")
            editor_ui.rebuild_top_panel()
            print(f"CLI: Successfully loaded level from {load_path}")
        else:
            print(f"CLI Warning: Load file not found at {load_path}")

    # --- Milestone 35: CLI Test Runner Hook ---
    if args.test:
        test_paths = resolve_test_paths(args.test)
        if not test_paths:
            print(f"ERROR: No tests found matching '{args.test}'")
            pygame.quit()
            sys.exit(1)
            
        print(f"\n--- STARTING TEST SUITE ('{args.test}') ---")
        test_results = []
        for tp in test_paths:
            res = run_single_test(tp, args.visible)
            test_results.append((tp, res))
            
        # Final Aggregate Reporting
        total = len(test_results)
        passed = sum(1 for _, s in test_results if s)
        print(f"\n--- TEST SUITE COMPLETE ---")
        print(f"TOTAL: {total} | PASS: {passed} | FAIL: {total - passed}")
        
    # --- Milestone 35: Failure Replay Mode ---
    if args.replay:
        run_replay_mode(args.replay)
        pygame.quit()
        sys.exit(0)
        
        pygame.quit()
        sys.exit(0 if passed == total else 1)

    grabbed_body = None
    prev_mode = game_state["mode"]
    game_state["wiring_source"] = None
    game_state["belt_source"] = None 
    game_state["pipe_source"] = None
    
    trash_can_visible = False
    trash_can_rect = pygame.Rect(w // 2 - 40, h - 100, 80, 80)
    cursor_over_trash = False
    
    def handle_tool_click(world_click_pos):
        """Helper to manage interaction with the tools based on world position."""
        nonlocal grabbed_body, trash_can_visible
        
        info = space.point_query_nearest(world_click_pos, 5.0, pymunk.ShapeFilter())
        target_entity = None
        
        if info and info.shape and info.shape.body != space.static_body:
            for entity in entities:
                if info.shape in getattr(entity, 'shapes', [entity.shape]):
                    target_entity = entity
                    break
                    
        active_tool = game_state["active_tool"]
        
        if target_entity:
            if active_tool == "wire_tool":
                # Phase 12: Separation of Logic Wires and Data Tubes
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    # SHIFT + Click: Clear ALL outgoing logic connections
                    if hasattr(target_entity, 'connected_uuids'):
                        target_entity.connected_uuids.clear()
                    
                    sound_manager.play_sound("snap.wav")
                    target_entity.flash_timer = 30
                    game_state["wiring_source"] = None
                    game_state["is_dirty"] = True
                    game_state["last_change_time"] = time.time()
                elif game_state["wiring_source"] is None:
                    game_state["wiring_source"] = target_entity
                elif game_state["wiring_source"] != target_entity:
                    src = game_state["wiring_source"]
                    connected = getattr(src, 'connected_uuids', [])
                    if target_entity.uuid in connected:
                        # Toggle OFF
                        connected.remove(target_entity.uuid)
                        sound_manager.play_sound("snap.wav")
                        target_entity.flash_timer = 20
                    else:
                        # Standard Connection (Logic Wire - Signals Only)
                        if target_entity.uuid not in connected:
                            connected.append(target_entity.uuid)
                        target_entity.play_event_sound("spawn_sound")
                    
                    game_state["wiring_source"] = None
                    game_state["is_dirty"] = True
                    game_state["last_change_time"] = time.time()
                    editor_ui.rebuild_left_inspector() 
                else:
                    game_state["wiring_source"] = None

            elif active_tool == "pipe_tool":
                if game_state["pipe_source"] is None:
                    game_state["pipe_source"] = target_entity
                    target_entity.play_event_sound("spawn_sound")
                elif game_state["pipe_source"] != target_entity:
                    src = game_state["pipe_source"]
                    tgt = target_entity
                    
                    mid_x = (src.body.position.x + tgt.body.position.x) / 2
                    mid_y = (src.body.position.y + tgt.body.position.y) / 2
                    
                    new_pipe = create_part(space, mid_x, mid_y, "data_pipe")
                    # Milestone 36 Fix: Save to overrides for persistence
                    new_pipe.overrides["source_uuid"] = src.uuid
                    new_pipe.overrides["target_uuid"] = tgt.uuid
                    
                    # Phase 12 Integration: creating a Data Tube automatically creates a Logic Wire.
                    if not hasattr(src, 'connected_uuids'):
                        src.connected_uuids = []
                    if tgt.uuid not in src.connected_uuids:
                        src.connected_uuids.append(tgt.uuid)
                    
                    entities.append(new_pipe)
                    active_instances[new_pipe.uuid] = new_pipe
                    target_entity.play_event_sound("spawn_sound")
                    game_state["pipe_source"] = None
                    game_state["is_dirty"] = True
                    game_state["last_change_time"] = time.time()
                    editor_ui.rebuild_left_inspector()
                else:
                    game_state["pipe_source"] = None

            elif active_tool == "belt_tool":
                target_axle = None
                if hasattr(target_entity, 'connect_belt'):
                    target_axle = target_entity
                
                if target_axle:
                    if game_state.get("belt_source") is None:
                        # First click: set the source
                        game_state["belt_source"] = target_axle
                        target_axle.play_event_sound("spawn_sound")
                    elif game_state["belt_source"] != target_axle:
                        # Second click: different axle, create the belt
                        game_state["belt_source"].connect_belt(target_axle)
                        target_axle.play_event_sound("spawn_sound")
                        game_state["belt_source"] = None
                        game_state["is_dirty"] = True
                        game_state["last_change_time"] = time.time()
                    else:
                        # Second click: same axle, cancel
                        game_state["belt_source"] = None
                else:
                    # Clicked something that isn't an axle
                    game_state["belt_source"] = None

            else:
                # Select existing component for moving or inspection
                mode = game_state.get("mode", "EDIT")
                if mode == "EDIT":
                    grabbed_body = info.shape.body
                    trash_can_visible = True
                
                game_state["selected_instance"] = target_entity
                editor_ui.rebuild_left_inspector()
                
        elif active_tool is not None and active_tool not in ("wire_tool", "belt_tool", "pipe_tool"):
            if game_state.get("mode") == "PAUSE":
                return # No spawning in pause mode
            
            # Spawn a new part into the world
            spawn_x, spawn_y = world_click_pos
            if game_state.get("snap_to_grid", False):
                spawn_x, spawn_y = snap_to_grid(spawn_x, spawn_y)
            
            new_part = create_part(space, spawn_x, spawn_y, active_tool)
            entities.append(new_part)
            active_instances[new_part.uuid] = new_part
            new_part.play_event_sound("spawn_sound")
            game_state["is_dirty"] = True
            game_state["last_change_time"] = time.time() # Update last_change_time
            
        else:
            # Clicked empty space with no spawn tool -> clear selection
            game_state["wiring_source"] = None
            game_state["belt_source"] = None
            game_state["pipe_source"] = None
            if game_state.get("selected_instance") is not None:
                game_state["selected_instance"] = None
                editor_ui.rebuild_left_inspector()

    start_ticks = pygame.time.get_ticks()
    running = True
    

    while running:
        dt = clock.tick(60) / 1000.0
        # Check CLI Timeout
        if args.timeout:
            elapsed_minutes = (pygame.time.get_ticks() - start_ticks) / 60000.0
            if elapsed_minutes >= args.timeout:
                print(f"CLI: Timeout of {args.timeout} minutes reached. Triggering quit sequence.")
                running = False

        current_mode = game_state["mode"]
        
        if current_mode != prev_mode:
            if current_mode == "PLAY":
                grabbed_body = None
                space.reindex_static()
                active_signals.clear()
            prev_mode = current_mode

        for entity in entities:
            entity.is_hovered = False
            
        m_pos = pygame.mouse.get_pos()
        world_m_pos = camera.screen_to_world(m_pos[0], m_pos[1])

        # Milestone 42: Continuous Gamepad Polling
        controller_manager.update(dt)
        pan_vx, pan_vy = controller_manager.get_camera_pan()
        if pan_vx != 0 or pan_vy != 0:
            camera.x += pan_vx
            camera.y += pan_vy

        
        if current_mode == "EDIT" and not grabbed_body:
            if playable_rect.collidepoint(m_pos):
                info = space.point_query_nearest(world_m_pos, 5.0, pymunk.ShapeFilter())
                if info and info.shape and info.shape.body != space.static_body:
                    for entity in entities:
                        if info.shape in getattr(entity, 'shapes', [entity.shape]):
                            entity.is_hovered = True
                            break

        for event in pygame.event.get():
            # Milestone 42 Resizing Fix: Intelligent Capping
            if event.type == pygame.VIDEORESIZE:
                # User clarification: Cap size at (world_width or 5000) + panels
                limit_w = min(5000, world_width)
                limit_h = min(5000, world_height)
                
                panels_w = editor_ui.side_w + editor_ui.right_w
                panels_h = editor_ui.top_h + editor_ui.bot_h
                
                target_w = min(event.w, limit_w + panels_w)
                target_h = min(event.h, limit_h + panels_h)
                
                # Re-apply mode to resize/cap the window if needed
                if (target_w, target_h) != (window_width, window_height):
                    screen = pygame.display.set_mode((target_w, target_h), pygame.RESIZABLE)
                    window_width, window_height = target_w, target_h
                    editor_ui.update_resolution(window_width, window_height)
                    camera.screen_width = editor_ui.playable_rect.width
                    camera.screen_height = editor_ui.playable_rect.height
                    playable_rect = editor_ui.playable_rect
                continue

            if event.type == pygame.QUIT:
                running = False
                
            if editor_ui.process_event(event):
                continue
                
            if controller_manager.process_event(event, ctrl_callbacks):
                continue
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and current_mode == "EDIT":
                    entity_to_delete = game_state.get("selected_instance")
                    if entity_to_delete:
                        # Milestone 34: Connection Sweeping
                        deleted_uuid = getattr(entity_to_delete, 'uuid', None)
                        sweep_orphaned_connections(deleted_uuid, entities)

                        if hasattr(entity_to_delete, 'cleanup'):
                            entity_to_delete.cleanup()
                        
                        if hasattr(entity_to_delete, 'uuid') and entity_to_delete.uuid in active_instances:
                            del active_instances[entity_to_delete.uuid]
                        
                        if entity_to_delete in entities:
                            entities.remove(entity_to_delete)
                        
                        if hasattr(entity_to_delete, 'body') and entity_to_delete.body:
                            # Rule: Constraints MUST be removed BEFORE bodies
                            for constraint in list(entity_to_delete.body.constraints):
                                if constraint in space.constraints:
                                    space.remove(constraint)
                                    
                        for shape in getattr(entity_to_delete, 'shapes', [getattr(entity_to_delete, 'shape', None)]):
                            if shape and shape in space.shapes:
                                space.remove(shape)
                                
                        if hasattr(entity_to_delete, 'body') and entity_to_delete.body:
                            if entity_to_delete.body != space.static_body and entity_to_delete.body in space.bodies:
                                space.remove(entity_to_delete.body)
                                    
                        if grabbed_body and hasattr(entity_to_delete, 'body') and grabbed_body == entity_to_delete.body:
                            grabbed_body = None
                            trash_can_visible = False
                            
                        game_state["selected_instance"] = None
                        game_state["is_dirty"] = True
                        game_state["last_change_time"] = time.time() # Update last_change_time
                        editor_ui.rebuild_left_inspector()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                camera.begin_pan(event.pos[0], event.pos[1])
                continue
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                camera.end_pan()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    world_click_pos = camera.screen_to_world(event.pos[0], event.pos[1])
                    if playable_rect.collidepoint(event.pos) and current_mode in ("EDIT", "PAUSE"):
                        handle_tool_click(world_click_pos)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"CRASH IN CLICK LOOP: {e}")
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                world_click_pos = camera.screen_to_world(event.pos[0], event.pos[1])
                
                if playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
                    info = space.point_query_nearest(world_click_pos, 5.0, pymunk.ShapeFilter())
                    if info and info.shape and info.shape.body != space.static_body:
                        for entity in list(entities):
                            if info.shape in getattr(entity, 'shapes', [getattr(entity, 'shape', None)]):
                                # Milestone 34: Connection Sweeping
                                deleted_uuid = getattr(entity, 'uuid', None)
                                sweep_orphaned_connections(deleted_uuid, entities)

                                if hasattr(entity, 'cleanup'):
                                    entity.cleanup()
                                if getattr(entity, 'body', None):
                                    # Rule: Constraints MUST be removed BEFORE bodies
                                    for constraint in list(entity.body.constraints):
                                        if constraint in space.constraints:
                                            space.remove(constraint)
                                        
                                for shape in getattr(entity, 'shapes', [getattr(entity, 'shape', None)]):
                                    if shape and shape in space.shapes:
                                        space.remove(shape)
                                        
                                if hasattr(entity, 'body') and entity.body:
                                    if entity.body != space.static_body and entity.body in space.bodies:
                                        space.remove(entity.body)
                                        
                                entities.remove(entity)
                                if entity.uuid in active_instances:
                                    del active_instances[entity.uuid]
                                game_state["is_dirty"] = True
                                game_state["last_change_time"] = time.time() # Update last_change_time
                                break
            
            elif event.type == pygame.MOUSEMOTION:
                if camera.is_panning:
                    camera.update_pan(event.pos[0], event.pos[1])
                
                if trash_can_visible:
                    cursor_over_trash = trash_can_rect.collidepoint(event.pos[0], event.pos[1])
                
                if current_mode == "EDIT" and grabbed_body:
                    world_drag_pos = camera.screen_to_world(event.pos[0], event.pos[1])
                    
                    if game_state.get("snap_to_grid", False):
                        world_drag_pos = snap_to_grid(world_drag_pos[0], world_drag_pos[1])
                    
                    grabbed_body.position = world_drag_pos
                    if grabbed_body.body_type == pymunk.Body.DYNAMIC:
                        grabbed_body.velocity = (0, 0)
                        grabbed_body.angular_velocity = 0
                    space.reindex_shapes_for_body(grabbed_body)
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if grabbed_body and cursor_over_trash and current_mode == "EDIT":
                    entity_to_delete = None
                    for entity in entities:
                        if hasattr(entity, 'body') and entity.body == grabbed_body:
                            entity_to_delete = entity
                            break
                    
                    if entity_to_delete:
                        if hasattr(entity_to_delete, 'cleanup'):
                            entity_to_delete.cleanup()
                        
                        if hasattr(entity_to_delete, 'uuid') and entity_to_delete.uuid in active_instances:
                            del active_instances[entity_to_delete.uuid]
                        
                        if entity_to_delete in entities:
                            entities.remove(entity_to_delete)
                        
                        if hasattr(entity_to_delete, 'body') and entity_to_delete.body:
                            for constraint in list(entity_to_delete.body.constraints):
                                if constraint in space.constraints:
                                    space.remove(constraint)
                                    
                        for shape in getattr(entity_to_delete, 'shapes', [getattr(entity_to_delete, 'shape', None)]):
                            if shape and shape in space.shapes:
                                space.remove(shape)
                                
                        if hasattr(entity_to_delete, 'body') and entity_to_delete.body:
                            if entity_to_delete.body != space.static_body and entity_to_delete.body in space.bodies:
                                space.remove(entity_to_delete.body)
                
                if grabbed_body:
                    game_state["is_dirty"] = True
                    game_state["last_change_time"] = time.time()
                grabbed_body = None
                trash_can_visible = False
                
            elif event.type == pygame.MOUSEWHEEL:
                if current_mode == "EDIT":
                    target = grabbed_body
                    if not target:
                        mouse_pos = pygame.mouse.get_pos()
                        world_mouse_pos = camera.screen_to_world(mouse_pos[0], mouse_pos[1])
                        info = space.point_query_nearest(world_mouse_pos, 5.0, pymunk.ShapeFilter())
                        if info and info.shape and info.shape.body != space.static_body:
                            target = info.shape.body
                    if target:
                        target.angle += event.y * 0.1
                        game_state["is_dirty"] = True
                        game_state["last_change_time"] = time.time()
                        space.reindex_shapes_for_body(target)

        if editor_ui.ui_manager.get_focus_set() is None:
            keys = pygame.key.get_pressed()
            rotated = False
            if keys[pygame.K_q]:
                grabbed_body.angle -= 0.05
                rotated = True
            if keys[pygame.K_e]:
                grabbed_body.angle += 0.05
                rotated = True
            if rotated:
                space.reindex_shapes_for_body(grabbed_body)
        
        if editor_ui.ui_manager.get_focus_set() is None:
            keys = pygame.key.get_pressed()
            dt_sim = clock.get_time() / 1000.0  
            camera.handle_keyboard_pan(keys, constants.CAMERA_PAN_SPEED, dt_sim)

        dt = clock.tick(60) / 1000.0
        controller_manager.update(dt)
        visual_fx_manager.update(dt)
        editor_ui.update(dt)
        editor_ui.sync_scrollbars_to_camera(camera)
        editor_ui.set_debug_info(world_m_pos[0], world_m_pos[1], window_width, window_height)

        # Milestone 35 Fix: Debounced Autosave (2.0s delay after last change)
        if game_state.get("is_dirty") and game_state["mode"] == "EDIT":
            if time.time() - game_state.get("last_change_time", 0) > 2.0:
                handle_quick_save()
                game_state["is_dirty"] = False

        if current_mode == "PLAY":
            # Apply wind force
            wind = game_state.get("wind", [0, 0])
            if wind[0] != 0 or wind[1] != 0:
                for body in space.bodies:
                    if body.body_type == pymunk.Body.DYNAMIC:
                        body.apply_force_at_world_point(tuple(wind), body.position)

            space.step(constants.PHYSICS_STEP * game_state.get("speed_multiplier", 1.0))
            
            while signal_queue:
                sender = signal_queue.pop(0)
                sender.flash_timer = 15 
                if hasattr(sender, 'connected_uuids'):
                    for tgt_uuid in sender.connected_uuids:
                        tgt = active_instances.get(tgt_uuid)
                        if tgt:
                            if not getattr(sender, 'variant_key', '').startswith('portal'):
                                active_signals.append({
                                    "sender_uuid": sender.uuid,
                                    "target_uuid": tgt_uuid,
                                    "progress": 0.0
                                })
                            if hasattr(tgt, 'receive_signal'):
                                tgt.receive_signal(payload=sender)
            
            alive_signals = []
            for sig in active_signals:
                sig["progress"] += constants.PHYSICS_STEP * 3.0 
                if sig["progress"] < 1.0:
                    alive_signals.append(sig)
            active_signals = alive_signals
            
            for entity in entities:
                entity.is_hidden = False
            
            for entity in list(entities):
                if getattr(entity, 'flash_timer', 0) > 0:
                    entity.flash_timer -= 1

                if getattr(entity, 'current_payload_uuid', None):
                    payload = active_instances.get(entity.current_payload_uuid)
                    if payload and hasattr(payload, 'body') and payload.body:
                        payload.body.position = entity.body.position
                        payload.body.velocity = (0, 0)
                        payload.body.angular_velocity = 0
                        payload.is_hidden = True
                        
                if hasattr(entity, 'stored_payload_uuids'):
                    for puuid in entity.stored_payload_uuids:
                        payload = active_instances.get(puuid)
                        if payload and hasattr(payload, 'body') and payload.body:
                            payload.body.position = entity.body.position
                            payload.body.velocity = (0, 0)
                            payload.body.angular_velocity = 0
                            payload.is_hidden = True

                if getattr(entity, 'floating', False):
                    mass = float(getattr(entity.body, 'mass', 0.0))
                    if mass > 0.0:
                        entity.body.apply_force_at_world_point(
                            (0.0, -mass * constants.FLOATING_UPWARD_ACCELERATION),
                            entity.body.position,
                        )
                    entity.floating_timer = max(0.0, float(getattr(entity, 'floating_timer', 0.0)) - constants.PHYSICS_STEP)
                    if entity.floating_timer <= 0.0:
                        entity.to_delete = True

                if hasattr(entity, 'poll_results'):
                    entity.poll_results(entities, active_instances)

                # Milestone 34: Kill Z Volume
                if hasattr(entity, 'body') and entity.body and entity.body.position.y > 5000:
                    entity.to_delete = True

            # Milestone 34: Safe Deletion Batching (Phase 9)
            to_delete_batch = [e for e in entities if getattr(e, 'to_delete', False)]
            
            for entity in to_delete_batch:
                # 1. Connection Sweeping (GC)
                deleted_uuid = getattr(entity, 'uuid', None)
                sweep_orphaned_connections(deleted_uuid, entities)

                # 2. Component Cleanup
                if hasattr(entity, 'cleanup'):
                    entity.cleanup()
                
                # 3. Explicit Memory Clearing
                if hasattr(entity, 'payload') and isinstance(entity.payload, dict):
                    entity.payload.clear()
                if hasattr(entity, 'trace_history') and isinstance(entity.trace_history, list):
                    entity.trace_history.clear()

                # 4. Object Pooling vs Physics Removal
                is_recycled = False
                if isinstance(entity, PayloadBallPart):
                    entity.is_hidden = True
                    entity.to_delete = False # Reset for pooling safety
                    if entity.body:
                        entity.body.velocity = (0, 0)
                        entity.body.angular_velocity = 0
                        entity.body.position = (-5000, -5000)
                        
                        if entity.body in space.bodies:
                            space.remove(entity.body)
                        for s in entity.shapes:
                            if s in space.shapes:
                                space.remove(s)
                    payload_pool.append(entity)
                    is_recycled = True
                
                if not is_recycled:
                    if getattr(entity, 'body', None):
                        # Rule: Constraints MUST be removed BEFORE bodies
                        for constraint in list(entity.body.constraints):
                            if constraint in space.constraints:
                                space.remove(constraint)
                                
                    for shape in getattr(entity, 'shapes', [getattr(entity, 'shape', None)]):
                        if shape and shape in space.shapes:
                            space.remove(shape)
                            
                    if hasattr(entity, 'body') and entity.body:
                        if entity.body != space.static_body and entity.body in space.bodies:
                            space.remove(entity.body)
                
                # 5. Final Lookup Removal
                if deleted_uuid and deleted_uuid in active_instances:
                    # Double check if it's the right entity
                    if active_instances[deleted_uuid] == entity:
                        del active_instances[deleted_uuid]

            # 6. Final Batch Removal from main entity list
            if to_delete_batch:
                entities[:] = [e for e in entities if not getattr(e, 'to_delete', False)]

            # 7. Update logic for remaining entities
            for entity in entities:
                if hasattr(entity, 'update_logic'):
                    entity.update_logic(constants.PHYSICS_STEP, game_state, entities, active_instances)
                    
        env_manager.draw_background(screen)
        
        if current_mode == "EDIT" and game_state.get("show_grid", True):
            grid_origin_x = -(camera.offset_x % constants.GRID_SIZE)
            grid_origin_y = -(camera.offset_y % constants.GRID_SIZE)
            
            grid_surface = pygame.Surface((window_width, window_height))
            grid_surface.set_alpha(constants.GRID_ALPHA)
            grid_surface.fill((0, 0, 0))  
            grid_surface.set_colorkey((0, 0, 0))  
            
            x = grid_origin_x
            while x < window_width:
                pygame.draw.line(grid_surface, constants.GRID_COLOR, (int(x), 0), (int(x), window_height), 1)
                x += constants.GRID_SIZE
            
            y = grid_origin_y
            while y < window_height:
                pygame.draw.line(grid_surface, constants.GRID_COLOR, (0, int(y)), (window_width, int(y)), 1)
                y += constants.GRID_SIZE
            
            screen.blit(grid_surface, (0, 0))

        # Milestone 42 Follow-up: DRAW VISIBLE WORLD BORDER
        # This draws a persistent neon border at the actual physics limits.
        border_top_left = camera.world_to_screen(0, 0)
        world_border_rect = pygame.Rect(
            int(border_top_left[0]), 
            int(border_top_left[1]), 
            world_width, world_height
        )
        pygame.draw.rect(screen, (0, 255, 255), world_border_rect, 3) # Neon Cyan

        world_screen_left = int(border_top_left[0])
        world_screen_top = int(border_top_left[1])
        world_screen_right = world_screen_left + world_width
        world_screen_bottom = world_screen_top + world_height
        void_color = (224, 224, 224)

        if world_screen_left > playable_rect.left:
            pygame.draw.rect(screen, void_color, pygame.Rect(playable_rect.left, playable_rect.top, world_screen_left - playable_rect.left, playable_rect.height))
        if world_screen_top > playable_rect.top:
            pygame.draw.rect(screen, void_color, pygame.Rect(playable_rect.left, playable_rect.top, playable_rect.width, world_screen_top - playable_rect.top))
        if world_screen_right < playable_rect.right:
            pygame.draw.rect(screen, void_color, pygame.Rect(world_screen_right, playable_rect.top, playable_rect.right - world_screen_right, playable_rect.height))
        if world_screen_bottom < playable_rect.bottom:
            pygame.draw.rect(screen, void_color, pygame.Rect(playable_rect.left, world_screen_bottom, playable_rect.width, playable_rect.bottom - world_screen_bottom))
        
        # Phase 14: Global Visual FX Budget (Stigmergy Traces & Particles)
        visual_fx_manager.draw(screen, camera=camera)
        
        # Milestone 44: Wiring 2.0 (Visible Splines & Data Pulses)
        # Display connections if globally toggled OR if the wire tool is active
        show_wiring = editor_ui.show_connections_globally or (game_state.get("active_tool") == "wire_tool")
        visual_fx_manager.draw_connections(screen, camera, entities, active_instances, active_signals, show_all=show_wiring)

        for entity in entities:
            if hasattr(entity, 'body') and entity.body:
                world_x, world_y = entity.body.position.x, entity.body.position.y
            elif hasattr(entity, 'x') and hasattr(entity, 'y'):
                world_x, world_y = entity.x, entity.y
            else:
                continue
                
            screen_x, screen_y = camera.world_to_screen(world_x, world_y)
            
            if (-100 < screen_x < constants.WINDOW_WIDTH + 100 and 
                -100 < screen_y < constants.WINDOW_HEIGHT + 100):
                
                if not getattr(entity, 'is_hidden', False):
                    if hasattr(entity, 'connected_belts'):
                        entity.update_visual(screen, camera=camera, active_instances=active_instances)
                    else:
                        entity.update_visual(screen, camera=camera)
                    
                    if current_mode == "EDIT" and getattr(entity, 'overrides', {}):
                        sx, sy = int(screen_x), int(screen_y)
                        pygame.draw.circle(screen, (255, 0, 255), (sx, sy), 5)
                        pygame.draw.circle(screen, (0, 0, 0), (sx, sy), 5, 1)

                if hasattr(entity, 'payload') and entity.payload:
                    if game_state.get("show_traces", False) and "trace" in entity.payload:
                        trace_list = entity.payload.get("trace", [])
                        if trace_list:
                            payload_str = " -> ".join(trace_list[-3:]) 
                        else:
                            payload_str = "Trace: Started"
                    else:
                        payload_str = str(entity.payload)
                        if len(payload_str) > 20:
                            payload_str = payload_str[:17] + "..."
                    
                    p_text = small_font.render(payload_str, True, (0, 255, 255))
                    p_rect = p_text.get_rect(center=(int(screen_x), int(screen_y) - 25))
                    
                    bg_surf = pygame.Surface((p_rect.width + 8, p_rect.height + 4), pygame.SRCALPHA)
                    bg_surf.fill((0, 0, 0, 180))
                    screen.blit(bg_surf, (p_rect.x - 4, p_rect.y - 2))
                    screen.blit(p_text, p_rect)
            
        # Redundant wire drawing loop removed in Phase 11. 
        # visual_fx_manager.draw_connections handles this now.

        # Redundant signal drawing loop removed in Phase 11.
        # visual_fx_manager.draw_connections handles signal pulses now.

        if current_mode == "EDIT" and game_state["active_tool"] == "wire_tool" and game_state.get("wiring_source"):
            src = game_state["wiring_source"]
            if src.body:
                world_start_x, world_start_y = src.body.position.x, src.body.position.y
                screen_start = camera.world_to_screen(world_start_x, world_start_y)
                start_x, start_y = int(screen_start[0]), int(screen_start[1])
                
                points = [get_wire_curve_point((start_x, start_y), m_pos, i / 25.0) for i in range(26)]
                int_points = [(int(p.x), int(p.y)) for p in points]
                pygame.draw.aalines(screen, (255, 150, 0), False, int_points)

        if current_mode == "EDIT" and game_state["active_tool"] == "pipe_tool" and game_state.get("pipe_source"):
            src = game_state["pipe_source"]
            if src.body:
                world_start_x, world_start_y = src.body.position.x, src.body.position.y
                screen_start = camera.world_to_screen(world_start_x, world_start_y)
                start_x, start_y = int(screen_start[0]), int(screen_start[1])
                
                points = [get_pipe_curve_point((start_x, start_y), m_pos, i / 20.0) for i in range(21)]
                int_points = [(int(p.x), int(p.y)) for p in points]
                
                preview_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                pygame.draw.lines(preview_surf, (100, 200, 255, 80), False, int_points, 18)
                pygame.draw.lines(preview_surf, (150, 230, 255, 200), False, int_points, 6)
                screen.blit(preview_surf, (0, 0))

        if current_mode == "EDIT" and game_state.get("active_tool") == "belt_tool" and game_state.get("belt_source"):
            src = game_state["belt_source"]
            if src.body:
                world_start_x, world_start_y = src.body.position.x, src.body.position.y
                screen_start = camera.world_to_screen(world_start_x, world_start_y)
                start_x, start_y = int(screen_start[0]), int(screen_start[1])
                pygame.draw.line(screen, (100, 100, 255), (start_x, start_y), m_pos, 3)

        if current_mode == "EDIT" and not grabbed_body and game_state["active_tool"] is not None:
            active_tool_key = game_state["active_tool"]
            preview_surf = create_icon_surface(active_tool_key, all_variants[active_tool_key])
            preview_surf.set_alpha(128) 
            preview_rect = preview_surf.get_rect(center=m_pos)
            screen.blit(preview_surf, preview_rect)

        border_color = env_manager.edit_mode_color if current_mode == "EDIT" else env_manager.play_mode_color
        pygame.draw.rect(screen, border_color, playable_rect, 5)

        editor_ui.draw(screen)
        
        if trash_can_visible and current_mode == "EDIT":
            trash_icon_font = pygame.font.SysFont(None, 48)
            trash_text = trash_icon_font.render("🗑", True, (255, 255, 255))
            trash_text_rect = trash_text.get_rect(center=trash_can_rect.center)
            screen.blit(trash_text, trash_text_rect)

        pygame.display.flip()

    # --- Handle CLI Auto-Dump Argument ---
    if args.dump:
        dump_path = os.path.abspath(args.dump)
        metadata = {
            "name": game_state.get("name", "CLI_Dump"),
            "description": game_state.get("description", "Automated CLI Dump"),
            "gravity": game_state.get("gravity", [0, 900]),
            "damping": game_state.get("damping", 0.99),
            "wind": game_state.get("wind", [0, 0])
        }
        level_manager.save_level(entities, filepath=dump_path, metadata=metadata)
        print(f"CLI: Automatically dumped world configuration to {dump_path}")

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()