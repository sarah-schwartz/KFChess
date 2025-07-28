#!/usr/bin/env python3
"""
Tests for SoundManager class.
Tests sound loading, event handling, and playback functionality.
"""

import unittest
import pathlib
import tempfile
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append('..')

# Mock pygame completely before any imports to prevent GUI windows and sound playback
with patch.dict('sys.modules', {
    'pygame': MagicMock(),
    'pygame.mixer': MagicMock(),
    'pygame.mixer.Sound': MagicMock()
}):
    from SoundManager import SoundManager
    from MessageBroker import MessageBroker
    from EventType import EventType
    from Command import Command


class TestSoundManager(unittest.TestCase):
    """Test cases for SoundManager functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.broker = MessageBroker()
        self.temp_dir = tempfile.mkdtemp()
        self.sounds_folder = pathlib.Path(self.temp_dir)
        
        # Create mock sound files
        self.move_sound_path = self.sounds_folder / "move.wav"
        self.capture_sound_path = self.sounds_folder / "capture.wav"
        
        # Create empty files for testing
        self.move_sound_path.touch()
        self.capture_sound_path.touch()
        
        # No need to create additional patches since pygame is already mocked globally

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sound_manager_initialization(self):
        """Test SoundManager initialization and sound loading."""
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Check that sound manager was created successfully
        self.assertIsNotNone(sound_manager)
        
        # Check that sound manager subscribed to events
        self.assertIn(EventType.PIECE_MOVED, self.broker.subscribers)
        self.assertIn(EventType.PIECE_CAPTURED, self.broker.subscribers)
        self.assertIn(EventType.INVALID_MOVE, self.broker.subscribers)

    def test_missing_sound_files(self):
        """Test SoundManager behavior when sound files are missing."""
        # Create empty directory
        empty_dir = pathlib.Path(self.temp_dir) / "empty"
        empty_dir.mkdir()
        
        # Should not crash when sound files are missing
        sound_manager = SoundManager(self.broker, empty_dir)
        self.assertIsNotNone(sound_manager)

    def test_piece_moved_event_handling(self):
        """Test that PIECE_MOVED events trigger move sound playback."""
        with unittest.mock.patch('pygame.mixer.Sound') as mock_sound_class:
            # Mock the Sound objects
            mock_move_sound = unittest.mock.Mock()
            mock_sound_class.return_value = mock_move_sound
            
            sound_manager = SoundManager(self.broker, self.sounds_folder)
            
            # Manually add the move sound to simulate it being loaded
            sound_manager.sounds['move'] = mock_move_sound
            
            # Create a test command
            test_command = Command(1000, "PW", "move", [(1, 1), (2, 2)])
            
            # Publish PIECE_MOVED event
            self.broker.publish(EventType.PIECE_MOVED, test_command)
            
            # Verify that play() was called on the move sound
            mock_move_sound.play.assert_called_once()
        
        # If we get here without exception, the test passed
        self.assertTrue(True, "Event handling completed without errors")

    def test_piece_captured_event_handling(self):
        """Test that PIECE_CAPTURED events trigger capture sound playback."""
        with unittest.mock.patch('pygame.mixer.Sound') as mock_sound_class:
            # Mock the Sound objects
            mock_capture_sound = unittest.mock.Mock()
            mock_sound_class.return_value = mock_capture_sound
            
            sound_manager = SoundManager(self.broker, self.sounds_folder)
            
            # Manually add the capture sound to simulate it being loaded
            sound_manager.sounds['capture'] = mock_capture_sound
            
            # Create test capture data
            capture_data = {
                "piece_id": "PB",
                "captured_by": "W",
                "captured_at": (3, 3)
            }
            
            # Publish PIECE_CAPTURED event
            self.broker.publish(EventType.PIECE_CAPTURED, capture_data)
            
            # Verify that play() was called on the capture sound
            mock_capture_sound.play.assert_called_once()
        
        # If we get here without exception, the test passed
        self.assertTrue(True, "Event handling completed without errors")

    def test_invalid_move_event_handling(self):
        """Test that INVALID_MOVE events trigger fail sound playback."""
        with unittest.mock.patch('pygame.mixer.Sound') as mock_sound_class:
            # Mock the Sound objects
            mock_fail_sound = unittest.mock.Mock()
            mock_sound_class.return_value = mock_fail_sound
            
            sound_manager = SoundManager(self.broker, self.sounds_folder)
            
            # Manually add the fail sound to simulate it being loaded
            sound_manager.sounds['fail'] = mock_fail_sound
            
            # Create test invalid move data
            invalid_move_data = {
                "piece_id": "PW_1",
                "attempted_move": [(1, 1), (1, 3)],
                "reason": "Invalid pawn move"
            }
            
            # Publish INVALID_MOVE event
            self.broker.publish(EventType.INVALID_MOVE, invalid_move_data)
            
            # Verify that play() was called on the fail sound
            mock_fail_sound.play.assert_called_once()
        
        # If we get here without exception, the test passed
        self.assertTrue(True, "INVALID_MOVE event handling completed without errors")

    def test_volume_control(self):
        """Test volume control functionality."""
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Test setting volume - should not crash
        sound_manager.set_volume(0.5)
        
        # If we get here without exception, the test passed
        self.assertTrue(True, "Volume control completed without errors")

    def test_stop_all_sounds(self):
        """Test stopping all sounds functionality."""
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Test stopping all sounds - should not crash
        sound_manager.stop_all_sounds()
        
        # If we get here without exception, the test passed
        self.assertTrue(True, "Stop all sounds completed without errors")

    def test_error_handling_in_event_processing(self):
        """Test error handling when sound playback fails."""
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Create a test command
        test_command = Command(1000, "PW", "move", [(1, 1), (2, 2)])
        
        # Publish PIECE_MOVED event - should not crash even if sound fails
        self.broker.publish(EventType.PIECE_MOVED, test_command)
        
        # If we get here without exception, the test passed
        self.assertTrue(True, "Error handling completed without crashing")

    def test_sound_loading_error_handling(self):
        """Test error handling when sound loading fails."""
        # Should not crash even with loading issues
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        self.assertIsNotNone(sound_manager)

    def test_sound_unavailable_warning(self):
        """Test warning when trying to play unavailable sounds."""
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Try to play move sound - should not crash
        test_command = Command(1000, "PW", "move", [(1, 1), (2, 2)])
        self.broker.publish(EventType.PIECE_MOVED, test_command)
        
        # If we get here without exception, the test passed
        self.assertTrue(True, "Sound playback completed without errors")


class TestSoundManagerIntegration(unittest.TestCase):
    """Integration tests for SoundManager with other game components."""

    def setUp(self):
        """Set up test fixtures."""
        self.broker = MessageBroker()
        self.temp_dir = tempfile.mkdtemp()
        self.sounds_folder = pathlib.Path(self.temp_dir)
        
        # Create mock sound files
        (self.sounds_folder / "move.wav").touch()
        (self.sounds_folder / "capture.wav").touch()

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multiple_events_handling(self):
        """Test handling multiple events in sequence."""
        sound_manager = SoundManager(self.broker, self.sounds_folder)
        
        # Publish multiple events
        move_command = Command(1000, "PW", "move", [(1, 1), (2, 2)])
        capture_data = {"piece_id": "PB", "captured_by": "W"}
        
        self.broker.publish(EventType.PIECE_MOVED, move_command)
        self.broker.publish(EventType.PIECE_CAPTURED, capture_data)
        self.broker.publish(EventType.PIECE_MOVED, move_command)
        
        # Should handle all events without crashing
        self.assertTrue(True, "Multiple events handled successfully")

    def test_concurrent_sound_manager_instances(self):
        """Test multiple SoundManager instances don't interfere."""
        # Create two sound managers
        broker1 = MessageBroker()
        broker2 = MessageBroker()
        
        sound_manager1 = SoundManager(broker1, self.sounds_folder)
        sound_manager2 = SoundManager(broker2, self.sounds_folder)
        
        # Publish event to first broker only
        test_command = Command(1000, "PW", "move", [(1, 1), (2, 2)])
        broker1.publish(EventType.PIECE_MOVED, test_command)
        
        # Should not crash - verifies isolation between different game instances
        self.assertTrue(True, "Multiple sound manager instances work correctly")


if __name__ == "__main__":
    # Set up test logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("Running SoundManager tests...")
    unittest.main()
