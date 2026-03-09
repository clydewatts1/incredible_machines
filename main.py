import pygame
import pymunk
import sys
import os
import tkinter as tk
from tkinter import filedialog

import constants
from entities.base import GamePart
from utils.sound_manager import sound_manager
from utils.environment_manager import env_manager
from utils.config_loader import load_all_variants
from utils.ui_manager import UIManager, UIPanel, UIButton, UILabel
from utils.level_manager import LevelManager

UI_TOP_HEIGHT = 50
UI_BOTTOM_HEIGHT = 40
UI_SIDE_WIDTH = 80
UI_RIGHT_SIDE_WIDTH = 120

def create_boundaries(space):
    """Create screen boundaries so things don't fall off screen."""
    static_body = space.static_body
    w, h = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
    thickness = 500.0
    
    # Phase 2: Physics Boundaries align with playable_rect
    # Offset the segments outward by the thickness so the *inner edge* of the segment
    # rests exactly on the UI boundary lines.
    left = UI_SIDE_WIDTH - thickness
    right = w - UI_RIGHT_SIDE_WIDTH + thickness
    top = UI_TOP_HEIGHT - thickness
    bottom = h - UI_BOTTOM_HEIGHT + thickness
    
    segments = [
        pymunk.Segment(static_body, (left, bottom), (right, bottom), thickness), # Bottom
        pymunk.Segment(static_body, (left, top), (left, bottom), thickness), # Left
        pymunk.Segment(static_body, (right, top), (right, bottom), thickness), # Right
        pymunk.Segment(static_body, (left, top), (right, top), thickness)  # Top
    ]
    
    for s in segments:
        s.elasticity = 0.8
        s.friction = 0.5
        space.add(s)

def dummy_action(feature_name):
    def callback():
        print(f"Not Implemented: {feature_name}")
    return callback

def set_mode(new_mode, state_dict):
    def callback():
        state_dict["mode"] = new_mode
    return callback

def set_active_tool(tool_key, state_dict):
    def callback():
        state_dict["active_tool"] = tool_key
    return callback

def create_icon_surface(variant_key, variant_data):
    """Phase 4: Loads an icon surface from the asset manager instead of procedural drawing."""
    from utils.asset_manager import asset_manager
    # Use variant_key or label for the fallback text
    label = variant_data.get("label", variant_key)
    icon_path = f"assets/icons/{variant_key}_button.png"
    
    # We use 40x40 since that matches the current UI sizes
    return asset_manager.get_image(icon_path, fallback_size=(40, 40), text_label=label)

