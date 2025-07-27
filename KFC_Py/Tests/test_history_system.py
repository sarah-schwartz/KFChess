"""
Test module for the command history management system.
Tests the functionality of command tracking and display for chess players.
"""

import unittest
import sys
import os

# Add the parent directory to the Python path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from GameHistoryDisplay import GameHistoryDisplay
from MessageBroker import MessageBroker
from Command import Command
from EventType import EventType


class TestHistorySystem(unittest.TestCase):
    """Test cases for the command history management system."""

    def setUp(self):
        """Set up test environment before each test."""
        self.broker = MessageBroker()
        self.history_display = GameHistoryDisplay(self.broker)

    def test_history_system_functionality(self):
        """Test the core functionality of the history system."""
        print("Testing command history management system...")
        
        # Commands for white player
        white_commands = [
            Command(1000, "PW", "move", ["e2", "e4"]),
            Command(3000, "NW", "move", ["g1", "f3"]),
            Command(5000, "BW", "move", ["f1", "c4"])
        ]
        
        # Commands for black player
        black_commands = [
            Command(2000, "PB", "move", ["e7", "e5"]),
            Command(4000, "NB", "move", ["b8", "c6"]),
            Command(6000, "NB", "move", ["g8", "f6"])
        ]
        
        # Publish commands
        for cmd in white_commands + black_commands:
            self.broker.publish(EventType.PIECE_MOVED, cmd)
        
        # Display results
        print("\nWhite player history:")
        white_history = self.history_display.white_history.get_formatted_history()
        for move in white_history:
            print(f"  {move}")
        
        print("\nBlack player history:")
        black_history = self.history_display.black_history.get_formatted_history()
        for move in black_history:
            print(f"  {move}")
        
        # Check move counts
        counts = self.history_display.get_move_counts()
        print(f"\nSummary: White player - {counts['white']} moves, Black player - {counts['black']} moves")
        
        # Verify results
        self.assertEqual(len(white_history), 3)
        self.assertEqual(len(black_history), 3)
        self.assertEqual(counts['white'], 3)
        self.assertEqual(counts['black'], 3)
        
        # Check timestamp format in moves
        self.assertRegex(white_history[0], r'^\d{2}:\d{2}:\d{2}')
        self.assertRegex(black_history[0], r'^\d{2}:\d{2}:\d{2}')
        
        # Display full table
        self.history_display.print_full_history()
        
        print("\nSystem test completed successfully!")

    def test_move_count_tracking(self):
        """Test that move counts are tracked correctly."""
        # Add some moves
        commands = [
            Command(1000, "PW", "move", ["e2", "e4"]),
            Command(2000, "PB", "move", ["e7", "e5"]),
            Command(3000, "NW", "move", ["g1", "f3"]),
        ]
        
        for cmd in commands:
            self.broker.publish(EventType.PIECE_MOVED, cmd)
        
        counts = self.history_display.get_move_counts()
        self.assertEqual(counts['white'], 2)
        self.assertEqual(counts['black'], 1)

    def test_timestamp_formatting(self):
        """Test that timestamps are formatted correctly as HH:MM:SS."""
        cmd = Command(3661000, "PW", "move", ["e2", "e4"])  # 1 hour, 1 minute, 1 second
        self.broker.publish(EventType.PIECE_MOVED, cmd)
        
        white_history = self.history_display.white_history.get_formatted_history()
        self.assertEqual(len(white_history), 1)
        self.assertTrue(white_history[0].startswith("01:01:01"))


if __name__ == '__main__':
    unittest.main()
