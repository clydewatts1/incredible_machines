import pygame
import pymunk
import sys
import os
import math
import tkinter as tk
from tkinter import filedialog

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
from entities.axle import AxlePart
from entities.brain import BrainPart
from entities.warehouse import WarehousePart
from entities.portal import PortalPart
from entities.payloadball import PayloadBallPart
from entities.textbox import TextBoxPart

# Import the new Data Pipe!
from entities.data_pipe import DataPipePart, get_pipe_curve_point

from utils.sound_manager import sound_manager
from utils.environment_manager import env_manager
from utils.config_loader import load_all_variants
from utils.level_manager import LevelManager
from utils.camera import Camera
from utils.physics_events import CollisionManager
from utils.editor_ui import EditorUI, create_icon_surface


def create_boundaries(space, playable_rect):
    static_body = space.static_body
    thickness = 50.0  # Thick walls prevent high-speed balls from tunneling through

    left = playable_rect.left
    right = playable_rect.right
    top = playable_rect.top
    bottom = playable_rect.bottom
    
    # Offset the segments by 'thickness' so their inner edges align perfectly with the green box
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

def dummy_action(feature_name):
    def callback():
        print(f"Not Implemented: {feature_name}")
    return callback

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
        return PayloadBallPart(space, x, y, variant_key)
    elif variant_key in ("data_source", "data_source_csv", "data_source_mcp"):
        return DataSource(space, x, y, variant_key)
    elif variant_key.startswith("data_sink"):
        return DataSink(space, x, y, variant_key)
    elif variant_key in ("gear_driver", "gear_follower"):
        return MechanicalPart(space, x, y, variant_key) 
    elif variant_key == "axle":
        return AxlePart(space, x, y, variant_key)
    elif variant_key == "data_pipe":
        return DataPipePart(space, x, y, variant_key)
    elif variant_key == "text_box":
        return TextBoxPart(space, x, y, variant_key)
        
    return GamePart(space, x, y, variant_key)

def get_wire_curve_point(start_pos, end_pos, t):
    """Calculates a point along an elegant S-Curve Bezier for logic wires, with a gentle wind sway."""
    p0 = pygame.math.Vector2(start_pos)
    p3 = pygame.math.Vector2(end_pos)
    
    dx = p3.x - p0.x
    dy = p3.y - p0.y
    dist = p0.distance_to(p3)
    
    time_sec = pygame.time.get_ticks() / 1000.0
    phase = (p0.x + p0.y) * 0.01 
    max_sway = min(25.0, dist * 0.15)
    
    sway1 = math.sin(time_sec * 2.0 + phase) * max_sway
    sway2 = math.sin(time_sec * 2.5 + phase + 1.0) * max_sway
    
    if abs(dx) > abs(dy):
        p1 = p0 + pygame.math.Vector2(dx * 0.5, sway1)
        p2 = p0 + pygame.math.Vector2(dx * 0.5, dy + sway2)
    else:
        p1 = p0 + pygame.math.Vector2(sway1, dy * 0.5)
        p2 = p0 + pygame.math.Vector2(dx + sway2, dy * 0.5)
        
    u = 1 - t
    return (u**3)*p0 + 3*(u**2)*t*p1 + 3*u*(t**2)*p2 + (t**3)*p3


def snap_to_grid(world_x, world_y):
    snapped_x = round(world_x / constants.GRID_SIZE) * constants.GRID_SIZE
    snapped_y = round(world_y / constants.GRID_SIZE) * constants.GRID_SIZE
    return (snapped_x, snapped_y)


