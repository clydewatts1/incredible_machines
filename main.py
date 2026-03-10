import pygame
import pymunk
import sys
import os
import tkinter as tk
from tkinter import filedialog

import constants
from entities.base import GamePart
from entities.active import FactoryPart
from entities.source import DataSource
from entities.sink import DataSink
from utils.sound_manager import sound_manager
from utils.environment_manager import env_manager
from utils.config_loader import load_all_variants
from utils.ui_manager import UIManager, UIPanel, UIButton, UILabel, UIScrollPanel, UITextInput, UITextArea
from utils.level_manager import LevelManager
from utils.camera import Camera

UI_TOP_HEIGHT = 50
UI_BOTTOM_HEIGHT = 40
UI_SIDE_WIDTH = 260
UI_RIGHT_SIDE_WIDTH = 320

def create_boundaries(space, world_width, world_height):
    """Create static boundaries for the full world canvas."""
    static_body = space.static_body
    thickness = 4.0

    left = 0
    right = world_width
    top = 0
    bottom = world_height
    
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


def create_part(space, x, y, variant_key):
    """Route entity construction through specialized classes when required."""
    if variant_key == "logic_factory":
        return FactoryPart(space, x, y, variant_key)
    elif variant_key in ("data_source", "data_source_csv", "data_source_mcp"):
        return DataSource(space, x, y, variant_key)
    elif variant_key.startswith("data_sink"):
        return DataSink(space, x, y, variant_key)
    return GamePart(space, x, y, variant_key)


def snap_to_grid(world_x, world_y):
    """
    M25 Phase 4: Snap world coordinates to the nearest grid intersection.
    
    Args:
        world_x: X coordinate in world space
        world_y: Y coordinate in world space
        
    Returns:
        Tuple of (snapped_x, snapped_y)
    """
    snapped_x = round(world_x / constants.GRID_SIZE) * constants.GRID_SIZE
    snapped_y = round(world_y / constants.GRID_SIZE) * constants.GRID_SIZE
    return (snapped_x, snapped_y)

