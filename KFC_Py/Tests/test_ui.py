"""
Test script for the GameUI functionality
This script tests the GameUI components without opening interactive windows
"""

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent))

import numpy as np
from GameUI import GameUI
from Board import Board
from MessageBroker import MessageBroker
from PlayerNamesManager import PlayerNamesManager
from img import Img

def test_ui_creation():
    """Test that GameUI can be created without errors."""
    print("Testing GameUI creation...")
    
    # Create MessageBroker for UI
    broker = MessageBroker()
    
    # Create PlayerNamesManager with mock names
    player_names_manager = PlayerNamesManager()
    player_names_manager.set_mock_names_for_testing("TestWhite", "TestBlack")
    
    # Create UI with sample data
    pieces_path = pathlib.Path("../pieces")
    ui = GameUI(None, pieces_path, broker, player_names_manager)
    
    print("✓ GameUI created successfully!")
    return ui

def test_ui_components():
    """Test GameUI components without opening windows."""
    print("Testing GameUI components...")
    
    # Create a dummy game board for testing
    dummy_img = Img()
    dummy_img.img = np.zeros((512, 512, 3), dtype=np.uint8)
    dummy_board = Board(64, 64, 8, 8, dummy_img)
    
    # Create UI
    ui = test_ui_creation()
    
    # Test that UI can render without opening window
    try:
        ui.simulate_sample_data()
        ui.render_complete_ui(dummy_board)
        print("✓ UI components rendered successfully!")
        
        # Test player names
        white_name = ui.player_names_manager.get_white_player_name()
        black_name = ui.player_names_manager.get_black_player_name()
        print(f"✓ Player names: {white_name} vs {black_name}")
        
    except Exception as e:
        print(f"✗ Error testing UI components: {e}")
        raise

def test_ui_mock_functionality():
    """Test UI functionality with mock data."""
    print("Testing UI functionality with mock data...")
    
    ui = test_ui_creation()
    
    # Test various UI methods that don't require windows
    try:
        # Test background loading
        background_loaded = ui.background_img is not None
        print(f"✓ Background image loaded: {background_loaded}")
        
        # Test player names functionality
        assert ui.player_names_manager.get_white_player_name() == "TestWhite"
        assert ui.player_names_manager.get_black_player_name() == "TestBlack"
        print("✓ Player names functionality working")
        
        print("✓ All UI functionality tests passed!")
        
    except Exception as e:
        print(f"✗ Error in UI functionality test: {e}")
        raise

if __name__ == "__main__":
    print("Running GameUI tests (no interactive windows)...")
    print("=" * 50)
    
    try:
        test_ui_creation()
        test_ui_components()
        test_ui_mock_functionality()
        
        print("=" * 50)
        print("✓ All GameUI tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n✗ Tests interrupted by user")
    except Exception as e:
        print(f"✗ Tests failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure any opencv windows are closed
        try:
            import cv2
            cv2.destroyAllWindows()
        except:
            pass
