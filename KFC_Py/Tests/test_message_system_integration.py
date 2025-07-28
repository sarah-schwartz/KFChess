import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import from KFC_Py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from MessageDisplay import MessageDisplay, GAME_START_MESSAGE, GAME_END_MESSAGE_TEMPLATE
from MessageBroker import MessageBroker
from EventType import EventType


class TestMessageDisplayConstants(unittest.TestCase):
    """Test that message constants work correctly."""
    
    def test_constants_are_defined(self):
        """Test that message constants are properly defined."""
        self.assertEqual(GAME_START_MESSAGE, "Welcome to KFC Chess!")
        self.assertEqual(GAME_END_MESSAGE_TEMPLATE, "{winner_color} Wins!")
    
    def test_game_end_template_formatting(self):
        """Test that game end template formats correctly."""
        white_message = GAME_END_MESSAGE_TEMPLATE.format(winner_color="White")
        black_message = GAME_END_MESSAGE_TEMPLATE.format(winner_color="Black")
        
        self.assertEqual(white_message, "White Wins!")
        self.assertEqual(black_message, "Black Wins!")


class TestMessageDisplayIntegration(unittest.TestCase):
    """Test full integration of message display system."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        self.message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
    
    def test_game_start_message_exact_content(self):
        """Test that game start shows exact expected message."""
        # Trigger game start event
        self.message_display.handle_event(EventType.GAME_START, {})
        
        # Verify exact message content
        self.assertEqual(self.message_display.current_message, GAME_START_MESSAGE)
        self.assertEqual(self.message_display.current_message, "Welcome to KFC Chess!")
    
    def test_game_end_message_exact_content(self):
        """Test that game end shows exact expected message."""
        # Test white victory
        event_data = {'winner': 'KW1', 'winner_color': 'White'}
        self.message_display.handle_event(EventType.GAME_END, event_data)
        self.assertEqual(self.message_display.current_message, "White Wins!")
        
        # Test black victory
        event_data = {'winner': 'KB1', 'winner_color': 'Black'}
        self.message_display.handle_event(EventType.GAME_END, event_data)
        self.assertEqual(self.message_display.current_message, "Black Wins!")
    
    @patch('time.time')
    def test_message_timing_precision(self, mock_time):
        """Test precise timing of message display and hiding."""
        mock_time.return_value = 0
        
        # Trigger game start message (2.5 second duration)
        self.message_display.handle_event(EventType.GAME_START, {})
        
        # At 0 seconds - message should be visible
        mock_time.return_value = 0
        self.message_display.update()
        self.assertIsNotNone(self.message_display.current_message)
        
        # At 2.4 seconds - message should still be visible
        mock_time.return_value = 2.4
        self.message_display.update()
        self.assertIsNotNone(self.message_display.current_message)
        
        # At 2.6 seconds - message should be hidden
        mock_time.return_value = 2.6
        self.message_display.update()
        self.assertIsNone(self.message_display.current_message)
    
    @patch('time.time')
    def test_victory_message_longer_duration(self, mock_time):
        """Test that victory messages display for 4 seconds."""
        mock_time.return_value = 0
        
        # Trigger game end message (4.0 second duration)
        event_data = {'winner': 'KW1', 'winner_color': 'White'}
        self.message_display.handle_event(EventType.GAME_END, event_data)
        
        # At 3.9 seconds - message should still be visible
        mock_time.return_value = 3.9
        self.message_display.update()
        self.assertIsNotNone(self.message_display.current_message)
        
        # At 4.1 seconds - message should be hidden
        mock_time.return_value = 4.1
        self.message_display.update()
        self.assertIsNone(self.message_display.current_message)
    
    def test_message_overwriting(self):
        """Test that new messages overwrite old ones."""
        # Start with game start message
        self.message_display.handle_event(EventType.GAME_START, {})
        self.assertEqual(self.message_display.current_message, "Welcome to KFC Chess!")
        
        # Immediately show game end message
        event_data = {'winner': 'KB1', 'winner_color': 'Black'}
        self.message_display.handle_event(EventType.GAME_END, event_data)
        
        # Should now show victory message
        self.assertEqual(self.message_display.current_message, "Black Wins!")
    
    def test_subscription_to_events(self):
        """Test that MessageDisplay is properly subscribed to events."""
        # Create a new broker and message display
        broker = MessageBroker()
        msg_display = MessageDisplay(broker)
        
        # Check that it's subscribed to the right events
        game_start_subscribers = broker.subscribers.get(EventType.GAME_START, set())
        game_end_subscribers = broker.subscribers.get(EventType.GAME_END, set())
        
        self.assertIn(msg_display, game_start_subscribers)
        self.assertIn(msg_display, game_end_subscribers)


class TestMessageDisplayAlpha(unittest.TestCase):
    """Test fade effects and alpha calculations."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        self.message_display = MessageDisplay(self.broker)
        self.message_display.message_fade_duration = 0.5  # 0.5 second fade
    
    @patch('time.time')
    def test_fade_in_effect(self, mock_time):
        """Test that messages fade in correctly."""
        # Start message at time 0
        mock_time.return_value = 0
        self.message_display.handle_event(EventType.GAME_START, {})
        
        # At start - alpha should be 0
        mock_time.return_value = 0
        alpha = self.message_display.get_message_alpha()
        self.assertEqual(alpha, 0.0)
        
        # At 0.25 seconds - alpha should be 0.5 (halfway through fade in)
        mock_time.return_value = 0.25
        alpha = self.message_display.get_message_alpha()
        self.assertAlmostEqual(alpha, 0.5, places=2)
        
        # At 0.5 seconds - alpha should be 1.0 (fully visible)
        mock_time.return_value = 0.5
        alpha = self.message_display.get_message_alpha()
        self.assertEqual(alpha, 1.0)
    
    @patch('time.time')
    def test_fade_out_effect(self, mock_time):
        """Test that messages fade out correctly."""
        # Start message at time 0 (2.5 second duration, 0.5 second fade)
        mock_time.return_value = 0
        self.message_display.handle_event(EventType.GAME_START, {})
        
        # At 2.0 seconds - should still be fully visible (fade starts at 2.0)
        mock_time.return_value = 2.0
        alpha = self.message_display.get_message_alpha()
        self.assertEqual(alpha, 1.0)
        
        # At 2.25 seconds - should be halfway faded out
        mock_time.return_value = 2.25
        alpha = self.message_display.get_message_alpha()
        self.assertAlmostEqual(alpha, 0.5, places=2)
        
        # At 2.5 seconds - should be completely faded out
        mock_time.return_value = 2.5
        alpha = self.message_display.get_message_alpha()
        self.assertEqual(alpha, 0.0)
    
    @patch('time.time')
    def test_full_visibility_period(self, mock_time):
        """Test that messages are fully visible between fade in/out."""
        # Start message at time 0 (2.5 second duration, 0.5 second fade each way)
        mock_time.return_value = 0
        self.message_display.handle_event(EventType.GAME_START, {})
        
        # Between 0.5 and 2.0 seconds - should be fully visible
        for test_time in [0.5, 1.0, 1.5, 2.0]:
            mock_time.return_value = test_time
            alpha = self.message_display.get_message_alpha()
            self.assertEqual(alpha, 1.0, f"Alpha should be 1.0 at time {test_time}")