def main():
    pygame.init()
    sound_manager.initialize()
    env_manager.initialize(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)
    
    all_variants = load_all_variants()
    
    # Phase 1: M17 Wire Tool Hack - Inject a fake variant so it gets a button
    if "wire_tool" not in all_variants:
        all_variants["wire_tool"] = {
            "label": "Wire Logic",
            "category": "logic",
            "template": "Rectangle",
            "color": [255, 255, 0]
        }

    categories = sorted({
        str(variant_data.get("category", "other")).lower()
        for variant_data in all_variants.values()
    })
    
    screen = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    pygame.display.set_caption("The Incredible Machine Clone - Milestone 9")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 16) # For Palette labels

    # Instantiate UIManager
    ui_manager = UIManager()
    
    w, h = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
    
    # Phase 3 & 4: Construct static UI Panels
    top_panel = UIPanel(pygame.Rect(0, 0, w, UI_TOP_HEIGHT), color=(50, 50, 50))
    bottom_panel = UIPanel(pygame.Rect(0, h - UI_BOTTOM_HEIGHT, w, UI_BOTTOM_HEIGHT), color=(50, 50, 50))
    left_panel = UIPanel(pygame.Rect(0, UI_TOP_HEIGHT, UI_SIDE_WIDTH, h - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT), color=(40, 40, 40))
    right_panel = UIPanel(pygame.Rect(w - UI_RIGHT_SIDE_WIDTH, UI_TOP_HEIGHT, UI_RIGHT_SIDE_WIDTH, h - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT), color=(40, 40, 40))

    # M25 UI polish: playable area is strictly framed by panel edges.
    playable_rect = pygame.Rect(
        left_panel.rect.right,
        top_panel.rect.bottom,
        right_panel.rect.left - left_panel.rect.right,
        bottom_panel.rect.top - top_panel.rect.bottom,
    )
    
    ui_manager.add_element(top_panel)
    ui_manager.add_element(bottom_panel)
    ui_manager.add_element(left_panel)
    ui_manager.add_element(right_panel)
    
    game_state = {
        "mode": "EDIT",
        "active_tool": None,
        "snap_to_grid": False,
        "show_grid": True,
        "selected_instance": None,
        "selected_category": "all",
    }

    # Track UI groups so panel rebuilds do not remove unrelated elements.
    top_bar_elements = []
    left_panel_elements = []
    category_tab_elements = []

    right_scroll_rect = pygame.Rect(
        right_panel.rect.x + 10,
        right_panel.rect.y + 76,
        right_panel.rect.width - 20,
        right_panel.rect.height - 86,
    )
    right_scroll_panel = UIScrollPanel(right_scroll_rect, color=(45, 45, 45), alpha=220)
    ui_manager.add_element(right_scroll_panel)

    right_panel_title = UILabel(
        pygame.Rect(right_panel.rect.x + 10, right_panel.rect.y + 8, right_panel.rect.width - 20, 24),
        text="Palette",
        font=font,
    )
    ui_manager.add_element(right_panel_title)

    def clear_top_bar():
        for element in top_bar_elements:
            if element in ui_manager.elements:
                ui_manager.elements.remove(element)
        top_bar_elements.clear()

    def clear_category_tabs():
        for element in category_tab_elements:
            if element in ui_manager.elements:
                ui_manager.elements.remove(element)
        category_tab_elements.clear()

    def add_top_btn_at(x, text, callback):
        btn_w = max(80, font.size(text)[0] + 20)
        btn = UIButton(
            pygame.Rect(int(x), 10, btn_w, 30),
            text=text,
            font=font,
            callback=callback,
            click_sound="clunk_top.wav",
        )
        ui_manager.add_element(btn)
        top_bar_elements.append(btn)
        return btn_w

    # Level Manager
    level_manager = LevelManager()
    
    def apply_level_data(level_data, constraints_data=None, connections_data=None):
        if not level_data:
            return
            
        # Clean current space
        for entity in list(entities):
            if hasattr(entity, 'cleanup'):
                entity.cleanup()
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
            
            new_part = create_part(space, pos["x"], pos["y"], variant_key)
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
            if hasattr(entity, 'cleanup'):
                entity.cleanup()
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
    
    def toggle_snap_to_grid():
        game_state["snap_to_grid"] = not game_state.get("snap_to_grid", False)
        build_top_panel()

    def build_top_panel():
        clear_top_bar()

        snap_enabled = game_state.get("snap_to_grid", False)
        snap_label = "Snap: ON" if snap_enabled else "Snap: OFF"

        # Left-aligned cluster: modes.
        left_x = 10
        for text, callback in [
            ("Play", handle_play),
            ("Edit", handle_edit),
            ("Clear", handle_clear),
            (snap_label, toggle_snap_to_grid),
        ]:
            left_x += add_top_btn_at(left_x, text, callback) + 8

        # Center-aligned cluster: file ops.
        center_buttons = [
            ("Q.Save", handle_quick_save),
            ("Q.Load", handle_quick_load),
            ("Save", handle_save),
            ("Load", handle_load),
        ]
        center_gap = 8
        center_width = sum(max(80, font.size(t)[0] + 20) for t, _ in center_buttons) + center_gap * (len(center_buttons) - 1)
        center_x = (w - center_width) // 2
        for text, callback in center_buttons:
            center_x += add_top_btn_at(center_x, text, callback) + center_gap

        # Right-aligned cluster: meta.
        meta_buttons = [
            ("Challenges", dummy_action("Challenges")),
            ("Help", dummy_action("Help")),
            ("Level Settings", dummy_action("Level Settings")),
        ]
        right_gap = 8
        right_width = sum(max(80, font.size(t)[0] + 20) for t, _ in meta_buttons) + right_gap * (len(meta_buttons) - 1)
        right_x = w - right_width - 10
        for text, callback in meta_buttons:
            right_x += add_top_btn_at(right_x, text, callback) + right_gap

    def build_category_tabs():
        clear_category_tabs()

        selected_category = game_state.get("selected_category", "all")
        tab_area_left = right_panel.rect.x + 10
        tab_area_right = right_panel.rect.right - 10
        tab_y = right_panel.rect.y + 38
        tab_x = tab_area_left
        tab_gap = 6
        row_gap = 4
        tab_height = 24
        row_count = 1

        tab_entries = ["all"] + categories
        for category_name in tab_entries:
            label = category_name.title()
            tab_width = max(52, small_font.size(label)[0] + 14)
            is_selected = category_name == selected_category

            if tab_x + tab_width > tab_area_right and tab_x > tab_area_left:
                tab_x = tab_area_left
                tab_y += tab_height + row_gap
                row_count += 1

            def make_callback(cat):
                def _callback():
                    game_state["selected_category"] = cat
                    build_category_tabs()
                    build_right_palette()
                return _callback

            tab_btn = UIButton(
                pygame.Rect(tab_x, tab_y, tab_width, tab_height),
                text=label,
                font=small_font,
                callback=make_callback(category_name),
                bg_color=(90, 130, 90) if is_selected else (70, 70, 70),
                hover_color=(120, 170, 120) if is_selected else (100, 100, 100),
                click_sound="clunk_side.wav",
            )
            ui_manager.add_element(tab_btn)
            category_tab_elements.append(tab_btn)
            tab_x += tab_width + tab_gap

        tabs_bottom = right_panel.rect.y + 38 + row_count * tab_height + max(0, row_count - 1) * row_gap
        right_scroll_panel.rect.y = tabs_bottom + 8
        right_scroll_panel.rect.height = max(60, right_panel.rect.bottom - 10 - right_scroll_panel.rect.y)

    def build_right_palette():
        right_scroll_panel.clear_children()

        padding = 10
        gap_x = 8
        gap_y = 8
        button_height = 70
        button_width = (right_scroll_panel.rect.width - (padding * 2) - (gap_x * 2)) // 3

        selected_category = game_state.get("selected_category", "all")
        palette_variants = [
            (k, v)
            for k, v in all_variants.items()
            if selected_category == "all" or str(v.get("category", "other")).lower() == selected_category
        ]
        for index, (variant_key, variant_data) in enumerate(palette_variants):
            col = index % 3
            row = index // 3
            btn_x = right_scroll_panel.rect.x + padding + col * (button_width + gap_x)
            btn_y = right_scroll_panel.rect.y + padding + row * (button_height + gap_y)
            icon_surf = create_icon_surface(variant_key, variant_data)
            label_text = variant_data.get("label", variant_key.replace("_", " ").title())
            btn = UIButton(
                pygame.Rect(btn_x, btn_y, button_width, button_height),
                text=label_text,
                font=small_font,
                icon_surface=icon_surf,
                callback=set_active_tool(variant_key, game_state),
                click_sound="clunk_side.wav",
            )
            right_scroll_panel.add_child(btn)

        rows = (len(palette_variants) + 2) // 3
        right_scroll_panel.content_height = padding * 2 + rows * button_height + max(0, rows - 1) * gap_y
        right_scroll_panel._clamp_scroll()

    def build_left_inspector():
        for element in left_panel_elements:
            if element in ui_manager.elements:
                ui_manager.elements.remove(element)
        left_panel_elements.clear()

        selected = game_state.get("selected_instance")
        x = left_panel.rect.x + 10
        y = left_panel.rect.y + 10
        width = left_panel.rect.width - 20

        title = UILabel(pygame.Rect(x, y, width, 24), text="Inspector", font=font)
        ui_manager.add_element(title)
        left_panel_elements.append(title)
        y += 30

        if selected is None:
            hint = UILabel(pygame.Rect(x, y, width, 24), text="Select an object", font=small_font)
            ui_manager.add_element(hint)
            left_panel_elements.append(hint)
            return

        inputs = {}
        all_keys = set(selected.properties.keys()).union(selected.overrides.keys())
        for key in sorted(list(all_keys)):
            if key in ["visual", "template", "texture_path", "image", "label"]:
                continue

            key_label = UILabel(pygame.Rect(x, y, width, 16), text=key, font=small_font)
            ui_manager.add_element(key_label)
            left_panel_elements.append(key_label)
            y += 18

            val_str = str(selected.get_property(key))
            if len(val_str) > 28 or "\n" in val_str:
                field = UITextArea(pygame.Rect(x, y, width, 54), font=small_font, text=val_str)
                y += 58
            else:
                field = UITextInput(pygame.Rect(x, y, width, 22), font=small_font, text=val_str)
                y += 28
            ui_manager.add_element(field)
            left_panel_elements.append(field)
            inputs[key] = field

        def apply_props():
            import ast
            new_dict = {}
            for key, field in inputs.items():
                text = field.text
                try:
                    if text.startswith("[") or text.startswith("{"):
                        new_dict[key] = ast.literal_eval(text)
                    elif "." in text:
                        new_dict[key] = float(text)
                    else:
                        new_dict[key] = int(text)
                except (ValueError, SyntaxError):
                    new_dict[key] = text
            selected.apply_draft_overrides(new_dict)
            game_state["selected_instance"] = None
            build_left_inspector()

        def reset_props():
            if hasattr(selected, "overrides"):
                selected.overrides.clear()
                selected.apply_draft_overrides({})
            game_state["selected_instance"] = None
            build_left_inspector()

        def cancel_props():
            game_state["selected_instance"] = None
            build_left_inspector()

        y += 4
        for text, callback in [("Save", apply_props), ("Reset", reset_props), ("Cancel", cancel_props)]:
            btn = UIButton(pygame.Rect(x, y, width, 26), text=text, font=small_font, callback=callback)
            ui_manager.add_element(btn)
            left_panel_elements.append(btn)
            y += 30

    build_top_panel()
    build_category_tabs()
    build_right_palette()
    build_left_inspector()
        
    # Bottom Panel Labels and Dummy Button for bottom layer sounds
    ui_manager.add_element(UILabel(pygame.Rect(10, h - UI_BOTTOM_HEIGHT + 5, 200, 30), text="Score: 0", font=font))
    ui_manager.add_element(UILabel(pygame.Rect(w - 210, h - UI_BOTTOM_HEIGHT + 5, 200, 30), text="Timer: 00:00", font=font))
    ui_manager.add_element(UIButton(pygame.Rect(w - 320, h - UI_BOTTOM_HEIGHT + 5, 100, 30), text="Options", font=font, callback=dummy_action("Options"), click_sound="clunk_bottom.wav"))
    
    # Initialize Pymunk Physics
    space = pymunk.Space()
    space.gravity = constants.GRAVITY
    create_boundaries(space, constants.WORLD_WIDTH, constants.WORLD_HEIGHT)
    
    # M25 Phase 2: Initialize Camera for infinite canvas
    camera = Camera(
        world_width=constants.WORLD_WIDTH,
        world_height=constants.WORLD_HEIGHT,
        screen_width=constants.WINDOW_WIDTH,
        screen_height=constants.WINDOW_HEIGHT
    )

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
        target_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_BASKET else shape_b
        basket_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_BASKET else shape_a
        
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

    space.on_collision(collision_type_a=constants.COLLISION_TYPE_BASKET, collision_type_b=None, begin=basket_sensor_begin)

    def cannon_sensor_begin(arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        # One shape is the cannon sensor (type 3), the other is the incoming object
        target_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_CANNON else shape_b
        cannon_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_CANNON else shape_a
        
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

    space.on_collision(collision_type_a=constants.COLLISION_TYPE_CANNON, collision_type_b=None, begin=cannon_sensor_begin)

    def factory_sensor_begin(arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_FACTORY_TOP else shape_b
        factory_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_FACTORY_TOP else shape_a

        incoming_entity = None
        factory_entity = None

        for entity in list(entities):
            if getattr(entity, 'shapes', None):
                if incoming_shape in entity.shapes:
                    incoming_entity = entity
                if factory_shape in entity.shapes:
                    factory_entity = entity

        if not incoming_entity or not factory_entity:
            return True

        if getattr(factory_entity, 'variant_key', None) != 'logic_factory':
            return True

        if incoming_entity.uuid == factory_entity.uuid:
            return True

        # During cooldown the top edge behaves as a solid wall.
        if getattr(factory_entity, 'cooldown_timer', 0.0) > 0.0:
            return True

        accepted = factory_entity.ingest_payload(incoming_entity)
        return not accepted

    space.on_collision(
        collision_type_a=constants.COLLISION_TYPE_FACTORY_TOP,
        collision_type_b=None,
        begin=factory_sensor_begin,
    )

    def sink_sensor_begin(arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        incoming_shape = shape_a if shape_b.collision_type == constants.COLLISION_TYPE_SINK_TOP else shape_b
        sink_shape = shape_b if shape_b.collision_type == constants.COLLISION_TYPE_SINK_TOP else shape_a

        incoming_entity = None
        sink_entity = None

        for entity in list(entities):
            entity_shapes = getattr(entity, 'shapes', [getattr(entity, 'shape', None)])
            if incoming_shape in entity_shapes:
                incoming_entity = entity
            if sink_shape in entity_shapes:
                sink_entity = entity

        if not incoming_entity or not sink_entity:
            return True

        if getattr(sink_entity, 'variant_key', '').startswith('data_sink') is False:
            return True

        if incoming_entity.uuid == sink_entity.uuid:
            return True

        accepted = sink_entity.ingest_payload(incoming_entity)
        return not accepted

    space.on_collision(
        collision_type_a=constants.COLLISION_TYPE_SINK_TOP,
        collision_type_b=None,
        begin=sink_sensor_begin,
    )
    
    grabbed_body = None
    prev_mode = game_state["mode"]
    game_state["wiring_source"] = None # Added for M17
    signal_queue = []
    
    # M25 Phase 6: Drag-to-Trash UX
    trash_can_visible = False
    trash_can_rect = pygame.Rect(w // 2 - 40, h - 100, 80, 80)
    cursor_over_trash = False
    
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
        
        # M25 Phase 3: Convert mouse position to world space for physics queries
        world_m_pos = camera.screen_to_world(m_pos[0], m_pos[1])
        
        # 2. Detect hover in EDIT mode if not currently dragging something
        if current_mode == "EDIT" and not grabbed_body:
            if playable_rect.collidepoint(m_pos):
                info = space.point_query_nearest(world_m_pos, 5.0, pymunk.ShapeFilter())
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
            
            # M25 Phase 3: Middle Mouse Button Camera Panning
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                camera.begin_pan(event.pos[0], event.pos[1])
                continue
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                camera.end_pan()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    # M25 Phase 3: Convert click position to world space
                    world_click_pos = camera.screen_to_world(event.pos[0], event.pos[1])
                    
                    # Check if click is inside the playable rect before interacting with the world
                    if playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
                        info = space.point_query_nearest(world_click_pos, 5.0, pymunk.ShapeFilter())
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
                                # M25 Phase 6: Show trash can when grabbing an object
                                trash_can_visible = True
                                
                                # Phase 3 Selection Logic
                                # Find which entity owns this shape
                                for entity in entities:
                                    if info.shape in getattr(entity, 'shapes', [entity.shape]):
                                        game_state["selected_instance"] = entity
                                        build_left_inspector()
                                        break
                        elif game_state["active_tool"] is not None and game_state["active_tool"] != "wire_tool":
                            # M25 Phase 3: Spawning logic uses world-space position
                            # M25 Phase 4: Apply grid snapping if enabled
                            variant_key = game_state["active_tool"]
                            spawn_x, spawn_y = world_click_pos
                            
                            if game_state.get("snap_to_grid", False):
                                spawn_x, spawn_y = snap_to_grid(spawn_x, spawn_y)
                            
                            new_part = create_part(space, spawn_x, spawn_y, variant_key)
                            entities.append(new_part)
                            active_instances[new_part.uuid] = new_part
                            new_part.play_event_sound("spawn_sound")
                        else:
                            # Deselect if clicking empty space (or cancel wire tool)
                            game_state["wiring_source"] = None
                            if game_state.get("selected_instance") is not None:
                                game_state["selected_instance"] = None
                                build_left_inspector()
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"CRASH IN CLICK LOOP: {e}")
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # M25 Phase 3: Right-click deletion with world-space coordinates
                world_click_pos = camera.screen_to_world(event.pos[0], event.pos[1])
                
                # Right-click deletion
                if playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
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
                                            
                                space.remove(*entity.shape.body.shapes)
                                if entity.shape.body != space.static_body:
                                    space.remove(entity.shape.body)
                                entities.remove(entity)
                                if entity.uuid in active_instances:
                                    del active_instances[entity.uuid]
                                break
            
            elif event.type == pygame.MOUSEMOTION:
                # M25 Phase 3: Update camera pan if middle mouse button dragging
                if camera.is_panning:
                    camera.update_pan(event.pos[0], event.pos[1])
                
                # M25 Phase 6: Update cursor over trash state
                if trash_can_visible:
                    cursor_over_trash = trash_can_rect.collidepoint(event.pos[0], event.pos[1])
                
                # M25 Phase 3: Dragging with world-space coordinates
                # M25 Phase 4: Apply grid snapping if enabled
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
                # M25 Phase 6: Check if releasing over trash can
                if grabbed_body and cursor_over_trash and current_mode == "EDIT":
                    # Find entity associated with grabbed_body
                    entity_to_delete = None
                    for entity in entities:
                        if hasattr(entity, 'body') and entity.body == grabbed_body:
                            entity_to_delete = entity
                            break
                    
                    # Safe deletion (from M11/M13)
                    if entity_to_delete:
                        # Cleanup
                        if hasattr(entity_to_delete, 'cleanup'):
                            entity_to_delete.cleanup()
                        
                        # Remove from active_instances
                        if hasattr(entity_to_delete, 'uuid') and entity_to_delete.uuid in active_instances:
                            del active_instances[entity_to_delete.uuid]
                        
                        # Remove from entities list
                        if entity_to_delete in entities:
                            entities.remove(entity_to_delete)
                        
                        # Remove from Pymunk space
                        if hasattr(entity_to_delete, 'body') and entity_to_delete.body:
                            # Remove constraints first
                            for constraint in list(entity_to_delete.body.constraints):
                                if constraint in space.constraints:
                                    space.remove(constraint)
                            # Remove shapes
                            if hasattr(entity_to_delete, 'shape') and entity_to_delete.shape:
                                if entity_to_delete.shape.body and entity_to_delete.shape.body != space.static_body:
                                    space.remove(*entity_to_delete.shape.body.shapes)
                                    space.remove(entity_to_delete.shape.body)
                
                grabbed_body = None
                trash_can_visible = False
                
            elif event.type == pygame.MOUSEWHEEL:
                if current_mode == "EDIT":
                    # World rotation still works when wheel wasn't consumed by the UI scroll panel.
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
        
        # M25 Phase 3: Keyboard-based camera panning (WASD / Arrow Keys)
        if not ui_manager.focused_element:
            keys = pygame.key.get_pressed()
            dt = clock.get_time() / 1000.0  # Convert milliseconds to seconds
            camera.handle_keyboard_pan(keys, constants.CAMERA_PAN_SPEED, dt)

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
                    # Cleanup the entity
                    if hasattr(entity, 'cleanup'):
                        entity.cleanup()
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
                    
        # ═══════════════════════════════════════════════════════════════
        # M25 PHASE 2: THREE-LAYER RENDER SYSTEM
        # ═══════════════════════════════════════════════════════════════
        
        # ───────────────────────────────────────────────────────────────
        # LAYER 1: Background & Grid (Camera Offset Applied)
        # ───────────────────────────────────────────────────────────────
        env_manager.draw_background(screen)
        
        # M25 Phase 4: Draw grid overlay in EDIT mode
        if current_mode == "EDIT" and game_state.get("show_grid", True):
            # Calculate grid origin offset by camera
            grid_origin_x = -(camera.offset_x % constants.GRID_SIZE)
            grid_origin_y = -(camera.offset_y % constants.GRID_SIZE)
            
            # Create a semi-transparent surface for the grid
            grid_surface = pygame.Surface((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
            grid_surface.set_alpha(constants.GRID_ALPHA)
            grid_surface.fill((0, 0, 0))  # Fill with black (will be made transparent)
            grid_surface.set_colorkey((0, 0, 0))  # Make black transparent
            
            # Draw vertical lines
            x = grid_origin_x
            while x < constants.WINDOW_WIDTH:
                pygame.draw.line(grid_surface, constants.GRID_COLOR, (int(x), 0), (int(x), constants.WINDOW_HEIGHT), 1)
                x += constants.GRID_SIZE
            
            # Draw horizontal lines
            y = grid_origin_y
            while y < constants.WINDOW_HEIGHT:
                pygame.draw.line(grid_surface, constants.GRID_COLOR, (0, int(y)), (constants.WINDOW_WIDTH, int(y)), 1)
                y += constants.GRID_SIZE
            
            screen.blit(grid_surface, (0, 0))
        
        # ───────────────────────────────────────────────────────────────
        # LAYER 2: World Entities (Camera Offset Applied)
        # ───────────────────────────────────────────────────────────────
        
        # Draw all entities with camera translation
        for entity in entities:
            # Get world-space position
            if hasattr(entity, 'body') and entity.body:
                world_x, world_y = entity.body.position.x, entity.body.position.y
                screen_x, screen_y = camera.world_to_screen(world_x, world_y)
                
                # Only render if on-screen (basic culling)
                if (-100 < screen_x < constants.WINDOW_WIDTH + 100 and 
                    -100 < screen_y < constants.WINDOW_HEIGHT + 100):
                    
                    # Temporarily offset the body for rendering, then restore
                    # (We can't mutate Pymunk bodies, so we'll pass screen coords to update_visual)
                    # For now, update_visual will need modification - let's use a simpler approach
                    # and create a camera-aware rendering method
                    entity.update_visual(screen, camera=camera)
                    
                    # Phase 6: Visual indicator for overrides
                    if current_mode == "EDIT" and getattr(entity, 'overrides', {}):
                        sx, sy = int(screen_x), int(screen_y)
                        pygame.draw.circle(screen, (255, 0, 255), (sx, sy), 5)
                        pygame.draw.circle(screen, (0, 0, 0), (sx, sy), 5, 1)
            
            # M17 Logic Wiring Renderer (with camera offset)
            if current_mode in ["EDIT", "PLAY"] or game_state["active_tool"] == "wire_tool":
                if hasattr(entity, 'connected_uuids') and entity.body:
                    world_start_x, world_start_y = entity.body.position.x, entity.body.position.y
                    screen_start = camera.world_to_screen(world_start_x, world_start_y)
                    start_pos = (int(screen_start[0]), int(screen_start[1]))
                    
                    for tgt_uuid in entity.connected_uuids:
                        tgt = active_instances.get(tgt_uuid)
                        if tgt and tgt.body:
                            world_end_x, world_end_y = tgt.body.position.x, tgt.body.position.y
                            screen_end = camera.world_to_screen(world_end_x, world_end_y)
                            end_pos = (int(screen_end[0]), int(screen_end[1]))
                            
                            flash = getattr(entity, 'flash_timer', 0)
                            if flash > 0:
                                wire_color = (0, 255, 255) # Cyan flash
                                width = 3
                            else:
                                wire_color = (255, 255, 0)
                                if current_mode == "PLAY":
                                    wire_color = (255, 200, 0)
                                width = 1

                            # Draw an anti-aliased logical line
                            if width == 1:
                                pygame.draw.aaline(screen, wire_color, start_pos, end_pos)
                            else:
                                pygame.draw.line(screen, wire_color, start_pos, end_pos, width)
                                
                            # Draw an arrowhead to indicate direction
                            direction = pymunk.Vec2d(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
                            if direction.length > 20:
                                direction = direction.normalized()
                                arrow_base = (end_pos[0] - int(direction.x * 15), end_pos[1] - int(direction.y * 15))
                                left_wing = (arrow_base[0] - int(direction.y * 5), arrow_base[1] + int(direction.x * 5))
                                right_wing = (arrow_base[0] + int(direction.y * 5), arrow_base[1] - int(direction.x * 5))
                                pygame.draw.polygon(screen, wire_color, [end_pos, left_wing, right_wing])

        # M17 Active Wiring preview line (with camera offset)
        if current_mode == "EDIT" and game_state["active_tool"] == "wire_tool" and game_state.get("wiring_source"):
            src = game_state["wiring_source"]
            if src.body:
                world_start_x, world_start_y = src.body.position.x, src.body.position.y
                screen_start = camera.world_to_screen(world_start_x, world_start_y)
                start_x, start_y = int(screen_start[0]), int(screen_start[1])
                pygame.draw.aaline(screen, (255, 150, 0), (start_x, start_y), m_pos)
            
        # Ghost Cursor Preview (with camera offset for placement)
        if current_mode == "EDIT" and not grabbed_body and game_state["active_tool"] is not None:
            # m_pos is in screen space, so no camera offset needed for drawing
            # But we need to show where it will actually be placed (handled in Phase 3)
            active_tool_key = game_state["active_tool"]
            preview_surf = create_icon_surface(active_tool_key, all_variants[active_tool_key])
            preview_surf.set_alpha(128) # semi-transparent
            preview_rect = preview_surf.get_rect(center=m_pos)
            screen.blit(preview_surf, preview_rect)

        # ───────────────────────────────────────────────────────────────
        # LAYER 3: UI Overlay (NO Camera Offset - Absolute Screen Coords)
        # ───────────────────────────────────────────────────────────────
        
        # Mode Indicator Border (drawn on playable rect, not affected by camera)
        border_color = env_manager.edit_mode_color if current_mode == "EDIT" else env_manager.play_mode_color
        pygame.draw.rect(screen, border_color, playable_rect, 5)

        # Phase 1, 3, 4: Draw UI Overlay
        ui_manager.draw(screen)
        
        # M25 Phase 6: Draw trash can if visible
        if trash_can_visible and current_mode == "EDIT":
            # Draw trash can background
            trash_bg_color = (150, 50, 50) if cursor_over_trash else (80, 80, 80)
            pygame.draw.rect(screen, trash_bg_color, trash_can_rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), trash_can_rect, 3, border_radius=10)
            
            # Draw trash can icon (simple representation)
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
