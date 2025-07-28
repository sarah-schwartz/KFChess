"""
Integration tests for game start and end sound functionality.
Tests the complete flow from game events to sound playback.
Created: July 28, 2025
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import pathlib
import tempfile
from io import StringIO
import sys
import time

try:
    # Import required modules - with error handling in case of missing dependencies
    from MessageBroker import MessageBroker
    from EventType import EventType
    from SoundManager import SoundManager
    from GameEventPublisher import GameEventPublisher
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Imports not available for testing: {e}")
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
class TestGameSoundIntegration(unittest.TestCase):
    """Integration tests for game start/end sound functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        self.event_publisher = GameEventPublisher(self.broker)
        
        # Create temporary directory for test sounds
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sounds_folder = pathlib.Path(self.temp_dir.name)
        
        # Create test sound files
        sound_files = ["gamestart.mp3", "gameend.mp3"]
        for sound_file in sound_files:
            (self.sounds_folder / sound_file).touch()
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_game_start_and_end_sounds(self, mock_mixer_init, mock_sound):
        """Test complete game flow: start event -> sound -> end event -> sound."""
        # Create mock sound objects
        mock_gamestart_sound = MagicMock()
        mock_gameend_sound = MagicMock()
        mock_other_sound = MagicMock()
        
        # Configure mock to return different sounds for different files
        def mock_sound_side_effect(path):
            if "gamestart" in str(path):
                return mock_gamestart_sound
            elif "gameend" in str(path):
                return mock_gameend_sound
            else:
                return mock_other_sound
        
        mock_sound.side_effect = mock_sound_side_effect
        
        # Create SoundManager instance
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Verify sounds were loaded correctly
        self.assertIn("gamestart", sound_manager.sounds)
        self.assertIn("gameend", sound_manager.sounds)
        
        # Test game events
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.event_publisher.send(EventType.GAME_START, {"timestamp": 1000})
            time.sleep(0.1)  # Small delay to ensure event processing
            self.event_publisher.send(EventType.GAME_END, {"winner": "KW1", "winner_color": "White"})
            time.sleep(0.1)  # Small delay to ensure event processing
            output = mock_stdout.getvalue()
        
        # Verify both sounds were played
        mock_gamestart_sound.play.assert_called_once()
        mock_gameend_sound.play.assert_called_once()
        
        # Verify debug messages
        self.assertIn("DEBUG: Played game start sound", output)
        self.assertIn("DEBUG: Played game end sound", output)
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_missing_sound_files_handled_gracefully(self, mock_mixer_init, mock_sound):
        """Test behavior when sound files are missing."""
        # Remove sound files to simulate missing files
        for sound_file in self.sounds_folder.glob("*.mp3"):
            sound_file.unlink()
        
        # Create SoundManager with missing files
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Verify missing sound keys are not in the sounds dictionary
        self.assertNotIn("gamestart", sound_manager.sounds)
        self.assertNotIn("gameend", sound_manager.sounds)
        
        # Test events with missing sounds - should not crash
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.event_publisher.send(EventType.GAME_START, {"timestamp": 0})
            time.sleep(0.1)  # Small delay to ensure event processing
            self.event_publisher.send(EventType.GAME_END, {"winner": "KW1"})
            time.sleep(0.1)  # Small delay to ensure event processing
            output = mock_stdout.getvalue()
        
        # Verify warning messages appear
        self.assertIn("WARNING: Game start sound not available", output)
        self.assertIn("WARNING: Game end sound not available", output)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
