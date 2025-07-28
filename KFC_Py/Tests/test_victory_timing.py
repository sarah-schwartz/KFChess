import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import from KFC_Py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Game import Game
from Board import Board
from Piece import Piece
from MessageBroker import MessageBroker
from MessageDisplay import MessageDisplay
from EventType import EventType
from Physics import IdlePhysics, MovePhysics
from State import State


class TestVictoryTiming(unittest.TestCase):
    """Test that victory detection waits for pieces to finish moving."""
    
    def setUp(self):
        """Set up test environment."""
        self.board = Board(8, 8, 64, 64)
        self.broker = MessageBroker()
        
        # Create minimal pieces with kings
        self.white_king = self._create_test_piece("KW1", (7, 4))
        self.black_king = self._create_test_piece("KB1", (0, 4))
        self.white_pawn = self._create_test_piece("PW1", (6, 4))
        
        self.pieces = [self.white_king, self.black_king, self.white_pawn]
        
    def _create_test_piece(self, piece_id: str, position: tuple) -> Piece:
        """Create a test piece with mock states."""
        piece = Mock(spec=Piece)
        piece.id = piece_id
        piece.current_cell.return_value = position
        
        # Create mock state with idle physics
        idle_state = Mock(spec=State)
        idle_state.name = 'idle'
        idle_state.physics = Mock(spec=IdlePhysics)
        idle_state.physics.get_start_ms.return_value = 0
        idle_state.can_capture.return_value = True
        idle_state.can_be_captured.return_value = True
        
        piece.state = idle_state
        piece.reset = Mock()
        piece.update = Mock()
        piece.draw_on_board = Mock()
        piece.on_command = Mock()
        
        return piece
    
    def test_victory_detection_waits_for_moving_pieces(self):
        """Test that victory is not declared while pieces are moving."""
        game = Game(self.pieces, self.board, self.broker, validate_board=False)
        
        # Remove black king to create victory condition
        game.pieces = [self.white_king, self.white_pawn]
        
        # Set white pawn to moving state
        moving_state = Mock(spec=State)
        moving_state.name = 'move'
        moving_state.physics = Mock(spec=MovePhysics)
        moving_state.physics.get_start_ms.return_value = 100
        self.white_pawn.state = moving_state
        
        # Should not declare victory while piece is moving
        self.assertFalse(game._is_win())
        
        # Change pawn back to idle
        idle_state = Mock(spec=State)
        idle_state.name = 'idle'
        idle_state.physics = Mock(spec=IdlePhysics)
        idle_state.physics.get_start_ms.return_value = 200
        self.white_pawn.state = idle_state
        
        # Now should declare victory
        self.assertTrue(game._is_win())
    
    def test_victory_detection_waits_for_jumping_pieces(self):
        """Test that victory is not declared while pieces are jumping."""
        game = Game(self.pieces, self.board, self.broker, validate_board=False)
        
        # Remove black king to create victory condition
        game.pieces = [self.white_king, self.white_pawn]
        
        # Set white pawn to jumping state
        jumping_state = Mock(spec=State)
        jumping_state.name = 'jump'
        jumping_state.physics = Mock()
        jumping_state.physics.get_start_ms.return_value = 100
        self.white_pawn.state = jumping_state
        
        # Should not declare victory while piece is jumping
        self.assertFalse(game._is_win())
        
        # Change pawn back to idle
        idle_state = Mock(spec=State)
        idle_state.name = 'idle'
        idle_state.physics = Mock()
        idle_state.physics.get_start_ms.return_value = 200
        self.white_pawn.state = idle_state
        
        # Now should declare victory
        self.assertTrue(game._is_win())
    
    def test_victory_allows_rest_states(self):
        """Test that victory can be declared when pieces are resting."""
        game = Game(self.pieces, self.board, self.broker, validate_board=False)
        
        # Remove black king to create victory condition
        game.pieces = [self.white_king, self.white_pawn]
        
        # Set white pawn to short_rest state
        rest_state = Mock(spec=State)
        rest_state.name = 'short_rest'
        rest_state.physics = Mock()
        rest_state.physics.get_start_ms.return_value = 100
        self.white_pawn.state = rest_state
        
        # Should declare victory even with resting piece
        self.assertTrue(game._is_win())
    
    def test_no_victory_with_both_kings(self):
        """Test that no victory is declared when both kings are present."""
        game = Game(self.pieces, self.board, self.broker, validate_board=False)
        
        # All pieces idle
        for piece in self.pieces:
            idle_state = Mock(spec=State)
            idle_state.name = 'idle'
            idle_state.physics = Mock()
            idle_state.physics.get_start_ms.return_value = 100
            piece.state = idle_state
        
        # Should not declare victory with both kings present
        self.assertFalse(game._is_win())
    
    @patch('builtins.print')
    def test_victory_debug_output(self, mock_print):
        """Test that victory detection produces correct debug output."""
        game = Game(self.pieces, self.board, self.broker, validate_board=False)
        
        # Remove black king to create victory condition
        game.pieces = [self.white_king, self.white_pawn]
        
        # Set pieces to idle
        for piece in game.pieces:
            idle_state = Mock(spec=State)
            idle_state.name = 'idle'
            idle_state.physics = Mock()
            idle_state.physics.get_start_ms.return_value = 100
            piece.state = idle_state
        
        # Call _is_win() to trigger debug output
        result = game._is_win()
        
        # Verify victory was declared
        self.assertTrue(result)
        
        # Check that debug messages were printed
        debug_calls = [call for call in mock_print.call_args_list if 'DEBUG:' in str(call)]
        self.assertGreater(len(debug_calls), 0)
        
        # Check for specific victory debug message
        victory_debug_found = any('Victory condition met' in str(call) for call in debug_calls)
        self.assertTrue(victory_debug_found)


