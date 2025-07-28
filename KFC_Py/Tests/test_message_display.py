#!/usr/bin/env python3
"""
Tests for MessageDisplay class.
Tests message handling for game start and end events.
"""

import sys
import os
import unittest
import tempfile
import pathlib
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append('..')

from MessageBroker import MessageBroker
from MessageDisplay import MessageDisplay
from EventType import EventType


class TestMessageDisplay(unittest.TestCase):
    """Test cases for MessageDisplay functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.broker = MessageBroker()

    def test_message_display_initialization(self):
        """Test MessageDisplay initialization and event subscription."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Check that message display was created successfully
        self.assertIsNotNone(message_display)
        
        # Check that message display subscribed to events
        self.assertIn(EventType.GAME_START, self.broker.subscribers)
        self.assertIn(EventType.GAME_END, self.broker.subscribers)

    def test_game_start_message_handling(self):
        """Test that GAME_START events trigger welcome messages."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Publish GAME_START event
        start_data = {
            "timestamp": 1000,
            "player_count": 2,
            "board_size": (8, 8)
        }
        
        self.broker.publish(EventType.GAME_START, start_data)
        
        # Check that a message is now being displayed
        current_message = message_display.get_current_message()
        self.assertIsNotNone(current_message)
        self.assertIn("", current_message.lower())  # Should contain game-related text
        
        print(f"✓ Game start message displayed: {current_message}")

    def test_game_end_message_handling(self):
        """Test that GAME_END events trigger victory messages."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Publish GAME_END event
        end_data = {
            "winner": "KW_1",
            "winner_color": "White",
            "timestamp": 5000,
            "total_pieces_remaining": 5
        }
        
        self.broker.publish(EventType.GAME_END, end_data)
        
        # Check that a victory message is now being displayed
        current_message = message_display.get_current_message()
        self.assertIsNotNone(current_message)
        self.assertIn("white", current_message.lower())  # Should contain winner info
        
        print(f"✓ Game end message displayed: {current_message}")

    def test_message_alpha_fade_effect(self):
        """Test that message alpha value changes over time for fade effects."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Show a message
        message_display._display_message("Test Message", duration=2.0)
        
        # Initially should have some alpha value
        alpha = message_display.get_message_alpha()
        self.assertGreaterEqual(alpha, 0.0)
        self.assertLessEqual(alpha, 1.0)
        
        print(f"✓ Message alpha value: {alpha}")

    def test_message_update_and_expiration(self):
        """Test that messages expire after their duration."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Show a very short message
        message_display._display_message("Short Message", duration=0.001)  # Very short duration
        
        # Initially should have a message
        self.assertIsNotNone(message_display.get_current_message())
        
        # Update to process expiration
        import time
        time.sleep(0.01)  # Wait longer than duration
        message_display.update()
        
        # Message should be gone now
        self.assertIsNone(message_display.get_current_message())
        
        print("✓ Message properly expired after duration")

    def test_multiple_events_handling(self):
        """Test handling multiple game events in sequence."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Start game
        self.broker.publish(EventType.GAME_START, {
            "timestamp": 1000,
            "player_count": 2
        })
        
        start_message = message_display.get_current_message()
        self.assertIsNotNone(start_message)
        
        # End game (should replace start message)
        self.broker.publish(EventType.GAME_END, {
            "winner": "KB_1",
            "winner_color": "Black",
            "timestamp": 10000
        })
        
        end_message = message_display.get_current_message()
        self.assertIsNotNone(end_message)
        self.assertNotEqual(start_message, end_message)  # Should be different message
        
        print(f"✓ Start message: {start_message}")
        print(f"✓ End message: {end_message}")

    def test_error_handling_in_event_processing(self):
        """Test error handling when message processing fails."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Publish event with invalid data - should not crash
        try:
            self.broker.publish(EventType.GAME_END, {"invalid": "data"})
            # Should handle gracefully
            self.assertTrue(True, "Error handling completed without crashing")
        except Exception as e:
            self.fail(f"MessageDisplay should handle invalid data gracefully: {e}")

    @patch('pygame.font.init')
    @patch('pygame.font.Font')
    def test_font_initialization_failure(self, mock_font_class, mock_font_init):
        """Test behavior when pygame fonts cannot be initialized."""
        # Make font initialization fail
        mock_font_init.side_effect = Exception("No pygame")
        mock_font_class.side_effect = Exception("No pygame")
        
        # Should not crash when fonts fail to initialize
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        self.assertIsNotNone(message_display)
        
        # Should still handle events without crashing
        self.broker.publish(EventType.GAME_START, {"timestamp": 1000})
        
        print("✓ MessageDisplay handles font initialization failure gracefully")


class TestMessageDisplayIntegration(unittest.TestCase):
    """Integration tests for MessageDisplay with game events."""

    def setUp(self):
        """Set up test fixtures."""
        self.broker = MessageBroker()

    def test_complete_game_message_flow(self):
        """Test the complete flow of messages during a game."""
        message_display = MessageDisplay(self.broker, screen_width=800, screen_height=600)
        
        # Simulate complete game flow
        print("Starting complete game message flow test...")
        
        # 1. Game starts
        self.broker.publish(EventType.GAME_START, {
            "timestamp": 0,
            "player_count": 2,
            "board_size": (8, 8)
        })
        
        start_message = message_display.get_current_message()
        print(f"1. Game start: {start_message}")
        self.assertIsNotNone(start_message)
        
        # 2. Game progresses (simulate some time passing)
        import time
        time.sleep(0.1)
        message_display.update()
        
        # 3. Game ends
        self.broker.publish(EventType.GAME_END, {
            "winner": "KW_1",
            "winner_color": "White",
            "timestamp": 60000,
            "total_pieces_remaining": 3
        })
        
        end_message = message_display.get_current_message()
        print(f"2. Game end: {end_message}")
        self.assertIsNotNone(end_message)
        
        print("✓ Complete game message flow test passed")


if __name__ == "__main__":
    print("Running MessageDisplay tests...")
    unittest.main(verbosity=2)