def main():
    pygame.init()
    sound_manager.initialize()
    env_manager.initialize(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)
    
    all_variants = load_all_variants()
    
    # Phase 1: M17 Wire Tool Hack - Inject a fake variant so it gets a button
    if "wire_tool" not in all_variants:
        all_variants["wire_tool"] = {
            "label": "Wire Logic",
            "template": "Rectangle",
            "color": [255, 255, 0]
        }
    
    screen = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    pygame.display.set_caption("The Incredible Machine Clone - Milestone 9")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 16) # For Palette labels

    # Instantiate UIManager
    ui_manager = UIManager()
    
    w, h = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
    
    # Calculate playable space
    playable_rect = pygame.Rect(
        UI_SIDE_WIDTH, 
        UI_TOP_HEIGHT, 
        w - UI_SIDE_WIDTH - UI_RIGHT_SIDE_WIDTH, 
        h - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT
    )
    
    # Phase 3 & 4: Construct static UI Panels
    top_panel = UIPanel(pygame.Rect(0, 0, w, UI_TOP_HEIGHT), color=(50, 50, 50))
    bottom_panel = UIPanel(pygame.Rect(0, h - UI_BOTTOM_HEIGHT, w, UI_BOTTOM_HEIGHT), color=(50, 50, 50))
    left_panel = UIPanel(pygame.Rect(0, UI_TOP_HEIGHT, UI_SIDE_WIDTH, h - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT), color=(40, 40, 40))
    right_panel = UIPanel(pygame.Rect(w - UI_RIGHT_SIDE_WIDTH, UI_TOP_HEIGHT, UI_RIGHT_SIDE_WIDTH, h - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT), color=(40, 40, 40))
    
    ui_manager.add_element(top_panel)
    ui_manager.add_element(bottom_panel)
    ui_manager.add_element(left_panel)
    ui_manager.add_element(right_panel)
    
    game_state = {
        "mode": "EDIT",
        "active_tool": None
    }
    
    # Top Panel Buttons
    pad = 10
    start_x = 10
    
    def add_top_btn(text, cb):
        nonlocal start_x
        # btn_w is min 80, or text length + 20 for padding
        btn_w = max(80, font.size(text)[0] + 20)
        ui_manager.add_element(UIButton(pygame.Rect(start_x, 10, btn_w, 30), text=text, font=font, callback=cb, click_sound="clunk_top.wav"))
        start_x += btn_w + pad

    # Level Manager
    level_manager = LevelManager()
    
    def apply_level_data(level_data, constraints_data=None, connections_data=None):
        if not level_data:
            return
            
        # Clean current space
        for entity in list(entities):
            if getattr(entity, 'body', None):
                for constraint in list(entity.body.constraints):
                    if constraint in space.constraints:
                        space.remove(constraint)
            if entity.shape and entity.shape.body:
                space.remove(*entity.shape.body.shapes)
                if entity.shape.body != space.static_body:
                    space.remove(entity.shape.body)
        entities.clear()
        active_instances.clear()
        
        # Instantiate parts based on level data
        for data in level_data:
            variant_key = data.get("entity_id")
            pos = data.get("position", {"x": 0, "y": 0})
            rot = data.get("rotation", 0)
            
            new_part = GamePart(space, pos["x"], pos["y"], variant_key)
            if "uuid" in data:
                new_part.uuid = data["uuid"]
            if "overrides" in data:
                new_part.apply_draft_overrides(data["overrides"])
            new_part.body.angle = rot
            space.reindex_shapes_for_body(new_part.body)
            entities.append(new_part)
            active_instances[new_part.uuid] = new_part
            
        # Pass 2: Instantiate Constraints
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
                        
        # Phase 4: M17 Instantiate logic connections
        if connections_data:
            for conn in connections_data:
                sender_uid = conn.get("sender")
                receiver_uid = conn.get("receiver")
                if sender_uid in active_instances and receiver_uid in active_instances:
                    # Wire them up immediately
                    active_instances[sender_uid].connected_uuids.append(receiver_uid)
            
    def handle_quick_save():
        level_manager.save_level(entities)
        
    def handle_quick_load():
        handle_clear()
        level_data, constraints_data, connections_data = level_manager.load_level()
        apply_level_data(level_data, constraints_data, connections_data)
        game_state["mode"] = "EDIT"

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

    def handle_clear():
        for entity in list(entities):
            if getattr(entity, 'body', None):
                for constraint in list(entity.body.constraints):
                    if constraint in space.constraints:
                        space.remove(constraint)
            if entity.shape and entity.shape.body:
                space.remove(*entity.shape.body.shapes)
                if entity.shape.body != space.static_body:
                    space.remove(entity.shape.body)
        entities.clear()
        active_instances.clear()

    def handle_play():
        game_state["mode"] = "PLAY"
        for entity in entities:
            if hasattr(entity, 'reset_logic'):
                entity.reset_logic()

    def handle_edit():
        game_state["mode"] = "EDIT"

    # Modes
    # Modes
    add_top_btn("Play", handle_play)
    add_top_btn("Edit", handle_edit)
    add_top_btn("Clear", handle_clear)
    add_top_btn("Q.Save", handle_quick_save)
    add_top_btn("Q.Load", handle_quick_load)
    add_top_btn("Save", handle_save)
    add_top_btn("Load", handle_load)
    
    # Stubs
    for stub in ["Challenges", "Help"]:
        add_top_btn(stub, dummy_action(stub))
        
    # Bottom Panel Labels and Dummy Button for bottom layer sounds
    ui_manager.add_element(UILabel(pygame.Rect(10, h - UI_BOTTOM_HEIGHT + 5, 200, 30), text="Score: 0", font=font))
    ui_manager.add_element(UILabel(pygame.Rect(w - 210, h - UI_BOTTOM_HEIGHT + 5, 200, 30), text="Timer: 00:00", font=font))
    ui_manager.add_element(UIButton(pygame.Rect(w - 320, h - UI_BOTTOM_HEIGHT + 5, 100, 30), text="Options", font=font, callback=dummy_action("Options"), click_sound="clunk_bottom.wav"))
    
    # Side Panels dynamic population from variants
    left_y_offset = UI_TOP_HEIGHT + 10
    
    # Track UI elements placed on the right
    right_panel_elements = []

    # Populate left panel
    # Phase 1 M17: Pin Wire tool to top left
    if "wire_tool" in all_variants:
        icon_surf = create_icon_surface("wire_tool", all_variants["wire_tool"])
        btn_x = (UI_SIDE_WIDTH - 60) // 2
        btn = UIButton(
            pygame.Rect(btn_x, left_y_offset, 60, 60), text="Wire Logic", font=small_font, 
            icon_surface=icon_surf, callback=set_active_tool("wire_tool", game_state), 
            click_sound="clunk_side.wav"
        )
        ui_manager.add_element(btn)
        left_y_offset += 70

    for i, (variant_key, variant_data) in enumerate(all_variants.items()):
        if variant_key == "wire_tool": continue
        if i % 2 == 0:
            icon_surf = create_icon_surface(variant_key, variant_data)
            label_text = variant_data.get("label", variant_key.replace("_", " ").title())
            btn_x = (UI_SIDE_WIDTH - 60) // 2
            
            btn_rect = pygame.Rect(btn_x, left_y_offset, 60, 60)
            btn = UIButton(
                btn_rect, text=label_text, font=small_font, icon_surface=icon_surf, 
                callback=set_active_tool(variant_key, game_state), click_sound="clunk_side.wav"
            )
            ui_manager.add_element(btn)
            left_y_offset += 70
            
    # Statically populate right panel once so they can be tracked
    ry = UI_TOP_HEIGHT + 10
    for i, (variant_key, variant_data) in enumerate(all_variants.items()):
        if variant_key == "wire_tool": continue
        if i % 2 != 0:
            icon_surf = create_icon_surface(variant_key, variant_data)
            label_text = variant_data.get("label", variant_key.replace("_", " ").title())
            btn_x = w - UI_RIGHT_SIDE_WIDTH + (UI_RIGHT_SIDE_WIDTH - 60) // 2
            
            btn = UIButton(
                pygame.Rect(btn_x, ry, 60, 60), text=label_text, font=small_font, 
                icon_surface=icon_surf, callback=set_active_tool(variant_key, game_state), 
                click_sound="clunk_side.wav"
            )
            ui_manager.add_element(btn)
            right_panel_elements.append(btn)
            ry += 70

    from utils.ui_manager import UITextInput, UITextArea

    panel_scroll_offset = [0] # List so it can be mutated within functions

    def build_right_panel():
        try:
            for el in right_panel_elements:
                if el in ui_manager.elements:
                    ui_manager.elements.remove(el)
            right_panel_elements.clear()

            selected = game_state.get("selected_instance")
            if selected is None:
                panel_scroll_offset[0] = 0
                ry = UI_TOP_HEIGHT + 10 + panel_scroll_offset[0]

                for i, (variant_key, variant_data) in enumerate(all_variants.items()):
                    if variant_key == "wire_tool": continue
                    if i % 2 != 0:
                            icon_surf = create_icon_surface(variant_key, variant_data)
                            label_text = variant_data.get("label", variant_key.replace("_", " ").title())
                            btn_x = w - UI_RIGHT_SIDE_WIDTH + (UI_RIGHT_SIDE_WIDTH - 60) // 2
                            
                            btn = UIButton(
                                pygame.Rect(btn_x, ry, 60, 60), text=label_text, font=small_font, 
                                icon_surface=icon_surf, callback=set_active_tool(variant_key, game_state), 
                                click_sound="clunk_side.wav"
                            )
                            ui_manager.add_element(btn)
                            right_panel_elements.append(btn)
                            ry += 70
            else:
                y_off = UI_TOP_HEIGHT + 10 + panel_scroll_offset[0]
                btn_x = w - UI_RIGHT_SIDE_WIDTH + 10
                lbl = UILabel(pygame.Rect(btn_x, y_off, UI_RIGHT_SIDE_WIDTH - 20, 20), text="Properties", font=small_font)
                ui_manager.add_element(lbl)
                right_panel_elements.append(lbl)
                y_off += 25
                
                inputs = {}
                all_keys = set(selected.properties.keys()).union(selected.overrides.keys())
                for k in sorted(list(all_keys)):
                    if k in ["visual", "template", "texture_path", "image", "label"]: continue
                    val = selected.get_property(k)
                    
                    klbl = UILabel(pygame.Rect(btn_x, y_off, UI_RIGHT_SIDE_WIDTH - 20, 15), text=k, font=small_font)
                    ui_manager.add_element(klbl)
                    right_panel_elements.append(klbl)
                    y_off += 15
                    
                    v_str = str(val)
                    if len(v_str) > 20 or "\n" in v_str:
                        inp = UITextArea(pygame.Rect(btn_x, y_off, UI_RIGHT_SIDE_WIDTH - 20, 50), font=small_font, text=v_str)
                        y_off += 55
                    else:
                        inp = UITextInput(pygame.Rect(btn_x, y_off, UI_RIGHT_SIDE_WIDTH - 20, 20), font=small_font, text=v_str)
                        y_off += 25
                        
                    ui_manager.add_element(inp)
                    right_panel_elements.append(inp)
                    inputs[k] = inp
                    
                def apply_props():
                    new_dict = {}
                    for k, inp in inputs.items():
                        val_str = inp.text
                        import ast
                        # Fix for list/dict representations:
                        try:
                            if val_str.startswith("[") or val_str.startswith("{"):
                                new_dict[k] = ast.literal_eval(val_str)
                            elif "." in val_str:
                                new_dict[k] = float(val_str)
                            else:
                                new_dict[k] = int(val_str)
                        except (ValueError, SyntaxError):
                            new_dict[k] = val_str
                    selected.apply_draft_overrides(new_dict)
                    game_state["selected_instance"] = None
                    build_right_panel()

                def cancel_props():
                    game_state["selected_instance"] = None
                    build_right_panel()
                    
                def reset_props():
                    if hasattr(selected, 'overrides'):
                        selected.overrides.clear()
                        # Reapply defaults by essentially applying empty overrides, or just forcing a reload of physics
                        selected.apply_draft_overrides({})
                    game_state["selected_instance"] = None
                    build_right_panel()

                y_off += 5
                btn_save = UIButton(pygame.Rect(btn_x, y_off, UI_RIGHT_SIDE_WIDTH - 20, 25), text="Save", font=small_font, callback=apply_props)
                ui_manager.add_element(btn_save)
                right_panel_elements.append(btn_save)
                y_off += 30
                
                btn_reset = UIButton(pygame.Rect(btn_x, y_off, UI_RIGHT_SIDE_WIDTH - 20, 25), text="Reset", font=small_font, callback=reset_props)
                ui_manager.add_element(btn_reset)
                right_panel_elements.append(btn_reset)
                y_off += 30
                
                btn_can = UIButton(pygame.Rect(btn_x, y_off, UI_RIGHT_SIDE_WIDTH - 20, 25), text="Cancel", font=small_font, callback=cancel_props)
                ui_manager.add_element(btn_can)
                right_panel_elements.append(btn_can)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"CRASH IN BUILD RIGHT PANEL: {e}")

    # initialize right panel (we already built the first state, just let it exist)
    # build_right_panel()

    # Initialize Pymunk Physics
    space = pymunk.Space()
    space.gravity = constants.GRAVITY
    create_boundaries(space)

    entities = []
    active_instances = {}
    
    def post_solve(arbiter, space, data):
        # Calculate collision magnitude
        if arbiter.total_impulse.length > 200:
            shape_a, shape_b = arbiter.shapes
            for entity in entities:
                if entity.shape in (shape_a, shape_b):
                    entity.play_event_sound("collision_sound")
        return True
        
    space.on_collision(collision_type_a=None, collision_type_b=None, post_solve=post_solve)
    
    def basket_sensor_begin(arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        target_shape = shape_a if shape_b.collision_type == 2 else shape_b
        basket_shape = shape_b if shape_b.collision_type == 2 else shape_a
        
        target_entity = None
        basket_entity = None
        
        for entity in list(entities):
            if getattr(entity, 'shapes', None):
                if target_shape in entity.shapes:
                    target_entity = entity
                if basket_shape in entity.shapes:
                    basket_entity = entity
            else:
                if getattr(entity, 'shape', None) == target_shape:
                    target_entity = entity
                if getattr(entity, 'shape', None) == basket_shape:
                    basket_entity = entity
                    
        if target_entity and basket_entity:
            # Phase 3: Type Filtering Logic
            accepts = basket_entity.get_property("accepts_types", ["all"])
            if isinstance(accepts, str):
                accepts = [accepts]
                
            if "all" in accepts or target_entity.variant_key in accepts:
                target_entity.to_delete = True
                
                # Phase 3: M17 Signal Queue Injection
                if basket_entity not in signal_queue:
                    signal_queue.append(basket_entity)
                    
                return False # Ingest, no physical bounce!
            else:
                return True # Reject, enforce physical bounce!
                
        return False

    space.on_collision(collision_type_a=2, collision_type_b=None, begin=basket_sensor_begin)

    def cannon_sensor_begin(arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        # One shape is the cannon sensor (type 3), the other is the incoming object
        target_shape = shape_a if shape_b.collision_type == 3 else shape_b
        cannon_shape = shape_b if shape_b.collision_type == 3 else shape_a
        
        # 1. Ingest (delete) the incoming projectile
        for entity in list(entities):
            if getattr(entity, 'shapes', None) and target_shape in entity.shapes:
                entity.to_delete = True
                break
            elif getattr(entity, 'shape', None) == target_shape:
                entity.to_delete = True
                break
                
        # 2. Trigger the cannon to fire immediately (or enqueue signal if it's acting as a Sender)
        for entity in list(entities):
            if getattr(entity, 'shapes', None) and cannon_shape in entity.shapes:
                entity.force_shoot = True
                # Phase 3: Enqueue signal if cannon was wired to another entity
                if entity not in signal_queue:
                    signal_queue.append(entity)
                break
                
        return False

    space.on_collision(collision_type_a=3, collision_type_b=None, begin=cannon_sensor_begin)
    
    grabbed_body = None
    prev_mode = game_state["mode"]
    game_state["wiring_source"] = None # Added for M17
    signal_queue = []

    running = True
    while running:
        current_mode = game_state["mode"]
        
        # Handle Mode Switch cleanups
        if current_mode != prev_mode:
            if current_mode == "PLAY":
                grabbed_body = None
                space.reindex_static()
            prev_mode = current_mode

        # 1. Reset hover state for all entities
        for entity in entities:
            entity.is_hovered = False
            
        m_pos = pygame.mouse.get_pos()
        
        # 2. Detect hover in EDIT mode if not currently dragging something
        if current_mode == "EDIT" and not grabbed_body:
            if playable_rect.collidepoint(m_pos):
                info = space.point_query_nearest(m_pos, 5.0, pymunk.ShapeFilter())
                if info and info.shape and info.shape.body != space.static_body:
                    for entity in entities:
                        if info.shape in getattr(entity, 'shapes', [entity.shape]):
                            entity.is_hovered = True
                            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Phase 4 & 5: Pass events to UIManager first
            if ui_manager.process_event(event):
                # UI Consumed the event, skip physics interactions
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    # Check if click is inside the playable rect before interacting with the world
                    if playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
                        info = space.point_query_nearest(event.pos, 5.0, pymunk.ShapeFilter())
                        if info and info.shape and info.shape.body != space.static_body:
                            # Phase 1: M17 Wire Tool Logic
                            if game_state["active_tool"] == "wire_tool":
                                target_entity = None
                                for entity in entities:
                                    if info.shape in getattr(entity, 'shapes', [entity.shape]):
                                        target_entity = entity
                                        break
                                        
                                if target_entity:
                                    if game_state["wiring_source"] is None:
                                        game_state["wiring_source"] = target_entity
                                    elif game_state["wiring_source"] != target_entity:
                                        # Link UUIDs
                                        game_state["wiring_source"].connected_uuids.append(target_entity.uuid)
                                        target_entity.play_event_sound("spawn_sound") # Feedback
                                        game_state["wiring_source"] = None
                            else:
                                # Normal Grab/Selection Loop
                                # Grab the body
                                grabbed_body = info.shape.body
                                
                                # Phase 3 Selection Logic
                                # Find which entity owns this shape
                                for entity in entities:
                                    if info.shape in getattr(entity, 'shapes', [entity.shape]):
                                        game_state["selected_instance"] = entity
                                        build_right_panel()
                                        break
                        elif game_state["active_tool"] is not None and game_state["active_tool"] != "wire_tool":
                            # Spawning logic via active tool
                            variant_key = game_state["active_tool"]
                            m_x, m_y = event.pos
                            new_part = GamePart(space, m_x, m_y, variant_key)
                            entities.append(new_part)
                            active_instances[new_part.uuid] = new_part
                            new_part.play_event_sound("spawn_sound")
                        else:
                            # Deselect if clicking empty space (or cancel wire tool)
                            game_state["wiring_source"] = None
                            if game_state.get("selected_instance") is not None:
                                game_state["selected_instance"] = None
                                build_right_panel()
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"CRASH IN CLICK LOOP: {e}")
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # Right-click deletion
                if playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
                    info = space.point_query_nearest(event.pos, 5.0, pymunk.ShapeFilter())
                    if info and info.shape and info.shape.body != space.static_body:
                        for entity in list(entities):
                            if info.shape in getattr(entity, 'shapes', [entity.shape]):
                                if getattr(entity, 'body', None):
                                    for constraint in list(entity.body.constraints):
                                        if constraint in space.constraints:
                                            space.remove(constraint)
                                            
                                space.remove(*entity.shape.body.shapes)
                                if entity.shape.body != space.static_body:
                                    space.remove(entity.shape.body)
                                entities.remove(entity)
                                if entity.uuid in active_instances:
                                    del active_instances[entity.uuid]
                                break
            
            elif event.type == pygame.MOUSEMOTION:
                if current_mode == "EDIT" and grabbed_body:
                    grabbed_body.position = event.pos
                    if grabbed_body.body_type == pymunk.Body.DYNAMIC:
                        grabbed_body.velocity = (0, 0)
                        grabbed_body.angular_velocity = 0
                    space.reindex_shapes_for_body(grabbed_body)
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                grabbed_body = None
                
            elif event.type == pygame.MOUSEWHEEL:
                if current_mode == "EDIT":
                    # Check if mouse is over the right panel
                    if pygame.mouse.get_pos()[0] > w - UI_RIGHT_SIDE_WIDTH:
                        if game_state.get("selected_instance") is not None:
                            panel_scroll_offset[0] += event.y * 20
                            # clamp scroll offset so it doesn't go below 0 (downwards)
                            if panel_scroll_offset[0] > 0:
                                panel_scroll_offset[0] = 0
                            build_right_panel()
                    else:
                        target = grabbed_body
                        if not target:
                            info = space.point_query_nearest(pygame.mouse.get_pos(), 5.0, pymunk.ShapeFilter())
                            if info and info.shape and info.shape.body != space.static_body:
                                target = info.shape.body
                        if target:
                            target.angle += event.y * 0.1
                            space.reindex_shapes_for_body(target)

        # Continuous rotation checks while in edit mode
        if current_mode == "EDIT" and grabbed_body and not ui_manager.focused_element:
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

        # Game State Engine
        if current_mode == "PLAY":
            space.step(constants.PHYSICS_STEP)
            
            # Phase 3: Process Logic Signals cleanly OUTSIDE the physics step
            while signal_queue:
                sender = signal_queue.pop(0)
                sender.flash_timer = 15 # Set frame flash duration
                if hasattr(sender, 'connected_uuids'):
                    for tgt_uuid in sender.connected_uuids:
                        tgt = active_instances.get(tgt_uuid)
                        if tgt and hasattr(tgt, 'receive_signal'):
                            tgt.receive_signal(payload=sender)
            
            # Process logic updates and ingestions
            for entity in list(entities):
                if getattr(entity, 'flash_timer', 0) > 0:
                    entity.flash_timer -= 1
                if getattr(entity, 'to_delete', False):
                    # Cleanup the entity
                    if getattr(entity, 'body', None):
                        for constraint in list(entity.body.constraints):
                            if constraint in space.constraints:
                                space.remove(constraint)
                                
                    for shape in getattr(entity, 'shapes', [entity.shape]):
                        if shape and shape.body and shape in space.shapes:
                            space.remove(shape)
                    if entity.body and entity.body != space.static_body and entity.body in space.bodies:
                        space.remove(entity.body)
                    if entity in entities:
                        entities.remove(entity)
                    if entity.uuid in active_instances:
                        del active_instances[entity.uuid]
                    continue
                
                if hasattr(entity, 'update_logic'):
                    entity.update_logic(constants.PHYSICS_STEP, game_state, entities, active_instances)
                    
        # Draw Background via EnvironmentManager
        env_manager.draw_background(screen)

        # Draw all entities
        for entity in entities:
            entity.update_visual(screen)
            
            # Phase 6: Visual indicator
            if current_mode == "EDIT" and getattr(entity, 'overrides', {}):
                body = getattr(entity, 'body', None)
                if body:
                    x, y = int(body.position.x), int(body.position.y)
                    # Draw a small magenta dot/circle in the center to indicate overrides
                    pygame.draw.circle(screen, (255, 0, 255), (x, y), 5)
                    pygame.draw.circle(screen, (0, 0, 0), (x, y), 5, 1)

            # Phase 2: M17 Logic Wiring Renderer
            if current_mode in ["EDIT", "PLAY"] or game_state["active_tool"] == "wire_tool":
                if hasattr(entity, 'connected_uuids') and entity.body:
                    start_pos = (int(entity.body.position.x), int(entity.body.position.y))
                    for tgt_uuid in entity.connected_uuids:
                        tgt = active_instances.get(tgt_uuid)
                        if tgt and tgt.body:
                            end_pos = (int(tgt.body.position.x), int(tgt.body.position.y))
                            
                            flash = getattr(entity, 'flash_timer', 0)
                            if flash > 0:
                                wire_color = (0, 255, 255) # Cyan flash
                                width = 3
                            else:
                                wire_color = (255, 255, 0)
                                if current_mode == "PLAY":
                                    wire_color = (255, 200, 0) # Brighter orange/yellow so it doesn't disappear against the background
                                width = 1

                            # Draw an anti-aliased logical line
                            if width == 1:
                                pygame.draw.aaline(screen, wire_color, start_pos, end_pos)
                            else:
                                pygame.draw.line(screen, wire_color, start_pos, end_pos, width) # bold for flashes
                                
                            # Draw an arrowhead to indicate direction (Sender -> Receiver)
                            direction = pymunk.Vec2d(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
                            if direction.length > 20:
                                direction = direction.normalized()
                                arrow_base = (end_pos[0] - int(direction.x * 15), end_pos[1] - int(direction.y * 15))
                                left_wing = (arrow_base[0] - int(direction.y * 5), arrow_base[1] + int(direction.x * 5))
                                right_wing = (arrow_base[0] + int(direction.y * 5), arrow_base[1] - int(direction.x * 5))
                                pygame.draw.polygon(screen, wire_color, [end_pos, left_wing, right_wing])

        # Phase 1: M17 Active Wiring preview line
        if current_mode == "EDIT" and game_state["active_tool"] == "wire_tool" and game_state.get("wiring_source"):
            src = game_state["wiring_source"]
            if src.body:
                start_x, start_y = int(src.body.position.x), int(src.body.position.y)
                pygame.draw.aaline(screen, (255, 150, 0), (start_x, start_y), m_pos)
            
        # Phase 5: Ghost Cursor Preview
        if current_mode == "EDIT" and not grabbed_body and game_state["active_tool"] is not None:
            if playable_rect.collidepoint(m_pos):
                active_tool_key = game_state["active_tool"]
                preview_surf = create_icon_surface(active_tool_key, all_variants[active_tool_key])
                preview_surf.set_alpha(128) # semi-transparent
                preview_rect = preview_surf.get_rect(center=m_pos)
                screen.blit(preview_surf, preview_rect)

        # Mode Indicator Border
        border_color = env_manager.edit_mode_color if current_mode == "EDIT" else env_manager.play_mode_color
        pygame.draw.rect(screen, border_color, playable_rect, 5)

        # Phase 1, 3, 4: Draw UI Overlay
        ui_manager.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
