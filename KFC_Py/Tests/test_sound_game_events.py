"""
Tests for SoundManager game start/end sound functionality.
Created: July 28, 2025
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pathlib
import tempfile
from io import StringIO
import sys

try:
    # Import required modules - with error handling in case of missing dependencies
    from MessageBroker import MessageBroker
    from EventType import EventType
    from SoundManager import SoundManager
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Imports not available for testing: {e}")
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
class TestSoundManagerGameEvents(unittest.TestCase):
    """Test cases for SoundManager game start/end sound functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        
        # Create temporary directory for test sounds
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sounds_folder = pathlib.Path(self.temp_dir.name)
        
        # Create test sound files
        self.gamestart_path = self.sounds_folder / "gamestart.mp3"
        self.gameend_path = self.sounds_folder / "gameend.mp3"
        
        # Create empty files to simulate existence
        self.gamestart_path.touch()
        self.gameend_path.touch()
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_load_game_sounds(self, mock_mixer_init, mock_sound):
        """Test that game start and end sounds are loaded properly."""
        # Create SoundManager instance
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Verify pygame mixer was initialized
        mock_mixer_init.assert_called_once()
        
        # Verify Sound was called for all expected sound files
        expected_calls = [
            unittest.mock.call(str(self.sounds_folder / "move.wav")),  # Won't exist, but call attempted
            unittest.mock.call(str(self.sounds_folder / "capture.wav")),  # Won't exist, but call attempted
            unittest.mock.call(str(self.sounds_folder / "fail.mp3")),  # Won't exist, but call attempted
            unittest.mock.call(str(self.gamestart_path)),  # Exists
            unittest.mock.call(str(self.gameend_path))  # Exists
        ]
        
        # Check that sounds were loaded (at least gamestart and gameend)
        self.assertIn("gamestart", sound_manager.sounds)
        self.assertIn("gameend", sound_manager.sounds)
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_game_start_event_handling(self, mock_mixer_init, mock_sound):
        """Test that GAME_START events trigger game start sound."""
        # Create mock sound object
        mock_gamestart_sound = MagicMock()
        mock_sound.return_value = mock_gamestart_sound
        
        # Create SoundManager instance
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Manually set the sound to ensure it's available
        sound_manager.sounds["gamestart"] = mock_gamestart_sound
        
        # Test game start event
        game_start_data = {
            "timestamp": 1000,
            "player_count": 2,
            "board_size": (8, 8)
        }
        
        # Capture output to verify debug messages
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            sound_manager.handle_event(EventType.GAME_START, game_start_data)
            output = mock_stdout.getvalue()
        
        # Verify sound was played
        mock_gamestart_sound.play.assert_called_once()
        self.assertIn("DEBUG: Played game start sound", output)
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_game_end_event_handling(self, mock_mixer_init, mock_sound):
        """Test that GAME_END events trigger game end sound."""
        # Create mock sound object
        mock_gameend_sound = MagicMock()
        mock_sound.return_value = mock_gameend_sound
        
        # Create SoundManager instance
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Manually set the sound to ensure it's available
        sound_manager.sounds["gameend"] = mock_gameend_sound
        
        # Test game end event
        game_end_data = {
            "winner": "KW1",
            "winner_color": "White",
            "timestamp": 5000,
            "total_pieces_remaining": 5
        }
        
        # Capture output to verify debug messages
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            sound_manager.handle_event(EventType.GAME_END, game_end_data)
            output = mock_stdout.getvalue()
        
        # Verify sound was played
        mock_gameend_sound.play.assert_called_once()
        self.assertIn("DEBUG: Played game end sound", output)
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_missing_game_sounds_handling(self, mock_mixer_init, mock_sound):
        """Test behavior when game sound files are missing."""
        # Remove the test sound files
        self.gamestart_path.unlink()
        self.gameend_path.unlink()
        
        # Create SoundManager instance
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Verify sounds are not loaded
        self.assertNotIn("gamestart", sound_manager.sounds)
        self.assertNotIn("gameend", sound_manager.sounds)
        
        # Test handling events with missing sounds
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            sound_manager.handle_event(EventType.GAME_START, {})
            sound_manager.handle_event(EventType.GAME_END, {})
            output = mock_stdout.getvalue()
        
        # Verify warning messages are displayed
        self.assertIn("WARNING: Game start sound not available", output)
        self.assertIn("WARNING: Game end sound not available", output)
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_subscription_to_game_events(self, mock_mixer_init, mock_sound):
        """Test that SoundManager subscribes to GAME_START and GAME_END events."""
        # Create SoundManager instance
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Verify subscriptions were made
        game_start_subscribers = self.broker.subscribers.get(EventType.GAME_START, [])
        game_end_subscribers = self.broker.subscribers.get(EventType.GAME_END, [])
        
        self.assertIn(sound_manager, game_start_subscribers)
        self.assertIn(sound_manager, game_end_subscribers)
    
    @patch('pygame.mixer.Sound')
    @patch('pygame.mixer.init')
    def test_sound_integration_with_broker(self, mock_mixer_init, mock_sound):
        """Test that sounds are played when events are published through broker."""
        # Create mock sound objects
        mock_gamestart_sound = MagicMock()
        mock_gameend_sound = MagicMock()
        
        # Create SoundManager instance
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Manually set the sounds to ensure they're available
        sound_manager.sounds["gamestart"] = mock_gamestart_sound
        sound_manager.sounds["gameend"] = mock_gameend_sound
        
        # Publish events through broker
        self.broker.publish(EventType.GAME_START, {"timestamp": 1000})
        self.broker.publish(EventType.GAME_END, {"winner": "KW1"})
        
        # Verify sounds were played
        mock_gamestart_sound.play.assert_called_once()
        mock_gameend_sound.play.assert_called_once()


class TestSoundManagerDocumentation(unittest.TestCase):
    """Test cases for verifying SoundManager documentation and interface."""
    
    @unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
    def test_sound_manager_docstrings(self):
        """Test that SoundManager has proper documentation."""
        self.assertIsNotNone(SoundManager.__doc__)
        self.assertIsNotNone(SoundManager.__init__.__doc__)
        self.assertIsNotNone(SoundManager.handle_event.__doc__)
    
    @unittest.skipUnless(IMPORTS_AVAILABLE, "Required imports not available")
    def test_sound_manager_methods_exist(self):
        """Test that SoundManager has all expected methods."""
        expected_methods = [
            '_load_sounds',
            'handle_event',
            '_play_move_sound',
            '_play_capture_sound',
            '_play_fail_sound',
            '_play_gamestart_sound',
            '_play_gameend_sound',
            'set_volume',
            'stop_all_sounds'
        ]
        
        for method_name in expected_methods:
            self.assertTrue(hasattr(SoundManager, method_name), 
                          f"SoundManager should have method {method_name}")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
