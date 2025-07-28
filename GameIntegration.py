"""
Module for integrating the new command history management system with the existing game.
"""

from typing import Optional
import pathlib
from Game import Game
from GameUI import GameUI
from GameHistoryDisplay import GameHistoryDisplay
from MessageBroker import MessageBroker
from Board import Board
from Piece import Piece
from typing import List


def create_game_with_history(pieces: List[Piece], board: Board, pieces_folder: pathlib.Path) -> tuple[Game, GameUI, GameHistoryDisplay, MessageBroker]:
    """
    Create a new game with full command history management support.
    
    Args:
        pieces: List of pieces
        board: Game board
        pieces_folder: Folder containing piece images
        
    Returns:
        tuple containing game, UI, history manager and message broker
    """
    # Create central MessageBroker
    broker = MessageBroker()
    
    # Create UI with broker
    ui = GameUI(None, pieces_folder, broker)  # Pass None for game temporarily
    
    # Create game with broker and UI
    game = Game(pieces, board, broker, ui)
    
    # Set game reference in UI
    ui.game = game
    
    # Get history display from UI
    history_display = ui.history_display
    
    return game, ui, history_display, broker


def test_history_system():
    """
    Function to test the new system.
    """
    print("Testing command history management system...")
    
    # Create MessageBroker for testing
    broker = MessageBroker()
    
    # Create history manager
    history_display = GameHistoryDisplay(broker)
    
    # Simulate commands
    from Command import Command
    from EventType import EventType
    
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
        broker.publish(EventType.PIECE_MOVED, cmd)
    
    # Display results
    print("\nWhite player history:")
    white_history = history_display.get_white_player_history()
    for move in white_history:
        print(f"  {move}")
    
    print("\nBlack player history:")
    black_history = history_display.get_black_player_history()
    for move in black_history:
        print(f"  {move}")
    
    # Display move counts and scores
    counts = history_display.get_move_counts()
    scores = history_display.get_scores()
    print(f"\nSummary: White player - {counts['white']} moves, {scores['white']} points")
    print(f"         Black player - {counts['black']} moves, {scores['black']} points")
    
    # Display full table
    history_display.print_full_history()
    
    print("\nSystem test completed successfully!")


if __name__ == "__main__":
    test_history_system()
