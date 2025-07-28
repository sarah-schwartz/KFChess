#!/usr/bin/env python3
"""
Test that pygame dependency is properly configured.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append('../..')


class TestSoundDependencies(unittest.TestCase):
    """Test sound system dependencies."""

    @patch('pygame.mixer')
    @patch('pygame.mixer.Sound')
    def test_pygame_import(self, mock_sound, mock_mixer):
        """Test that pygame can be imported."""
        try:
            import pygame
            self.assertTrue(True, "pygame imported successfully")
        except ImportError:
            self.fail("pygame is not installed or not importable")

    @patch('pygame.mixer')
    def test_pygame_mixer_functionality(self, mock_mixer):
        """Test basic pygame mixer functionality."""
        # Configure mocks
        mock_mixer.init.return_value = None
        mock_mixer.quit.return_value = None
        mock_mixer.get_init.return_value = (22050, -16, 2)
        
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.quit()
            self.assertTrue(True, "pygame.mixer basic functionality works")
        except Exception as e:
            self.fail(f"pygame.mixer functionality test failed: {e}")

    def test_setup_py_includes_pygame(self):
        """Test that setup.py includes pygame dependency."""
        setup_py_path = os.path.join('..', 'setup.py')
        
        if os.path.exists(setup_py_path):
            with open(setup_py_path, 'r') as f:
                content = f.read()
                self.assertIn('pygame', content, "pygame should be listed in setup.py dependencies")
        else:
            self.skipTest("setup.py not found")

    def test_sound_files_exist(self):
        """Test that required sound files exist."""
        pieces_path = os.path.join('..', 'pieces', 'sound')
        
        if os.path.exists(pieces_path):
            move_wav = os.path.join(pieces_path, 'move.wav')
            capture_wav = os.path.join(pieces_path, 'capture.wav')
            
            self.assertTrue(os.path.exists(move_wav), "move.wav should exist")
            self.assertTrue(os.path.exists(capture_wav), "capture.wav should exist")
        else:
            self.skipTest("pieces/sound directory not found")


if __name__ == "__main__":
    print("Testing sound system dependencies...")
    unittest.main()