class TestVictoryMessageIntegration(unittest.TestCase):
    """Test integration between victory detection and message display."""
    
    def setUp(self):
        """Set up test environment."""
        self.board = Board(8, 8, 64, 64)
        self.broker = MessageBroker()
        self.message_display = MessageDisplay(self.broker)
        
        # Create test UI mock
        self.mock_ui = Mock()
        self.mock_ui.message_display = self.message_display
        self.mock_ui.render_complete_ui = Mock()
        self.mock_ui.show = Mock()
        
        # Create minimal pieces
        self.white_king = self._create_test_piece("KW1", (7, 4))
        self.pieces = [self.white_king]
        
    def _create_test_piece(self, piece_id: str, position: tuple) -> Piece:
        """Create a test piece with mock states."""
        piece = Mock(spec=Piece)
        piece.id = piece_id
        piece.current_cell.return_value = position
        
        idle_state = Mock(spec=State)
        idle_state.name = 'idle'
        idle_state.physics = Mock()
        idle_state.physics.get_start_ms.return_value = 0
        piece.state = idle_state
        piece.reset = Mock()
        piece.update = Mock()
        piece.draw_on_board = Mock()
        
        return piece
    
    @patch('time.time')
    @patch('time.sleep')
    def test_victory_message_display_timing(self, mock_sleep, mock_time):
        """Test that victory message is displayed for correct duration."""
        # Mock time to control the 5-second display loop
        mock_time.side_effect = [0, 1, 2, 3, 4, 5, 6]  # Simulate time progression
        
        game = Game(self.pieces, self.board, self.broker, self.mock_ui, validate_board=False)
        
        # Call _announce_win to trigger message display
        game._announce_win()
        
        # Verify UI was called multiple times during the 5-second period
        self.assertGreater(self.mock_ui.render_complete_ui.call_count, 4)
        self.assertGreater(self.mock_ui.show.call_count, 4)
        
        # Verify message display was updated
        # Note: message_display.update() is called via hasattr check in the loop
    
    def test_victory_event_published(self):
        """Test that GAME_END event is published with correct data."""
        game = Game(self.pieces, self.board, self.broker, self.mock_ui, validate_board=False)
        
        # Subscribe to GAME_END events
        received_events = []
        
        def capture_event(event_type, data):
            received_events.append((event_type, data))
        
        # Mock subscriber
        mock_subscriber = Mock()
        mock_subscriber.handle_event = capture_event
        self.broker.subscribe(EventType.GAME_END, mock_subscriber)
        
        # Call _announce_win
        game._announce_win()
        
        # Verify event was published
        self.assertEqual(len(received_events), 1)
        event_type, data = received_events[0]
        
        self.assertEqual(event_type, EventType.GAME_END)
        self.assertIn('winner', data)
        self.assertIn('winner_color', data)
        self.assertIn('timestamp', data)
        self.assertIn('total_pieces_remaining', data)
        
        # Verify winner is White (only white king remains)
        self.assertEqual(data['winner_color'], 'White')
        self.assertEqual(data['winner'], 'KW1')
        self.assertEqual(data['total_pieces_remaining'], 1)


class TestVictoryMessageContent(unittest.TestCase):
    """Test that victory messages show correct content."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        self.message_display = MessageDisplay(self.broker)
    
    def test_victory_message_content_white_wins(self):
        """Test victory message for white winner."""
        # Simulate GAME_END event for white victory
        event_data = {
            'winner': 'KW1',
            'winner_color': 'White',
            'timestamp': 1000,
            'total_pieces_remaining': 5
        }
        
        # Trigger event
        self.message_display.handle_event(EventType.GAME_END, event_data)
        
        # Check that message was set
        self.assertIsNotNone(self.message_display.current_message)
        self.assertEqual(self.message_display.current_message, "White Wins!")
    
    def test_victory_message_content_black_wins(self):
        """Test victory message for black winner."""
        # Simulate GAME_END event for black victory
        event_data = {
            'winner': 'KB1',
            'winner_color': 'Black',
            'timestamp': 1000,
            'total_pieces_remaining': 3
        }
        
        # Trigger event
        self.message_display.handle_event(EventType.GAME_END, event_data)
        
        # Check that message was set
        self.assertIsNotNone(self.message_display.current_message)
        self.assertEqual(self.message_display.current_message, "Black Wins!")
    
    @patch('time.time')
    def test_victory_message_duration(self, mock_time):
        """Test that victory message is displayed for 4 seconds."""
        mock_time.side_effect = [0, 1, 2, 3, 4, 5]  # Simulate time progression
        
        # Trigger victory message
        event_data = {
            'winner': 'KW1',
            'winner_color': 'White',
            'timestamp': 1000,
            'total_pieces_remaining': 1
        }
        
        self.message_display.handle_event(EventType.GAME_END, event_data)
        
        # Message should be present initially
        self.assertIsNotNone(self.message_display.current_message)
        
        # Update at 3 seconds - should still be visible
        mock_time.return_value = 3
        self.message_display.update()
        self.assertIsNotNone(self.message_display.current_message)
        
        # Update at 5 seconds - should be hidden
        mock_time.return_value = 5
        self.message_display.update()
        self.assertIsNone(self.message_display.current_message)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
