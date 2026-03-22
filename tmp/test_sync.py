import sys
import os
import pygame
import pymunk

# Mock necessary components
sys.path.append(os.path.abspath("."))
from utils.editor_ui import EditorUI
from entities.base import GamePart
from utils.level_manager import LevelManager

def test_sync():
    pygame.init()
    # Set a tiny display mode to satisfy pygame_gui requirements
    pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    # Mock game_state with Old values
    game_state = {
        "flow_name": "Old", 
        "flow_description": "Old", 
        "selected_instance": "GLOBAL_FLOW",
        "selected_category": "all"
    }
    
    # Initialize EditorUI (Mocking the required dictionaries)
    ui_settings = {
        "ui_top_height": 50,
        "ui_bottom_height": 50,
        "ui_left_panel_width": 200,
        "ui_right_panel_width": 200
    }
    
    # We need a dummy callbacks dict
    callbacks = {
        "save": lambda: None,
        "load": lambda: None,
        "clear": lambda: None,
        "play": lambda: None,
        "pause": lambda: None,
        "edit": lambda: None,
        "snap": lambda: None,
        "flow_settings": lambda: None
    }
    
    ui = EditorUI(800, 600, ui_settings, {}, [], game_state, callbacks)
    
    # Build the inspector (this populates ui.flow_inputs)
    ui._build_flow_inspector()
    
    print(f"Initial Name in field: {ui.flow_inputs['name'].get_text()}")
    
    # Simulate user typing new values in UI fields
    ui.flow_inputs["name"].set_text("New Name")
    ui.flow_inputs["description"].set_text("New Desc")
    
    # PRE-SYNC: Verify game_state still has OLD values
    print(f"Pre-Sync GameState: {game_state['flow_name']}, {game_state['flow_description']}")
    assert game_state["flow_name"] == "Old"
    
    # Trigger sync (which handle_save/handle_quick_save now does)
    ui.sync_ui_to_state()
    
    # POST-SYNC: Verify game_state has NEW values
    print(f"Post-Sync GameState: {game_state['flow_name']}, {game_state['flow_description']}")
    assert game_state["flow_name"] == "New Name"
    assert game_state["flow_description"] == "New Desc"
    
    print("SUCCESS: sync_ui_to_state successfully committed UI inputs to game_state!")

if __name__ == "__main__":
    try:
        test_sync()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        pygame.quit()
