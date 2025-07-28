import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import from KFC_Py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from GameFactory import GameFactory
from MessageBroker import MessageBroker
from EventType import EventType


class TestFullSystemIntegration(unittest.TestCase):
    """Test complete integration of message system with game."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
    
    def test_game_factory_returns_six_components(self):
        """Test that GameFactory returns all 6 components including MessageDisplay."""
        try:
            result = GameFactory.create_game_with_history(self.broker)
            
            # Should return exactly 6 components
            self.assertEqual(len(result), 6)
            
            game, ui, history_display, broker, sound_manager, message_display = result
            
            # Verify all components are not None
            self.assertIsNotNone(game)
            self.assertIsNotNone(ui)
            self.assertIsNotNone(history_display)
            self.assertIsNotNone(broker)
            self.assertIsNotNone(sound_manager)
            self.assertIsNotNone(message_display)
            
            # Verify message_display is the correct type
            from MessageDisplay import MessageDisplay
            self.assertIsInstance(message_display, MessageDisplay)
            
        except Exception as e:
            self.fail(f"GameFactory.create_game_with_history failed: {e}")
    
    def test_message_display_in_ui(self):
        """Test that UI contains message_display."""
        try:
            game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
            
            # UI should have message_display attribute
            self.assertTrue(hasattr(ui, 'message_display'))
            self.assertEqual(ui.message_display, message_display)
            
        except Exception as e:
            self.fail(f"UI message_display integration failed: {e}")
    
    def test_event_flow_game_start(self):
        """Test complete event flow from game start to message display."""
        game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
        
        # Track events received by message display
        original_handle_event = message_display.handle_event
        received_events = []
        
        def track_events(event_type, data):
            received_events.append((event_type, data))
            return original_handle_event(event_type, data)
        
        message_display.handle_event = track_events
        
        # Mock game run to avoid infinite loop
        with patch.object(game, '_run_game_loop'), \
             patch.object(game, '_announce_win'), \
             patch.object(game, 'start_user_input_thread'):
            
            # Run game start (should publish GAME_START event)
            game.run(num_iterations=0, is_with_graphics=False)
        
        # Check that GAME_START event was received
        game_start_events = [event for event in received_events if event[0] == EventType.GAME_START]
        self.assertEqual(len(game_start_events), 1)
        
        # Check that message was set correctly
        self.assertEqual(message_display.current_message, "Welcome to KFC Chess!")
    
    def test_event_flow_game_end(self):
        """Test complete event flow from game end to message display."""
        game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
        
        # Track events received by message display
        original_handle_event = message_display.handle_event
        received_events = []
        
        def track_events(event_type, data):
            received_events.append((event_type, data))
            return original_handle_event(event_type, data)
        
        message_display.handle_event = track_events
        
        # Mock UI methods to avoid pygame issues
        ui.render_complete_ui = Mock()
        ui.show = Mock()
        
        # Mock time to speed up the test
        with patch('time.time', side_effect=[0, 6]), \
             patch('time.sleep'):
            
            # Call announce_win (should publish GAME_END event and show message)
            game._announce_win()
        
        # Check that GAME_END event was received
        game_end_events = [event for event in received_events if event[0] == EventType.GAME_END]
        self.assertEqual(len(game_end_events), 1)
        
        # Check event data
        event_type, event_data = game_end_events[0]
        self.assertIn('winner_color', event_data)
        self.assertIn('winner', event_data)
        
        # Check that victory message was set
        self.assertIn('Wins!', message_display.current_message)
    
    def test_invalid_move_sound_integration(self):
        """Test that invalid move events trigger sound system."""
        game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
        
        # Track events received by sound manager
        original_handle_event = sound_manager.handle_event
        received_events = []
        
        def track_sound_events(event_type, data):
            received_events.append((event_type, data))
            return original_handle_event(event_type, data)
        
        sound_manager.handle_event = track_sound_events
        
        # Publish INVALID_MOVE event
        game.event_publisher.send(EventType.INVALID_MOVE, {
            "piece_id": "PW1",
            "attempted_move": [(6, 0), (5, 0)],
            "reason": "Test invalid move"
        })
        
        # Check that INVALID_MOVE event was received by sound manager
        invalid_move_events = [event for event in received_events if event[0] == EventType.INVALID_MOVE]
        self.assertEqual(len(invalid_move_events), 1)
    
    @patch('pygame.font.init')
    @patch('pygame.font.Font')
    def test_message_display_font_initialization(self, mock_font, mock_font_init):
        """Test that MessageDisplay initializes fonts correctly."""
        # Mock font creation
        mock_font_instance = Mock()
        mock_font.return_value = mock_font_instance
        
        # Create message display
        game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
        
        # Check that font initialization was attempted
        mock_font_init.assert_called()
        
        # Check that fonts were created
        self.assertEqual(mock_font.call_count, 2)  # large and medium fonts
    
    def test_message_constants_integration(self):
        """Test that message constants are used throughout the system."""
        from MessageDisplay import GAME_START_MESSAGE, GAME_END_MESSAGE_TEMPLATE
        
        game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
        
        # Test game start message
        message_display.handle_event(EventType.GAME_START, {})
        self.assertEqual(message_display.current_message, GAME_START_MESSAGE)
        
        # Test game end message template
        event_data = {'winner': 'KW1', 'winner_color': 'White'}
        message_display.handle_event(EventType.GAME_END, event_data)
        expected_message = GAME_END_MESSAGE_TEMPLATE.format(winner_color='White')
        self.assertEqual(message_display.current_message, expected_message)


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world scenarios and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
    
    def test_rapid_game_events(self):
        """Test system behavior with rapid consecutive events."""
        game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
        
        # Rapidly send multiple events
        events = [
            (EventType.GAME_START, {}),
            (EventType.INVALID_MOVE, {"piece_id": "PW1", "reason": "test"}),
            (EventType.PIECE_MOVED, Mock()),
            (EventType.PIECE_CAPTURED, {"piece_id": "PB1", "captured_by": "W"}),
            (EventType.GAME_END, {"winner": "KW1", "winner_color": "White"})
        ]
        
        for event_type, data in events:
            game.event_publisher.send(event_type, data)
        
        # System should handle all events without crashing
        # Final message should be the game end message
        self.assertEqual(message_display.current_message, "White Wins!")
    
    def test_system_without_ui(self):
        """Test that system works even without UI."""
        # Create game without UI
        from Game import Game
        from Board import Board
        from Piece import Piece
        
        board = Board(8, 8, 64, 64)
        pieces = []  # Empty for this test
        game = Game(pieces, board, self.broker, ui=None, validate_board=False)
        
        # Should not crash when announcing win without UI
        try:
            with patch('time.time', return_value=0), \
                 patch('time.sleep'):
                game._announce_win()
        except Exception as e:
            self.fail(f"Game without UI crashed: {e}")
    
    @patch('time.time')
    @patch('time.sleep')
    def test_message_timing_in_real_scenario(self, mock_sleep, mock_time):
        """Test message timing in realistic game scenario."""
        # Simulate time progression during victory sequence
        time_sequence = [0, 1, 2, 3, 4, 5, 6]
        mock_time.side_effect = time_sequence
        
        game, ui, history_display, broker, sound_manager, message_display = GameFactory.create_game_with_history(self.broker)
        
        # Mock UI methods
        ui.render_complete_ui = Mock()
        ui.show = Mock()
        
        # Call victory sequence
        game._announce_win()
        
        # Verify UI was called during the 5-second display period
        self.assertGreater(ui.render_complete_ui.call_count, 0)
        self.assertGreater(ui.show.call_count, 0)
        
        # Verify sleep was called to control frame rate
        self.assertGreater(mock_sleep.call_count, 0)


if __name__ == '__main__':
    # Run with high verbosity to see all test details
    unittest.main(verbosity=2, buffer=True)
