"""
Test module for game integration and setup.
Contains utilities for creating and testing complete game instances with history.
"""

import sys
import os

# Add the parent directory to the Python path to allow module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from GameHistoryDisplay import GameHistoryDisplay
from MessageBroker import MessageBroker
from Command import Command
from EventType import EventType


def test_game_creation():
    """
    Simple test to verify game creation works properly.
    """
    print("Testing game creation with history...")
    
    # Create MessageBroker for testing
    broker = MessageBroker()
    
    # Create history manager
    history_display = GameHistoryDisplay(broker)
    
    # Simulate some test commands
    test_commands = [
        Command(1000, "PW", "move", ["e2", "e4"]),
        Command(2000, "PB", "move", ["e7", "e5"]),
    ]
    
    # Publish commands
    for cmd in test_commands:
        broker.publish(EventType.PIECE_MOVED, cmd)
    
    # Verify creation worked
    counts = history_display.get_move_counts()
    print(f"Test completed: {counts['white']} white moves, {counts['black']} black moves")
    
    return True


if __name__ == "__main__":
    test_game_creation()
