"""
Test script for the GameUI functionality
This script demonstrates the enhanced UI with background image and player information
"""

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent))

from GameUI import test_ui_display

if __name__ == "__main__":
    print("Testing GameUI with background and player information...")
    print("Press ESC to exit the UI test")
    
    try:
        test_ui_display()
    except KeyboardInterrupt:
        print("\nUI test completed successfully!")
    except Exception as e:
        print(f"Error during UI test: {e}")
    finally:
        import cv2
        cv2.destroyAllWindows()
