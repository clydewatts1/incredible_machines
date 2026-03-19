import pygame
import pymunk
import sys
import os
import math
import tkinter as tk
from tkinter import filedialog

import constants

# --- Register Collision Types Dynamically if missing ---
if not hasattr(constants, 'COLLISION_TYPE_WAREHOUSE'):
    constants.COLLISION_TYPE_WAREHOUSE = 10
if not hasattr(constants, 'COLLISION_TYPE_PORTAL'):
    constants.COLLISION_TYPE_PORTAL = 11

from entities.base import GamePart

# Ensure this matches your local engine import
try:
    from agent_engine import FactoryPart 
except ImportError:
    from entities.active import FactoryPart

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
from utils.ui_manager import UIManager, UIPanel, UIButton, UILabel, UIScrollPanel, UITextInput, UITextArea
from utils.level_manager import LevelManager
from utils.camera import Camera
from utils.physics_events import CollisionManager

UI_TOP_HEIGHT = 50
UI_BOTTOM_HEIGHT = 40
UI_SIDE_WIDTH = 260
UI_RIGHT_SIDE_WIDTH = 320

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

def set_mode(new_mode, state_dict):
    def callback():
        state_dict["mode"] = new_mode
    return callback

def set_active_tool(tool_key, state_dict):
    def callback():
        state_dict["active_tool"] = tool_key
    return callback

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
    global UI_TOP_HEIGHT, UI_BOTTOM_HEIGHT, UI_SIDE_WIDTH, UI_RIGHT_SIDE_WIDTH

    pygame.init()
    sound_manager.initialize()
    env_manager.initialize(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)

    window_width = env_manager.get_int("window_width", constants.WINDOW_WIDTH)
    window_height = env_manager.get_int("window_height", constants.WINDOW_HEIGHT)
    world_width = env_manager.get_int("world_width", constants.WORLD_WIDTH)
    world_height = env_manager.get_int("world_height", constants.WORLD_HEIGHT)

    UI_TOP_HEIGHT = env_manager.get_int("ui_top_height", UI_TOP_HEIGHT)
    UI_BOTTOM_HEIGHT = env_manager.get_int("ui_bottom_height", UI_BOTTOM_HEIGHT)
    UI_SIDE_WIDTH = env_manager.get_int("ui_left_panel_width", UI_SIDE_WIDTH)
    UI_RIGHT_SIDE_WIDTH = env_manager.get_int("ui_right_panel_width", UI_RIGHT_SIDE_WIDTH)
    
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
    
    screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE | pygame.SCALED)
    pygame.display.set_caption("The Incredible Machine Clone - Milestone 24")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 16)

    ui_manager = UIManager()
    
    w, h = window_width, window_height
    
    top_panel = UIPanel(pygame.Rect(0, 0, w, UI_TOP_HEIGHT), color=(50, 50, 50))
    bottom_panel = UIPanel(pygame.Rect(0, h - UI_BOTTOM_HEIGHT, w, UI_BOTTOM_HEIGHT), color=(50, 50, 50))
    left_panel = UIPanel(pygame.Rect(0, UI_TOP_HEIGHT, UI_SIDE_WIDTH, h - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT), color=(40, 40, 40))
    right_panel = UIPanel(pygame.Rect(w - UI_RIGHT_SIDE_WIDTH, UI_TOP_HEIGHT, UI_RIGHT_SIDE_WIDTH, h - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT), color=(40, 40, 40))

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
        "show_traces": False,
        "selected_instance": None,
        "selected_category": "all",
        "wiring_source": None,
        "belt_source": None,
        "pipe_source": None,  # ADD STATE FOR PIPE DRAWING
    }

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

    left_scroll_rect = pygame.Rect(
        left_panel.rect.x + 10,
        left_panel.rect.y + 40,
        left_panel.rect.width - 20,
        left_panel.rect.height - 50,
    )
    left_scroll_panel = UIScrollPanel(left_scroll_rect, color=(45, 45, 45), alpha=220)
    ui_manager.add_element(left_scroll_panel)

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
        # Increased padding slightly to ensure labels like "Trace: OFF" fit perfectly
        btn_w = max(86, font.size(text)[0] + 24)
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

    level_manager = LevelManager()
    
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
        build_top_panel()

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
            build_top_panel()

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
        build_top_panel()

    def handle_pause():
        if game_state["mode"] == "PLAY":
            game_state["mode"] = "PAUSE"
        elif game_state["mode"] == "PAUSE":
            game_state["mode"] = "PLAY"
        build_top_panel()

    def handle_edit():
        game_state["mode"] = "EDIT"
        build_top_panel()
        
    def handle_quit():
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def toggle_snap_to_grid():
        game_state["snap_to_grid"] = not game_state.get("snap_to_grid", False)
        build_top_panel()

    def toggle_traces():
        game_state["show_traces"] = not game_state.get("show_traces", False)
        build_top_panel()

    def build_top_panel():
        clear_top_bar()

        snap_enabled = game_state.get("snap_to_grid", False)
        snap_label = "Snap: ON" if snap_enabled else "Snap: OFF"
        pause_label = "Resume" if game_state.get("mode") == "PAUSE" else "Pause"
        trace_label = "Trace: ON" if game_state.get("show_traces", False) else "Trace: OFF"

        # Left-aligned cluster: modes and toggles.
        left_x = 10
        for text, callback in [
            ("Play", handle_play),
            (pause_label, handle_pause),
            ("Edit", handle_edit),
            ("Clear", handle_clear),
            (snap_label, toggle_snap_to_grid),
            (trace_label, toggle_traces), 
        ]:
            left_x += add_top_btn_at(left_x, text, callback) + 8

        # Right-aligned cluster: file ops and meta
        right_buttons = [
            ("Q.Save", handle_quick_save),
            ("Q.Load", handle_quick_load),
            ("Save", handle_save),
            ("Load", handle_load),
            ("Challenges", dummy_action("Challenges")),
            ("Help", dummy_action("Help")),
            ("Quit", handle_quit),
        ]
        right_gap = 8
        right_width = sum(max(86, font.size(t)[0] + 24) for t, _ in right_buttons) + right_gap * (len(right_buttons) - 1)
        right_x = w - right_width - 10
        
        for text, callback in right_buttons:
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

        left_scroll_panel.clear_children()

        selected = game_state.get("selected_instance")
        x = left_panel.rect.x + 10
        y = left_panel.rect.y + 10
        width = left_panel.rect.width - 20

        title = UILabel(pygame.Rect(x, y, width, 24), text="Inspector", font=font)
        ui_manager.add_element(title)
        left_panel_elements.append(title)
        y += 30

        if selected is None:
            hint = UILabel(
                pygame.Rect(left_scroll_panel.rect.x + 4, left_scroll_panel.rect.y + 8, left_scroll_panel.rect.width - 8, 24),
                text="Select an object",
                font=small_font,
            )
            left_scroll_panel.add_child(hint)
            left_scroll_panel.content_height = 40
            return

        inputs = {}
        content_x = left_scroll_panel.rect.x + 4
        content_y = left_scroll_panel.rect.y + 8
        content_width = left_scroll_panel.rect.width - 8
        all_keys = set(selected.properties.keys()).union(selected.overrides.keys())
        
        if hasattr(selected, 'payload') and 'payload' not in all_keys:
            all_keys.add('payload')
            
        for key in sorted(list(all_keys)):
            if key in ["visual", "template", "texture_path", "image", "label"]:
                continue

            key_label = UILabel(pygame.Rect(content_x, content_y, content_width, 16), text=key, font=small_font)
            left_scroll_panel.add_child(key_label)
            content_y += 18

            if key == 'payload' and not (key in selected.properties or key in selected.overrides):
                val_str = str(getattr(selected, 'payload', ''))
            else:
                val_str = str(selected.get_property(key))

            if len(val_str) > 28 or "\n" in val_str:
                field = UITextArea(pygame.Rect(content_x, content_y, content_width, 54), font=small_font, text=val_str)
                content_y += 58
            else:
                field = UITextInput(pygame.Rect(content_x, content_y, content_width, 22), font=small_font, text=val_str)
                content_y += 28
            left_scroll_panel.add_child(field)
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
            
            if 'payload' in new_dict:
                selected.payload = new_dict['payload']
                
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

        content_y += 4
        for text, callback in [("Save", apply_props), ("Reset", reset_props), ("Cancel", cancel_props)]:
            btn = UIButton(
                pygame.Rect(content_x, content_y, content_width, 26),
                text=text,
                font=small_font,
                callback=callback,
            )
            left_scroll_panel.add_child(btn)
            content_y += 30

        left_scroll_panel.content_height = (content_y - left_scroll_panel.rect.y) + 8
        left_scroll_panel._clamp_scroll()

    build_top_panel()
    build_category_tabs()
    build_right_palette()
    build_left_inspector()
        
    ui_manager.add_element(UILabel(pygame.Rect(10, h - UI_BOTTOM_HEIGHT + 5, 200, 30), text="Score: 0", font=font))
    ui_manager.add_element(UILabel(pygame.Rect(w - 210, h - UI_BOTTOM_HEIGHT + 5, 200, 30), text="Timer: 00:00", font=font))
    ui_manager.add_element(UIButton(pygame.Rect(w - 320, h - UI_BOTTOM_HEIGHT + 5, 100, 30), text="Options", font=font, callback=dummy_action("Options"), click_sound="clunk_bottom.wav"))
    
    space = pymunk.Space()
    space.gravity = constants.GRAVITY
    create_boundaries(space, playable_rect)
    
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
    game_state["wiring_source"] = None
    game_state["belt_source"] = None 
    game_state["pipe_source"] = None
    
    trash_can_visible = False
    trash_can_rect = pygame.Rect(w // 2 - 40, h - 100, 80, 80)
    cursor_over_trash = False
    
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
                
            if ui_manager.process_event(event):
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
                        build_left_inspector()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                camera.begin_pan(event.pos[0], event.pos[1])
                continue
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                camera.end_pan()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    world_click_pos = camera.screen_to_world(event.pos[0], event.pos[1])
                    
                    if playable_rect.collidepoint(event.pos) and current_mode == "EDIT":
                        info = space.point_query_nearest(world_click_pos, 5.0, pymunk.ShapeFilter())
                        if info and info.shape and info.shape.body != space.static_body:
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
                                        game_state["wiring_source"].connected_uuids.append(target_entity.uuid)
                                        target_entity.play_event_sound("spawn_sound")
                                        game_state["wiring_source"] = None

                            elif game_state["active_tool"] == "pipe_tool":
                                target_entity = None
                                for entity in entities:
                                    if info.shape in getattr(entity, 'shapes', [entity.shape]):
                                        target_entity = entity
                                        break
                                        
                                if target_entity:
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

                            elif game_state["active_tool"] == "belt_tool":
                                target_axle = None
                                for entity in entities:
                                    if info and info.shape in getattr(entity, 'shapes', [entity.shape]):
                                        if hasattr(entity, 'connect_belt'):
                                            target_axle = entity
                                            break
                                
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
                                grabbed_body = info.shape.body
                                trash_can_visible = True
                                
                                for entity in entities:
                                    if info.shape in getattr(entity, 'shapes', [entity.shape]):
                                        game_state["selected_instance"] = entity
                                        build_left_inspector()
                                        break
                                        
                        elif game_state["active_tool"] is not None and game_state["active_tool"] not in ("wire_tool", "belt_tool", "pipe_tool"):
                            variant_key = game_state["active_tool"]
                            spawn_x, spawn_y = world_click_pos
                            
                            if game_state.get("snap_to_grid", False):
                                spawn_x, spawn_y = snap_to_grid(spawn_x, spawn_y)
                            
                            new_part = create_part(space, spawn_x, spawn_y, variant_key)
                            entities.append(new_part)
                            active_instances[new_part.uuid] = new_part
                            new_part.play_event_sound("spawn_sound")
                        else:
                            game_state["wiring_source"] = None
                            game_state["belt_source"] = None
                            game_state["pipe_source"] = None
                            if game_state.get("selected_instance") is not None:
                                game_state["selected_instance"] = None
                                build_left_inspector()
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
        
        if not ui_manager.focused_element:
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
        pygame.draw.rect(screen, border_color, playable_rect, 5)

        ui_manager.draw(screen)
        
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