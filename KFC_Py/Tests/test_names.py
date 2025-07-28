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
    
    # Test the GUI
    print("Starting name input GUI...")
    white_name, black_name = manager.get_player_names_from_gui()
    print(f"Names entered: White='{white_name}', Black='{black_name}'")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()
