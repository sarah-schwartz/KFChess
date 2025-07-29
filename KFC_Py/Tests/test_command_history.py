#!/usr/bin/env python3
import unittest
from unittest.mock import Mock, patch
import sys
import os
import time

# Add the parent directory to the path so we can import from KFC_Py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from CommandHistoryManager import CommandHistoryManager
from MessageBroker import MessageBroker
from EventType import EventType
from Command import Command


class TestCommandHistoryManager(unittest.TestCase):
    """Test CommandHistoryManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        self.white_history = CommandHistoryManager("W", self.broker)
        self.black_history = CommandHistoryManager("B", self.broker)
    
    def test_initialization(self):
        """Test CommandHistoryManager initialization."""
        self.assertEqual(self.white_history.player_color, "W")
        self.assertEqual(self.black_history.player_color, "B")
        self.assertIsNotNone(self.white_history.broker)
        self.assertTrue(self.white_history.command_history.empty())
        self.assertEqual(len(self.white_history.formatted_history), 0)
    
    def test_piece_ownership_check(self):
        """Test _is_my_piece method."""
        # White pieces
        self.assertTrue(self.white_history._is_my_piece("KW"))
        self.assertTrue(self.white_history._is_my_piece("PW1"))
        self.assertTrue(self.white_history._is_my_piece("QW"))
        
        # Black pieces should not belong to white player
        self.assertFalse(self.white_history._is_my_piece("KB"))
        self.assertFalse(self.white_history._is_my_piece("PB1"))
        
        # Invalid piece IDs
        self.assertFalse(self.white_history._is_my_piece("K"))
        self.assertFalse(self.white_history._is_my_piece(""))
    
    def test_white_piece_move_recorded(self):
        """Test that white piece moves are recorded for white player."""
        # Create a Command for white king move
        command = Command(
            timestamp=int(time.time() * 1000),  # Convert to milliseconds
            piece_id="KW",
            type="move",
            params=[(4, 7), (5, 7)]
        )
        
        # Publish move event through broker
        self.broker.publish(EventType.PIECE_MOVED, command)
        
        # Check that white history recorded the move
        self.assertFalse(self.white_history.command_history.empty())
        self.assertEqual(len(self.white_history.formatted_history), 1)
        
        # Black history should be empty
        self.assertTrue(self.black_history.command_history.empty())
        self.assertEqual(len(self.black_history.formatted_history), 0)
    
    def test_black_piece_move_recorded(self):
        """Test that black piece moves are recorded for black player."""
        # Create a Command for black queen move
        command = Command(
            timestamp=int(time.time() * 1000),  # Convert to milliseconds
            piece_id="QB",
            type="move",
            params=[(3, 0), (3, 4)]
        )
        
        # Publish move event through broker
        self.broker.publish(EventType.PIECE_MOVED, command)
        
        # Check that black history recorded the move
        self.assertFalse(self.black_history.command_history.empty())
        self.assertEqual(len(self.black_history.formatted_history), 1)
        
        # White history should be empty
        self.assertTrue(self.white_history.command_history.empty())
        self.assertEqual(len(self.white_history.formatted_history), 0)
    
    def test_multiple_moves_recorded(self):
        """Test multiple moves are recorded in order."""
        # Create multiple commands for white pieces
        command1 = Command(
            timestamp=int(time.time() * 1000),  # Convert to milliseconds
            piece_id="PW1",
            type="move",
            params=[(0, 6), (0, 5)]
        )
        
        command2 = Command(
            timestamp=int(time.time() * 1000) + 1000,  # Add 1 second in milliseconds
            piece_id="NW1",
            type="move",
            params=[(1, 7), (2, 5)]
        )
        
        # Publish move events through broker
        self.broker.publish(EventType.PIECE_MOVED, command1)
        self.broker.publish(EventType.PIECE_MOVED, command2)
        
        # Check that both moves were recorded
        self.assertEqual(len(self.white_history.formatted_history), 2)
        
        # Check that moves are in correct order by examining the formatted descriptions
        descriptions = [entry["description"] for entry in self.white_history.formatted_history]
        self.assertEqual(len(descriptions), 2)
        
        # Both descriptions should contain piece names and positions
        self.assertIn("Pawn", descriptions[0])
        self.assertIn("Knight", descriptions[1])
    
    def test_jump_command_recorded(self):
        """Test that jump commands are recorded."""
        # Create a jump command for white piece
        command = Command(
            timestamp=int(time.time() * 1000),  # Convert to milliseconds
            piece_id="BW1",
            type="jump",
            params=[(2, 7), (4, 5)]
        )
        
        # Publish jump event through broker
        self.broker.publish(EventType.PIECE_MOVED, command)
        
        # Check that jump was recorded
        self.assertEqual(len(self.white_history.formatted_history), 1)
        description = self.white_history.formatted_history[0]["description"]
        self.assertIn("Bishop", description)
        self.assertIn("->", description)  # Should show movement
    
    def test_non_move_commands_ignored(self):
        """Test that non-move/jump commands are ignored."""
        # Create a command that is not move or jump
        command = Command(
            timestamp=int(time.time() * 1000),  # Convert to milliseconds
            piece_id="KW",
            type="capture",
            params=["some", "params"]
        )
        
        # Publish event through broker
        self.broker.publish(EventType.PIECE_MOVED, command)
        
        # History should remain empty since it's not a move/jump
        self.assertTrue(self.white_history.command_history.empty())
        self.assertEqual(len(self.white_history.formatted_history), 0)


if __name__ == '__main__':
    unittest.main()
