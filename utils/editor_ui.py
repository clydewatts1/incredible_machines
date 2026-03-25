import pygame
import os
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel, UILabel, UIScrollingContainer, UITextEntryLine, UITextBox, UIDropDownMenu, UITextEntryBox, UIImage, UIHorizontalScrollBar, UIVerticalScrollBar
from utils.asset_manager import asset_manager
from utils.sound_manager import sound_manager

# Milestone 42 Safeguard: In some versions of pygame_gui (e.g. 0.6.14), 
# these constants are missing from the module root.
if not hasattr(pygame_gui, "UI_HORIZONTAL_SCROLLBAR_CHANGED"):
    pygame_gui.UI_HORIZONTAL_SCROLLBAR_CHANGED = pygame.USEREVENT + 1000
if not hasattr(pygame_gui, "UI_VERTICAL_SCROLLBAR_CHANGED"):
    pygame_gui.UI_VERTICAL_SCROLLBAR_CHANGED = pygame.USEREVENT + 1001

def create_icon_surface(variant_key, variant_data):
    """
    Generates a 40x40 icon for the palette.
    If a texture_path exists, it uses a thumbnail of that sprite.
    Otherwise, it draws a primitive shape with a text label.
    """
    label = variant_data.get("label", variant_key[:2].upper())
    tex_path = variant_data.get("texture_path")
    if not tex_path:
        icon_path = f"assets/icons/{variant_key}_button.png"
    else:
        icon_path = tex_path
    
    # Check if we should draw a primitive fallback
    if variant_data.get("template") == "Circle" and not os.path.exists(icon_path):
        return asset_manager.get_image(icon_path, fallback_size=(40, 40), text_label="⚙")
    
    return asset_manager.get_image(icon_path, fallback_size=(40, 40), text_label=label)

THEME_DATA = {
    "defaults": {
        "colours": {
            "normal_bg": "#E0E0E0",
            "normal_text": "#000000",
            "normal_border": "#000000",
            "hovered_bg": "#00FFFF",
            "selected_bg": "#00FFFF"
        },
        "font": { "name": "arial", "size": 14 }
    },
    "panel": {
        "colours": {
            "normal_bg": "#E0E0E0",
            "normal_border": "#000000"
        }
    },
    "scrolling_container": {
        "colours": {
            "normal_bg": "#E0E0E0",
            "container_bg": "#E0E0E0",
            "normal_border": "#000000"
        }
    },
    "label": {
        "colours": { "normal_text": "#000000" }
    },
    "button": {
        "colours": {
            "normal_bg": "#A0A0A0",
            "hovered_bg": "#00FFFF",
            "normal_text": "#000000",
            "normal_border": "#000000"
        }
    },
    "text_entry_line": {
        "colours": { "normal_bg": "#FFFFFF", "normal_text": "#000000", "normal_border": "#000000" }
    },
    "text_entry_box": {
        "colours": { "normal_bg": "#FFFFFF", "normal_text": "#000000", "normal_border": "#000000" }
    },
    "#top_bar": {
        "colours": { "normal_bg": "#E0E0E0", "normal_border": "#000000" }
    },
    "#side_panel": {
        "colours": { "normal_bg": "#E0E0E0", "normal_border": "#000000" }
    },
    "#side_panel_scroller": {
        "colours": { "normal_bg": "#E0E0E0", "container_bg": "#E0E0E0" }
    },
    "#transport_btn": {
        "font": { "name": "segoeuisymbol", "size": 18 }
    }
}

