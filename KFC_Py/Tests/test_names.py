#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

try:
    from PlayerNamesManager import PlayerNamesManager
    
    print("Testing PlayerNamesManager...")
    manager = PlayerNamesManager()
    print("PlayerNamesManager created successfully!")
    
    print("Background image loaded:", manager.background_img is not None)
    
    # Test with mock names (no GUI required for testing)
    print("Testing with mock names...")
    manager.set_mock_names_for_testing("TestWhite", "TestBlack")
    white_name = manager.get_white_player_name()
    black_name = manager.get_black_player_name()
    print(f"Mock names set: White='{white_name}', Black='{black_name}'")
    
    # Test setting custom names
    manager.set_player_names("CustomWhite", "CustomBlack")
    print(f"Custom names set: White='{manager.get_white_player_name()}', Black='{manager.get_black_player_name()}'")
    
    # Test name by color
    print(f"White player by color: {manager.get_player_name_by_color('W')}")
    print(f"Black player by color: {manager.get_player_name_by_color('B')}")
    
    print("All tests passed!")

except Exception as e:
    import traceback
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()
