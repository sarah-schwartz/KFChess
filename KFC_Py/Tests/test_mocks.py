#!/usr/bin/env python3
"""
Global mocks for all tests to prevent GUI windows, sound playback, and user input.
Import this module in any test that might trigger interactive components.
"""

import sys
from unittest.mock import patch, MagicMock

# Global mock configuration to prevent GUI windows and sound playback
GLOBAL_MOCKS = {
    # Pygame mocks for sound system
    'pygame': MagicMock(),
    'pygame.mixer': MagicMock(),
    'pygame.mixer.Sound': MagicMock(),
    
    # OpenCV mocks for camera/video functionality
    'cv2': MagicMock(),
    
    # GUI framework mocks
    'tkinter': MagicMock(),
    'tkinter.messagebox': MagicMock(),
    'tkinter.simpledialog': MagicMock(),
}

def setup_global_mocks():
    """Setup global mocks to prevent GUI windows and sound playback."""
    for module_name, mock_obj in GLOBAL_MOCKS.items():
        sys.modules[module_name] = mock_obj

def mock_player_input():
    """Mock function to replace user input for player names."""
    return ('TestWhite', 'TestBlack')

def mock_user_input(prompt=""):
    """Mock function to replace input() calls."""
    return 'TestInput'

# Automatically setup mocks when this module is imported
setup_global_mocks()

# Patch common problematic functions
patch('builtins.input', side_effect=mock_user_input).start()

# Try to patch PlayerNamesManager if it exists
try:
    patch('PlayerNamesManager.PlayerNamesManager.get_player_names_from_gui', 
          return_value=mock_player_input()).start()
except (ImportError, ModuleNotFoundError):
    print("Note: PlayerNamesManager not found, skipping GUI mock")

print("🔇 Global test mocks activated - no GUI windows or sounds will be played")
