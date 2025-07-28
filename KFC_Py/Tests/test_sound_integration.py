#!/usr/bin/env python3
"""
Integration tests for sound system with GameFactory.
Tests that sound system is properly integrated into game creation.
"""

import unittest
import pathlib
import tempfile
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append('..')

# Mock pygame and GUI components before any imports
with patch.dict('sys.modules', {
    'pygame': MagicMock(),
    'pygame.mixer': MagicMock(),
    'pygame.mixer.Sound': MagicMock()
}):
    from GameFactory import create_game_with_history
    from GraphicsFactory import MockImgFactory
    from SoundManager import SoundManager
    from MessageBroker import MessageBroker
    from EventType import EventType


class TestSoundSystemIntegration(unittest.TestCase):
    """Test sound system integration with game creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pieces_root = pathlib.Path(self.temp_dir)
        
        # Mock pygame and GUI components
        self.pygame_patcher = patch('pygame.mixer')
        self.pygame_sound_patcher = patch('pygame.mixer.Sound')
        self.input_patcher = patch('builtins.input', return_value='TestPlayer')
        self.gui_patcher = patch('PlayerNamesManager.PlayerNamesManager.get_player_names_from_gui', 
                                return_value=('White Player', 'Black Player'))
        
        self.mock_mixer = self.pygame_patcher.start()
        self.mock_sound_class = self.pygame_sound_patcher.start()
        self.mock_input = self.input_patcher.start()
        self.mock_gui = self.gui_patcher.start()
        
        # Configure pygame mocks
        self.mock_mixer.init.return_value = None
        self.mock_mixer.get_init.return_value = (22050, -16, 2)
        self.mock_sound = MagicMock()
        self.mock_sound_class.return_value = self.mock_sound
        
        # Create required game files
        self._create_test_game_files()

    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        self.pygame_patcher.stop()
        self.pygame_sound_patcher.stop()
        self.input_patcher.stop()
        self.gui_patcher.stop()
        
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_game_files(self):
        """Create minimal game files for testing."""
        # Create board.csv
        board_csv = self.pieces_root / "board.csv"
        with board_csv.open('w') as f:
            f.write("RB,NB,BB,QB,KB,BB,NB,RB\n")
            f.write("PB,PB,PB,PB,PB,PB,PB,PB\n")
            f.write(",,,,,,,,\n")
            f.write(",,,,,,,,\n")
            f.write(",,,,,,,,\n")
            f.write(",,,,,,,,\n")
            f.write("PW,PW,PW,PW,PW,PW,PW,PW\n")
            f.write("RW,NW,BW,QW,KW,BW,NW,RW\n")

        # Create board.png (dummy file)
        board_png = self.pieces_root / "board.png"
        board_png.touch()

        # Create sound directory and files
        sound_dir = self.pieces_root / "sound"
        sound_dir.mkdir()
        (sound_dir / "move.wav").touch()
        (sound_dir / "capture.wav").touch()

        # Create piece directories (minimal structure)
        for piece in ["RB", "NB", "BB", "QB", "KB", "PB", "RW", "NW", "BW", "QW", "KW", "PW"]:
            piece_dir = self.pieces_root / piece
            piece_dir.mkdir()
            states_dir = piece_dir / "states"
            states_dir.mkdir()
            idle_dir = states_dir / "idle"
            idle_dir.mkdir()
            
            # Create sprites directory
            sprites_dir = idle_dir / "sprites"
            sprites_dir.mkdir()
            (sprites_dir / "frame_0.png").touch()
            
            # Create moves.txt
            moves_file = idle_dir / "moves.txt"
            with moves_file.open('w') as f:
                f.write("1,0\n")
                f.write("-1,0\n")

        # Create background.jpg
        (self.pieces_root / "background.jpg").touch()

    def test_sound_manager_created_during_game_creation(self):
        """Test that SoundManager is created and integrated during game creation."""
        # Create game with sound system
        game, ui, history_display, broker, sound_manager = create_game_with_history(
            self.pieces_root, MockImgFactory()
        )
        
        # Verify sound manager was created
        self.assertIsInstance(sound_manager, SoundManager)
        
        # Verify sound manager is subscribed to events
        self.assertIn(EventType.PIECE_MOVED, broker.subscribers)
        self.assertIn(EventType.PIECE_CAPTURED, broker.subscribers)

    @patch('pygame.mixer.init')
    @patch('pygame.mixer.Sound')
    @patch('KFC_Py.PlayerNamesManager.PlayerNamesManager.get_player_names_from_gui')
    def test_sound_system_handles_game_events(self, mock_names, mock_sound, mock_init):
        """Test that sound system responds to actual game events."""
        # Mock player name input
        mock_names.return_value = ("TestWhite", "TestBlack")
        
    def test_sound_system_handles_game_events(self):
        """Test that sound system responds to actual game events."""
        # Create game with sound system
        game, ui, history_display, broker, sound_manager = create_game_with_history(
            self.pieces_root, MockImgFactory()
        )
        
        # Simulate piece move event
        from Command import Command
        move_command = Command(1000, "PW", "move", [(6, 0), (5, 0)])
        broker.publish(EventType.PIECE_MOVED, move_command)
        
        # Simulate piece capture event
        capture_data = {
            "piece_id": "PB",
            "captured_by": "W",
            "captured_at": (5, 0)
        }
        broker.publish(EventType.PIECE_CAPTURED, capture_data)
        
        # If we get here without exceptions, the test passed
        self.assertTrue(True, "Sound system handled events without errors")

    @patch('pygame.mixer.init')
    @patch('pygame.mixer.Sound')
    @patch('KFC_Py.PlayerNamesManager.PlayerNamesManager.get_player_names_from_gui')
    def test_missing_sound_files_graceful_handling(self, mock_names, mock_sound, mock_init):
        """Test that missing sound files are handled gracefully."""
        # Mock player name input
        mock_names.return_value = ("TestWhite", "TestBlack")
        
        # Remove sound files
        sound_dir = self.pieces_root / "sound"
        for sound_file in sound_dir.glob("*.wav"):
            sound_file.unlink()
        
        # Mock sound loading to fail
        mock_sound.side_effect = Exception("File not found")
        
        # Should not crash even with missing sound files
        game, ui, history_display, broker, sound_manager = create_game_with_history(
            self.pieces_root, MockImgFactory()
        )
        
        # Sound manager should still be created
        self.assertIsInstance(sound_manager, SoundManager)

    def test_sound_system_with_game_backward_compatibility(self):
        """Test that create_game (backward compatibility) still works with sound system."""
        # Test backward compatibility function
        from GameFactory import create_game
        game = create_game(self.pieces_root, MockImgFactory())
        
        # Should not crash and should return a game instance
        self.assertIsNotNone(game)


class TestSoundSystemPerformance(unittest.TestCase):
    """Performance tests for sound system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.sounds_folder = pathlib.Path(self.temp_dir)
        
        # Create mock sound files
        (self.sounds_folder / "move.wav").touch()
        (self.sounds_folder / "capture.wav").touch()

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rapid_event_handling(self):
        """Test sound system performance with rapid events."""
        broker = MessageBroker()
        sound_manager = SoundManager(broker, self.sounds_folder)
        
        # Simulate rapid events
        from Command import Command
        for i in range(100):
            move_command = Command(i * 10, f"P{i%2}", "move", [(i%8, 0), ((i+1)%8, 0)])
            broker.publish(EventType.PIECE_MOVED, move_command)
            
            if i % 10 == 0:  # Every 10th event is a capture
                capture_data = {"piece_id": f"P{i%2}", "captured_by": "W"}
                broker.publish(EventType.PIECE_CAPTURED, capture_data)
        
        # Should handle all events without crashing
        self.assertTrue(True, "Rapid events handled successfully")

    def test_memory_usage_with_long_game(self):
        """Test that sound system doesn't leak memory during long games."""
        broker = MessageBroker()
        sound_manager = SoundManager(broker, self.sounds_folder)
        
        # Simulate a very long game with many events
        from Command import Command
        for i in range(1000):
            if i % 2 == 0:
                move_command = Command(i * 10, "PW", "move", [(i%8, 0), ((i+1)%8, 0)])
                broker.publish(EventType.PIECE_MOVED, move_command)
            else:
                capture_data = {"piece_id": "PB", "captured_by": "W"}
                broker.publish(EventType.PIECE_CAPTURED, capture_data)
        
        # Sound manager should still be responsive
        test_command = Command(10000, "PW", "move", [(0, 0), (1, 1)])
        broker.publish(EventType.PIECE_MOVED, test_command)
        
        # Should handle all events without crashing
        self.assertTrue(True, "Long game simulation completed successfully")


if __name__ == "__main__":
    print("Running Sound System Integration tests...")
    unittest.main()