class TestMessageDisplayError(unittest.TestCase):
    """Test error handling in message display."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        self.message_display = MessageDisplay(self.broker)
    
    def test_missing_winner_color(self):
        """Test handling of GAME_END event with missing winner_color."""
        # Send event with missing winner_color
        event_data = {'winner': 'KW1'}
        
        # Should not crash and should use default
        self.message_display.handle_event(EventType.GAME_END, event_data)
        
        # Should show message with "Unknown"
        self.assertEqual(self.message_display.current_message, "Unknown Wins!")
    
    def test_invalid_event_type(self):
        """Test handling of invalid event types."""
        # Should not crash when receiving invalid event
        try:
            self.message_display.handle_event("INVALID_EVENT", {})
        except Exception as e:
            self.fail(f"MessageDisplay crashed on invalid event: {e}")
    
    @patch('builtins.print')
    def test_error_logging(self, mock_print):
        """Test that errors are properly logged."""
        # Create a message display that will fail during handle_event
        with patch.object(self.message_display, '_show_game_start_message', side_effect=Exception("Test error")):
            self.message_display.handle_event(EventType.GAME_START, {})
        
        # Check that error was logged
        error_calls = [call for call in mock_print.call_args_list if 'ERROR:' in str(call)]
        self.assertGreater(len(error_calls), 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