class EditorUI:
    def __init__(self, window_width, window_height, env_settings, all_variants, categories, game_state, callbacks):
        self.window_size = (window_width, window_height)
        self.w, self.h = self.window_size
        self.env_settings = env_settings
        self.all_variants = all_variants
        self.categories = categories
        self.game_state = game_state
        self.callbacks = callbacks
        self.dirty_callback = callbacks.get("dirty_callback")

        # Initialize pygame-gui UIManager with the correct theme file
        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "theme.json")
        self.ui_manager = pygame_gui.UIManager(self.window_size, theme_path)
        
        # UI Dimensions
        self.top_h = env_settings["ui_top_height"]
        self.bot_h = env_settings["ui_bottom_height"]
        self.side_w = env_settings["ui_left_panel_width"]
        self.right_w = env_settings["ui_right_panel_width"]
        
        # Core Panels
        self.top_panel = UIPanel(
            relative_rect=pygame.Rect(0, 0, self.w, self.top_h),
            manager=self.ui_manager,
            object_id="#top_bar"
        )
        self.bottom_panel = UIPanel(
            relative_rect=pygame.Rect(0, self.h - self.bot_h, self.w, self.bot_h),
            manager=self.ui_manager,
            object_id="#top_bar"
        )
        self.left_panel = UIPanel(
            relative_rect=pygame.Rect(0, self.top_h, self.side_w, self.h - self.top_h - self.bot_h),
            manager=self.ui_manager,
            object_id="#side_panel"
        )
        self.right_panel = UIPanel(
            relative_rect=pygame.Rect(self.w - self.right_w, self.top_h, self.right_w, self.h - self.top_h - self.bot_h),
            manager=self.ui_manager,
            object_id="#side_panel"
        )
        
        self.playable_rect = pygame.Rect(
            self.side_w, self.top_h, 
            self.w - self.side_w - self.right_w, 
            self.h - self.top_h - self.bot_h
        )
        
        # Containers for scrolling content
        self.left_container = UIScrollingContainer(
            relative_rect=pygame.Rect(10, 40, self.side_w - 20, self.left_panel.relative_rect.height - 50),
            manager=self.ui_manager,
            container=self.left_panel,
            object_id="#side_panel_scroller"
        )
        self.right_container = UIScrollingContainer(
            relative_rect=pygame.Rect(10, 80, self.right_w - 20, self.right_panel.relative_rect.height - 90),
            manager=self.ui_manager,
            container=self.right_panel,
            object_id="#right_panel_scroller"
        )
        
        # Milestone 42: Window Scrollbars
        # Horizontal scrollbar at bottom of playable area
        sb_h = 16
        # World limits (from constants or camera)
        from constants import WORLD_WIDTH, WORLD_HEIGHT
        vis_pct_h = self.playable_rect.width / WORLD_WIDTH
        vis_pct_v = self.playable_rect.height / WORLD_HEIGHT

        self.h_scrollbar = UIHorizontalScrollBar(
            relative_rect=pygame.Rect(self.side_w, self.h - self.bot_h - sb_h, self.playable_rect.width - sb_h, sb_h),
            manager=self.ui_manager,
            visible_percentage=vis_pct_h
        )
        # Vertical scrollbar at right of playable area
        self.v_scrollbar = UIVerticalScrollBar(
            relative_rect=pygame.Rect(self.w - self.right_w - sb_h, self.top_h, sb_h, self.playable_rect.height),
            manager=self.ui_manager,
            visible_percentage=vis_pct_v
        )
        
        # Bottom Bar Labels
        self.score_label = UILabel(
            relative_rect=pygame.Rect(10, 5, 200, 30),
            text="Score: 0",
            manager=self.ui_manager,
            container=self.bottom_panel
        )
        self.timer_label = UILabel(
            relative_rect=pygame.Rect(self.w - 210, 5, 200, 30),
            text="Timer: 00:00",
            manager=self.ui_manager,
            container=self.bottom_panel
        )
        self.options_btn = UIButton(
            relative_rect=pygame.Rect(self.w - 320, 5, 100, 30),
            text="Options",
            manager=self.ui_manager,
            container=self.bottom_panel
        )

        # Tracking for elements that need cleanup
        self.top_elements = []
        self.category_tabs = []
        self.inspector_elements = []
        self.palette_elements = []
        self.inspector_inputs = {}
        self.flow_inputs = {}

    def rebuild_top_panel(self):
        """Builds the professional menu bar with transport and file ops."""
        for el in self.top_elements:
            el.kill()
        self.top_elements.clear()

        # 1. FILE ACTIONS (Left Cluster)
        file_actions = [
            ("SAVE", self.callbacks["save"]),
            ("LOAD", self.callbacks["load"]),
            ("NEW", self.callbacks["new"])
        ]
        
        btn_x = 10
        for text, cb in file_actions:
            btn = UIButton(
                relative_rect=pygame.Rect(btn_x, 10, 80, 30),
                text=text,
                manager=self.ui_manager,
                container=self.top_panel,
                object_id="#file_action_btn"
            )
            self.top_elements.append(btn)
            btn_x += 85
            # Store callback for handling in process_events
            btn.user_data = text

        # 2. TRANSPORT CONTROLS (Center Cluster)
        # We calculate the center based on the top panel width
        center_x = self.w // 2
        cluster_width = 240
        start_x = center_x - (cluster_width // 2)
        
        transport_btns = [
            ("<<", lambda: self._set_speed(0.5)),
            ("▶",  self.callbacks["play"]),
            ("⏸",  self.callbacks["pause"]),
            (">>", lambda: self._set_speed(4.0)), # Toggles speed in main.py logic based on game_state
            ("■",  self.callbacks["edit"])
        ]
        
        btn_x = start_x
        for text, cb in transport_btns:
            btn = UIButton(
                relative_rect=pygame.Rect(btn_x, 10, 40, 30),
                text=text,
                manager=self.ui_manager,
                container=self.top_panel,
                tool_tip_text=f"Transport: {text}",
                object_id="#transport_btn"
            )
            # We store callbacks in user_data or just handle them in process_event
            btn.user_data = cb
            self.top_elements.append(btn)
            btn_x += 45

        # 3. UTILITY GROUP (Right)
        right_x = self.w - 180
        snap_text = "Grid" # We'll use tooltips for status or toggling text
        grid_btn = UIButton(
            relative_rect=pygame.Rect(right_x, 10, 70, 30),
            text=snap_text,
            manager=self.ui_manager,
            container=self.top_panel,
            tool_tip_text="Toggle Snap Grid"
        )
        grid_btn.user_data = self.callbacks["snap"]
        self.top_elements.append(grid_btn)

        # Milestone 35: Record Test Button
        rec_color = "#FF0000" if self.game_state.get("record_mode") else "#A0A0A0"
        rec_text = "● REC" if not self.game_state.get("record_mode") else "■ STOP REC"
        rec_btn = UIButton(
            relative_rect=pygame.Rect(right_x - 110, 10, 100, 30),
            text=rec_text,
            manager=self.ui_manager,
            container=self.top_panel,
            tool_tip_text="Record Test Case (Snapshot I/O)"
        )
        rec_btn.user_data = "RECORD_TOGGLE"
        self.top_elements.append(rec_btn)
        
        flow_btn = UIButton(
            relative_rect=pygame.Rect(right_x + 75, 10, 50, 30),
            text="Flow",
            manager=self.ui_manager,
            container=self.top_panel,
            tool_tip_text="Model Metadata"
        )
        flow_btn.user_data = self.callbacks["flow_settings"]
        self.top_elements.append(flow_btn)

        reimage_btn = UIButton(
            relative_rect=pygame.Rect(right_x + 130, 10, 70, 30),
            text="REIMAGE",
            manager=self.ui_manager,
            container=self.top_panel,
            tool_tip_text="Regenerate all project assets"
        )
        reimage_btn.user_data = self.callbacks["reimage"]
        self.top_elements.append(reimage_btn)

    def set_score(self, score):
        self.score_label.set_text(f"Score: {score}")

    def set_timer(self, time_str):
        self.timer_label.set_text(f"Timer: {time_str}")

    def _set_speed(self, multiplier):
        self.game_state["speed_multiplier"] = multiplier
        sound_manager.play_sound("clunk_top.wav")

    def rebuild_category_tabs(self):
        """Builds standardized category tabs for the palette."""
        for el in self.category_tabs:
            el.kill()
        self.category_tabs.clear()

        selected = self.game_state.get("selected_category", "all")
        tab_entries = ["all"] + self.categories
        
        tab_x, tab_y = 10, 10
        tab_h = 24
        
        for cat in tab_entries:
            label = cat.title()
            tw = max(60, len(label) * 8 + 10) # Simple estimate or use font.size if needed
            
            if tab_x + tw > self.right_w - 20:
                tab_x = 10
                tab_y += tab_h + 4
            
            btn = UIButton(
                relative_rect=pygame.Rect(tab_x, tab_y, tw, tab_h),
                text=label,
                manager=self.ui_manager,
                container=self.right_panel,
                object_id="#selected_tab" if cat == selected else "#tab"
            )
            btn.user_data = cat # Category name
            self.category_tabs.append(btn)
            tab_x += tw + 4
        
        # Adjust container position
        new_top = tab_y + tab_h + 10
        self.right_container.set_relative_position((10, new_top))
        self.right_container.set_dimensions((self.right_w - 20, self.right_panel.relative_rect.height - new_top - 10))

    def rebuild_right_palette(self):
        """Builds the component palette as icon tiles inside bordered card panels."""
        for el in self.palette_elements:
            el.kill()
        self.palette_elements.clear()

        COLS = 3
        ICON_BTN_SIZE = 56   # Square button containing the icon
        LABEL_H = 20
        PAD = 4              # Inner padding inside the card
        CARD_H = PAD + ICON_BTN_SIZE + 2 + LABEL_H + PAD
        gx, gy = 6, 8
        container_w = self.right_container.relative_rect.width
        card_w = (container_w - (COLS + 1) * gx) // COLS

        selected = self.game_state.get("selected_category", "all")
        variants = [(k, v) for k, v in self.all_variants.items()
                    if selected == "all" or str(v.get("category", "other")).lower() == selected]

        for i, (vk, vd) in enumerate(variants):
            col, row = i % COLS, i // COLS
            cx = gx + col * (card_w + gx)
            cy = gy + row * (CARD_H + gy)

            label_text = vd.get("label", vk)
            desc = vd.get("description", "A factory component.")

            # --- Card panel (the border box) ---
            card = UIPanel(
                relative_rect=pygame.Rect(cx, cy, card_w, CARD_H),
                manager=self.ui_manager,
                container=self.right_container,
                object_id="#palette_card"
            )
            self.palette_elements.append(card)

            # Milestone fix: Decouple icon from button to prevent state-based disappearing
            btn_w = card_w - 2 * PAD
            icon_surf = create_icon_surface(vk, vd)
            if icon_surf:
                icon_scaled = pygame.transform.smoothscale(icon_surf, (40, 40))
                # Center the 40x40 icon inside the card's button area
                img_x = PAD + (btn_w - 40) // 2
                img_y = PAD + (ICON_BTN_SIZE - 40) // 2
                img = UIImage(
                    relative_rect=pygame.Rect(img_x, img_y, 40, 40),
                    image_surface=icon_scaled,
                    manager=self.ui_manager,
                    container=card,
                    object_id="#palette_icon"
                )
                self.palette_elements.append(img)

            # Interactive button sits on top, transparent but handling clicks/hover
            btn = UIButton(
                relative_rect=pygame.Rect(PAD, PAD, btn_w, ICON_BTN_SIZE),
                text="",
                manager=self.ui_manager,
                container=card,
                tool_tip_text=f"{label_text}: {desc}",
                object_id="#palette_btn"
            )
            btn.user_data = vk
            
            # Milestone fix: highlight the active tool
            if vk == self.game_state.get("active_tool"):
                btn.select()
                
            self.palette_elements.append(btn)

            # Label beneath the button inside the card
            short_label = label_text[:12] if len(label_text) <= 12 else label_text[:11] + "…"
            lbl = UILabel(
                relative_rect=pygame.Rect(PAD, PAD + ICON_BTN_SIZE + 2, btn_w, LABEL_H),
                text=short_label,
                manager=self.ui_manager,
                container=card,
                object_id="#palette_label"
            )
            self.palette_elements.append(lbl)

        rows = (len(variants) + COLS - 1) // COLS
        self.right_container.set_scrollable_area_dimensions(
            (container_w, rows * (CARD_H + gy) + gy)
        )

    def rebuild_left_inspector(self):
        """Generates dynamic input fields for the selected entity."""
        # Clear existing elements
        for el in self.inspector_elements:
            el.kill()
        self.inspector_elements.clear()
        self.inspector_inputs.clear()
        self.flow_inputs.clear()

        selected = self.game_state.get("selected_instance")
        
        # Inspector title
        title = UILabel(relative_rect=pygame.Rect(10, 10, self.side_w - 20, 24), text="Inspector", manager=self.ui_manager, container=self.left_panel)
        self.inspector_elements.append(title)

        if selected is None:
            lbl = UILabel(relative_rect=pygame.Rect(0, 0, self.side_w - 40, 30), text="Select an object", manager=self.ui_manager, container=self.left_container)
            self.inspector_elements.append(lbl)
            return

        if selected == "GLOBAL_FLOW":
            self._build_flow_inspector()
            return

        # Object Inspector
        y_off = 0
        instance_name = selected.overrides.get("custom_name", selected.get_property("label", selected.variant_key))
        lbl = UILabel(relative_rect=pygame.Rect(0, y_off, self.side_w - 40, 24), text=f"[{instance_name}]", manager=self.ui_manager, container=self.left_container)
        self.inspector_elements.append(lbl)
        y_off += 30

        reserved = ["custom_name", "custom_description"]
        all_keys = [k for k in selected.properties.keys() if k not in reserved and k not in ["template", "texture_path", "image", "label"]]
        for k in selected.overrides.keys():
            if k not in all_keys and k not in reserved: all_keys.append(k)
        
        ordered_keys = reserved + sorted(all_keys)
        self.inspector_inputs = {}

        for key in ordered_keys:
            lbl = UILabel(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 20), text=key, manager=self.ui_manager, container=self.left_container)
            self.inspector_elements.append(lbl)
            y_off += 22
            
            val = str(selected.get_property(key, ""))
            if key == "custom_description" or len(val) > 30:
                field = UITextEntryBox(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 60), manager=self.ui_manager, container=self.left_container, initial_text=val)
                y_off += 65
            else:
                field = UITextEntryLine(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 30), manager=self.ui_manager, container=self.left_container)
                field.set_text(val)
                y_off += 35
            
            self.inspector_inputs[key] = field
            self.inspector_elements.append(field)

        apply_btn = UIButton(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 30), text="Apply Changes", manager=self.ui_manager, container=self.left_container)
        apply_btn.user_data = "APPLY"
        self.inspector_elements.append(apply_btn)
        y_off += 40
        
        self.left_container.set_scrollable_area_dimensions((self.side_w - 20, y_off + 20))

    def _build_flow_inspector(self):
        y_off = 0
        lbl = UILabel(relative_rect=pygame.Rect(0, y_off, self.side_w - 40, 24), text="Flow Settings", manager=self.ui_manager, container=self.left_container)
        self.inspector_elements.append(lbl)
        y_off += 30
        
        lbl = UILabel(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 20), text="Flow Name", manager=self.ui_manager, container=self.left_container)
        self.inspector_elements.append(lbl)
        y_off += 22
        name_in = UITextEntryLine(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 30), manager=self.ui_manager, container=self.left_container)
        name_in.set_text(self.game_state.get("name", ""))
        self.inspector_elements.append(name_in)
        self.flow_inputs["name"] = name_in
        y_off += 35
        
        lbl = UILabel(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 20), text="Description", manager=self.ui_manager, container=self.left_container)
        self.inspector_elements.append(lbl)
        y_off += 22
        desc_in = UITextEntryBox(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 60), manager=self.ui_manager, container=self.left_container, initial_text=self.game_state.get("description", ""))
        self.inspector_elements.append(desc_in)
        self.flow_inputs["description"] = desc_in
        y_off += 65

        # Physics Settings
        physics_fields = [
            ("Gravity X", "gravity_x", self.game_state.get("gravity", [0, 900])[0]),
            ("Gravity Y", "gravity_y", self.game_state.get("gravity", [0, 900])[1]),
            ("Damping", "damping", self.game_state.get("damping", 0.99)),
            ("Wind X", "wind_x", self.game_state.get("wind", [0, 0])[0]),
            ("Wind Y", "wind_y", self.game_state.get("wind", [0, 0])[1])
        ]

        for label_text, key, val in physics_fields:
            lbl = UILabel(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 20), text=label_text, manager=self.ui_manager, container=self.left_container)
            self.inspector_elements.append(lbl)
            y_off += 22
            inp = UITextEntryLine(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 30), manager=self.ui_manager, container=self.left_container)
            inp.set_text(str(val))
            self.inspector_elements.append(inp)
            self.flow_inputs[key] = inp
            y_off += 35
        
        flow_save = UIButton(relative_rect=pygame.Rect(0, y_off, self.side_w - 50, 30), text="Save Flow Settings", manager=self.ui_manager, container=self.left_container)
        flow_save.user_data = "SAVE_FLOW_TRIGGER"
        self.inspector_elements.append(flow_save)
        
        self.left_container.set_scrollable_area_dimensions((self.side_w - 20, y_off + 50))

    def process_event(self, event):
        """Delegates events to pygame-gui and handles internal callbacks."""
        # DEBUG: If you see this, the latest file is being loaded.
        # print("DEBUG: EditorUI process_event running...")
        self.ui_manager.process_events(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, "user_data"):
                ud = event.ui_element.user_data
                if ud == "SAVE": self.callbacks["save"]()
                elif ud == "LOAD": self.callbacks["load"]()
                elif ud == "NEW": self.callbacks["new"]()
                elif ud == "RECORD_TOGGLE":
                    if "record_test" in self.callbacks:
                        self.callbacks["record_test"]()
                        self.rebuild_top_panel()
                elif callable(ud):
                    ud()
                elif ud == "APPLY":
                    self._apply_inspector_changes()
                elif ud == "SAVE_FLOW_TRIGGER":
                    name = self.flow_inputs["name"].get_text()
                    desc = self.flow_inputs["description"].get_text()
                    
                    # Parse physics values
                    try:
                        gx = float(self.flow_inputs["gravity_x"].get_text())
                        gy = float(self.flow_inputs["gravity_y"].get_text())
                        damp = float(self.flow_inputs["damping"].get_text())
                        wx = float(self.flow_inputs["wind_x"].get_text())
                        wy = float(self.flow_inputs["wind_y"].get_text())
                    except:
                        gx, gy, damp, wx, wy = 0, 900, 0.99, 0, 0

                    if "save_flow" in self.callbacks:
                        self.callbacks["save_flow"](name, desc, [gx, gy], damp, [wx, wy])
                    else:
                        self.game_state["flow_name"] = name
                        self.game_state["flow_description"] = desc
                        self.game_state["gravity"] = [gx, gy]
                        self.game_state["damping"] = damp
                        self.game_state["wind"] = [wx, wy]
                        self.game_state["selected_instance"] = None
                        self.rebuild_left_inspector()
                elif ud in self.all_variants:
                    self.game_state["active_tool"] = ud
                elif ud in ["all"] + self.categories:
                    self.game_state["selected_category"] = ud
                    self.rebuild_category_tabs()
                    self.rebuild_right_palette()
        
        return self.ui_manager.get_focus_set() is not None or self.ui_manager.get_hovering_any_element()

    def _update_camera_from_scrollbars(self):
        """Update camera offsets based on scrollbar positions."""
        # start_percentage in 0.6.14 is 0.0 to (1.0 - vis_pct)
        # We normalize this to 0.0 - 1.0 for the camera
        vis_h = self.h_scrollbar.visible_percentage
        fx = self.h_scrollbar.start_percentage / max(0.001, 1.0 - vis_h)
        
        vis_v = self.v_scrollbar.visible_percentage
        fy = self.v_scrollbar.start_percentage / max(0.001, 1.0 - vis_v)
        
        if "camera" in self.callbacks:
            cam = self.callbacks["camera"]()
            if cam:
                cam.set_offsets_from_fractions(fx, fy)

    def sync_scrollbars_to_camera(self, camera):
        """Update scrollbar knob positions to match current camera offset."""
        if not camera or not hasattr(self, 'h_scrollbar'):
            return
            
        fx, fy = camera.get_scroll_fractions()
        
        # Convert 0.0-1.0 fractions back to start_percentages (0.0 to 1.0-vis_pct)
        sp_h = fx * (1.0 - self.h_scrollbar.visible_percentage)
        sp_v = fy * (1.0 - self.v_scrollbar.visible_percentage)
        
        self.h_scrollbar.set_scroll_from_start_percentage(sp_h)
        self.v_scrollbar.set_scroll_from_start_percentage(sp_v)

    def sync_ui_to_state(self):
        """Commits pending UI entries to state before a global save."""
        selected = self.game_state.get("selected_instance")
        if selected == "GLOBAL_FLOW":
            if "name" in self.flow_inputs:
                self.game_state["name"] = self.flow_inputs["name"].get_text()
            if "description" in self.flow_inputs:
                self.game_state["description"] = self.flow_inputs["description"].get_text()
            
            # Sync physics values
            try:
                if "gravity_x" in self.flow_inputs:
                    gx = float(self.flow_inputs["gravity_x"].get_text())
                    gy = float(self.flow_inputs["gravity_y"].get_text())
                    self.game_state["gravity"] = [gx, gy]
                if "damping" in self.flow_inputs:
                    self.game_state["damping"] = float(self.flow_inputs["damping"].get_text())
                if "wind_x" in self.flow_inputs:
                    wx = float(self.flow_inputs["wind_x"].get_text())
                    wy = float(self.flow_inputs["wind_y"].get_text())
                    self.game_state["wind"] = [wx, wy]
            except:
                pass
        elif selected is not None:
            self._apply_inspector_changes(clear_selection=False)

    def _apply_inspector_changes(self, clear_selection=True):
        import ast
        selected = self.game_state["selected_instance"]
        if selected is None or selected == "GLOBAL_FLOW":
            return
            
        new_overrides = {}
        for k, field in self.inspector_inputs.items():
            if hasattr(field, 'get_text'):
                txt = field.get_text()
            else:
                continue
            
            try:
                if txt.startswith("[") or txt.startswith("{"): new_overrides[k] = ast.literal_eval(txt)
                elif "." in txt: new_overrides[k] = float(txt)
                else: new_overrides[k] = int(txt)
            except: new_overrides[k] = txt
            
        selected.apply_draft_overrides(new_overrides)
        if self.dirty_callback:
            self.dirty_callback()
            
        if clear_selection:
            self.game_state["selected_instance"] = None
            self.rebuild_left_inspector()

    def update(self, time_delta):
        self.ui_manager.update(time_delta)
        
        # Milestone 42 Fix: Polling for scrollbar movement
        # (Version 0.6.14 lacks UI_HORIZONTAL_SCROLLBAR_CHANGED event at module root)
        if hasattr(self, 'h_scrollbar') and hasattr(self, 'v_scrollbar'):
            if self.h_scrollbar.has_moved_recently or self.v_scrollbar.has_moved_recently:
                self._update_camera_from_scrollbars()

    def draw(self, surface):
        # Paint the left panel container background explicitly (UIScrollingContainer
        # renders on an internal surface that ignores theme colours).
        PANEL_BG = (224, 224, 224)  # #E0E0E0
        left_abs = pygame.Rect(
            self.left_panel.rect.x + 10,
            self.left_panel.rect.y + 40,
            self.side_w - 20,
            self.left_panel.rect.height - 50
        )
        pygame.draw.rect(surface, PANEL_BG, left_abs)
        right_abs = pygame.Rect(
            self.right_panel.rect.x + 10,
            self.right_panel.rect.y + 80,
            self.right_w - 20,
            self.right_panel.rect.height - 90
        )
        pygame.draw.rect(surface, PANEL_BG, right_abs)
        self.ui_manager.draw_ui(surface)