def main():
    pygame.init()
    sound_manager.initialize()
    env_manager.initialize(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)

    window_width = env_manager.get_int("window_width", constants.WINDOW_WIDTH)
    window_height = env_manager.get_int("window_height", constants.WINDOW_HEIGHT)
    world_width = env_manager.get_int("world_width", constants.WORLD_WIDTH)
    world_height = env_manager.get_int("world_height", constants.WORLD_HEIGHT)
    
    w, h = window_width, window_height

    all_variants = load_all_variants()
    
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
    
    screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE | pygame.SCALED)
    pygame.display.set_caption("The Incredible Machine Clone - Milestone 27")
    clock = pygame.time.Clock()
    
    game_state = {
        "mode": "EDIT",
        "active_tool": None,
        "snap_to_grid": False,
        "show_grid": True,
        "show_traces": False,
        "selected_instance": None,
        "selected_category": "all",
        "wiring_source": None,
        "belt_source": None,
        "pipe_source": None,
    }

    level_manager = LevelManager()
    editor_ui = None  # Forward declaration for callbacks
    
    def apply_level_data(level_data, constraints_data=None, connections_data=None):
        if not level_data:
            return
            
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
            variant_key = data.get("entity_id")
            pos = data.get("position", {"x": 0, "y": 0})
            rot = data.get("rotation", 0)
            
            new_part = create_part(space, pos["x"], pos["y"], variant_key)
            if "uuid" in data:
                new_part.uuid = data["uuid"]
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
            
    def handle_quick_save():
        level_manager.save_level(entities)
        
    def handle_quick_load():
        handle_clear()
        level_data, constraints_data, connections_data = level_manager.load_level()
        apply_level_data(level_data, constraints_data, connections_data)
        game_state["mode"] = "EDIT"
        editor_ui.rebuild_top_panel()

    def handle_save():
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
            initialdir=os.path.abspath("saves"),
            title="Save Level As..."
        )
        root.destroy()
        if filepath:
            level_manager.save_level(entities, filepath=filepath)
            
    def handle_load():
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
            initialdir=os.path.abspath("saves"),
            title="Load Level"
        )
        root.destroy()
        if filepath:
            handle_clear()
            level_data, constraints_data, connections_data = level_manager.load_level(filepath)
            apply_level_data(level_data, constraints_data, connections_data)
            game_state["mode"] = "EDIT"
            editor_ui.rebuild_top_panel()

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

    def handle_play():
        game_state["mode"] = "PLAY"
        for entity in entities:
            if hasattr(entity, 'reset_logic'):
                entity.reset_logic()
        editor_ui.rebuild_top_panel()

    def handle_pause():
        if game_state["mode"] == "PLAY":
            game_state["mode"] = "PAUSE"
        elif game_state["mode"] == "PAUSE":
            game_state["mode"] = "PLAY"
        editor_ui.rebuild_top_panel()

    def handle_edit():
        game_state["mode"] = "EDIT"
        editor_ui.rebuild_top_panel()
        
    def handle_quit():
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def toggle_snap_to_grid():
        game_state["snap_to_grid"] = not game_state.get("snap_to_grid", False)
        editor_ui.rebuild_top_panel()

    def toggle_traces():
        game_state["show_traces"] = not game_state.get("show_traces", False)
        editor_ui.rebuild_top_panel()

    callbacks = {
        "play": handle_play,
        "pause": handle_pause,
        "edit": handle_edit,
        "clear": handle_clear,
        "snap": toggle_snap_to_grid,
        "trace": toggle_traces,
        "q_save": handle_quick_save,
        "q_load": handle_quick_load,
        "save": handle_save,
        "load": handle_load,
        "quit": handle_quit,
        "challenges": dummy_action("Challenges"),
        "help": dummy_action("Help"),
        "options": dummy_action("Options")
    }

    env_settings = {
        "ui_top_height": env_manager.get_int("ui_top_height", 50),
        "ui_bottom_height": env_manager.get_int("ui_bottom_height", 40),
        "ui_left_panel_width": env_manager.get_int("ui_left_panel_width", 260),
        "ui_right_panel_width": env_manager.get_int("ui_right_panel_width", 320)
    }

    editor_ui = EditorUI(
        window_width, window_height, env_settings, 
        all_variants, categories, game_state, callbacks
    )
    editor_ui.rebuild_top_panel()
    editor_ui.rebuild_category_tabs()
    editor_ui.rebuild_right_palette()
    editor_ui.rebuild_left_inspector()
    
    space = pymunk.Space()
    space.gravity = constants.GRAVITY
    create_boundaries(space, editor_ui.playable_rect)
    
    camera = Camera(
        world_width=world_width,
        world_height=world_height,
        screen_width=window_width,
        screen_height=window_height
    )

    entities = []
    active_instances = {}
    signal_queue = []
    active_signals = [] 
    
    collision_manager = CollisionManager(entities, active_instances, signal_queue)
    collision_manager.setup(space)
    
    grabbed_body = None
    prev_mode = game_state["mode"]
    
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
                if game_state["wiring_source"] is None:
                    game_state["wiring_source"] = target_entity
                elif game_state["wiring_source"] != target_entity:
                    game_state["wiring_source"].connected_uuids.append(target_entity.uuid)
                    target_entity.play_event_sound("spawn_sound")
                    game_state["wiring_source"] = None
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
                    new_pipe.properties["source_uuid"] = src.uuid
                    new_pipe.properties["target_uuid"] = tgt.uuid
                    
                    entities.append(new_pipe)
                    active_instances[new_pipe.uuid] = new_pipe
                    target_entity.play_event_sound("spawn_sound")
                    game_state["pipe_source"] = None
                else:
                    game_state["pipe_source"] = None

            elif active_tool == "belt_tool":
                target_axle = None
                if hasattr(target_entity, 'connect_belt'):
                    target_axle = target_entity
                
                if target_axle:
                    if game_state.get("belt_source") is None:
                        game_state["belt_source"] = target_axle
                        target_axle.play_event_sound("spawn_sound")
                    elif game_state["belt_source"] != target_axle:
                        game_state["belt_source"].connect_belt(target_axle)
                        target_axle.play_event_sound("spawn_sound")
                        game_state["belt_source"] = None
                    else:
                        game_state["belt_source"] = None
                else:
                    game_state["belt_source"] = None

            else:
                # Select existing component for moving or inspection
                grabbed_body = info.shape.body
                trash_can_visible = True
                game_state["selected_instance"] = target_entity
                editor_ui.rebuild_left_inspector()
                
        elif active_tool is not None and active_tool not in ("wire_tool", "belt_tool", "pipe_tool"):
            # Spawn a new part into the world
            spawn_x, spawn_y = world_click_pos
            if game_state.get("snap_to_grid", False):
                spawn_x, spawn_y = snap_to_grid(spawn_x, spawn_y)
            
            new_part = create_part(space, spawn_x, spawn_y, active_tool)
            entities.append(new_part)
            active_instances[new_part.uuid] = new_part
            new_part.play_event_sound("spawn_sound")
            
        else:
            # Clicked empty space with no spawn tool -> clear selection
            game_state["wiring_source"] = None
            game_state["belt_source"] = None
            game_state["pipe_source"] = None
            if game_state.get("selected_instance") is not None:
                game_state["selected_instance"] = None
                editor_ui.rebuild_left_inspector()

    running = True
    while running:
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
        
        if current_mode == "EDIT" and not grabbed_body:
            if editor_ui.playable_rect.collidepoint(m_pos):
                info = space.point_query_nearest(world_m_pos, 5.0, pymunk.ShapeFilter())
                if info and info.shape and info.shape.body != space.static_body:
                    for entity in entities:
                        if info.shape in getattr(entity, 'shapes', [entity.shape]):
                            entity.is_hovered = True
                            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if editor_ui.process_event(event):
                continue
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and current_mode == "EDIT":
                    entity_to_delete = game_state.get("selected_instance")
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
                                    
                        if grabbed_body and hasattr(entity_to_delete, 'body') and grabbed_body == entity_to_delete.body:
                            grabbed_body = None
                            trash_can_visible = False
                            
                        game_state["selected_instance"] = None
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
                    if editor_ui.playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
                        handle_tool_click(world_click_pos)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"CRASH IN CLICK LOOP: {e}")
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                world_click_pos = camera.screen_to_world(event.pos[0], event.pos[1])
                
                if editor_ui.playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
                    info = space.point_query_nearest(world_click_pos, 5.0, pymunk.ShapeFilter())
                    if info and info.shape and info.shape.body != space.static_body:
                        for entity in list(entities):
                            if info.shape in getattr(entity, 'shapes', [entity.shape]):
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
                                        
                                entities.remove(entity)
                                if entity.uuid in active_instances:
                                    del active_instances[entity.uuid]
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
                        space.reindex_shapes_for_body(target)

        if current_mode == "EDIT" and grabbed_body and not editor_ui.focused_element:
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
        
        if not editor_ui.focused_element:
            keys = pygame.key.get_pressed()
            dt = clock.get_time() / 1000.0  
            camera.handle_keyboard_pan(keys, constants.CAMERA_PAN_SPEED, dt)

        if current_mode == "PLAY":
            space.step(constants.PHYSICS_STEP)
            
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

                if getattr(entity, 'to_delete', False):
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
                    if entity in entities:
                        entities.remove(entity)
                    if entity.uuid in active_instances:
                        del active_instances[entity.uuid]
                    continue
                
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

        world_screen_left = int(-camera.offset_x)
        world_screen_top = int(-camera.offset_y)
        world_screen_right = int(world_width - camera.offset_x)
        world_screen_bottom = int(world_height - camera.offset_y)
        void_color = (85, 85, 85)

        if world_screen_left > 0:
            pygame.draw.rect(screen, void_color, pygame.Rect(0, 0, world_screen_left, window_height))
        if world_screen_top > 0:
            pygame.draw.rect(screen, void_color, pygame.Rect(0, 0, window_width, world_screen_top))
        if world_screen_right < window_width:
            pygame.draw.rect(screen, void_color, pygame.Rect(world_screen_right, 0, window_width - world_screen_right, window_height))
        if world_screen_bottom < window_height:
            pygame.draw.rect(screen, void_color, pygame.Rect(0, world_screen_bottom, window_width, window_height - world_screen_bottom))
        
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
            
            if current_mode in ["EDIT", "PLAY", "PAUSE"] or game_state["active_tool"] == "wire_tool":
                if hasattr(entity, 'connected_uuids') and getattr(entity, 'body', None):
                    world_start_x, world_start_y = entity.body.position.x, entity.body.position.y
                    screen_start = camera.world_to_screen(world_start_x, world_start_y)
                    start_pos = (int(screen_start[0]), int(screen_start[1]))
                    
                    for tgt_uuid in entity.connected_uuids:
                        tgt = active_instances.get(tgt_uuid)
                        if tgt and getattr(tgt, 'body', None):
                            world_end_x, world_end_y = tgt.body.position.x, tgt.body.position.y
                            screen_end = camera.world_to_screen(world_end_x, world_end_y)
                            end_pos = (int(screen_end[0]), int(screen_end[1]))
                            
                            flash = getattr(entity, 'flash_timer', 0)
                            
                            if getattr(entity, 'variant_key', '').startswith('portal'):
                                wire_color = (200, 50, 255) if flash > 0 else (100, 20, 150)
                                width = 4 if flash > 0 else 2
                            else:
                                wire_color = (0, 255, 255) if flash > 0 else (255, 255, 0)
                                if current_mode in ["PLAY", "PAUSE"] and flash <= 0:
                                    wire_color = (255, 200, 0)
                                width = 3 if flash > 0 else 1

                            points = [get_wire_curve_point(start_pos, end_pos, i / 25.0) for i in range(26)]
                            int_points = [(int(p.x), int(p.y)) for p in points]

                            if width == 1:
                                pygame.draw.aalines(screen, wire_color, False, int_points)
                            else:
                                pygame.draw.lines(screen, wire_color, False, int_points, width)
                                
                            start_v = pygame.math.Vector2(start_pos)
                            end_v = pygame.math.Vector2(end_pos)
                            if start_v.distance_to(end_v) > 20:
                                direction = points[-1] - points[-2]
                                if direction.length() > 0:
                                    direction = direction.normalize()
                                    arrow_base = points[-1] - direction * 15
                                    left_wing = arrow_base + pygame.math.Vector2(-direction.y, direction.x) * 5
                                    right_wing = arrow_base + pygame.math.Vector2(direction.y, -direction.x) * 5
                                    pygame.draw.polygon(
                                        screen, 
                                        wire_color, 
                                        [(int(points[-1].x), int(points[-1].y)), 
                                         (int(left_wing.x), int(left_wing.y)), 
                                         (int(right_wing.x), int(right_wing.y))]
                                    )

        for sig in active_signals:
            sender = active_instances.get(sig["sender_uuid"])
            tgt = active_instances.get(sig["target_uuid"])
            if sender and tgt and getattr(sender, 'body', None) and getattr(tgt, 'body', None):
                sx, sy = camera.world_to_screen(sender.body.position.x, sender.body.position.y)
                ex, ey = camera.world_to_screen(tgt.body.position.x, tgt.body.position.y)
                
                pt = get_wire_curve_point((sx, sy), (ex, ey), sig["progress"])
                px, py = pt.x, pt.y
                
                pygame.draw.circle(screen, (0, 200, 255), (int(px), int(py)), 8) 
                pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), 4) 

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
        pygame.draw.rect(screen, border_color, editor_ui.playable_rect, 5)

        editor_ui.draw(screen)
        
        if trash_can_visible and current_mode == "EDIT":
            trash_bg_color = (150, 50, 50) if cursor_over_trash else (80, 80, 80)
            pygame.draw.rect(screen, trash_bg_color, trash_can_rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), trash_can_rect, 3, border_radius=10)
            
            trash_icon_font = pygame.font.SysFont(None, 48)
            trash_text = trash_icon_font.render("🗑", True, (255, 255, 255))
            trash_text_rect = trash_text.get_rect(center=trash_can_rect.center)
            screen.blit(trash_text, trash_text_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()