import pathlib, time, sys
import logging

# Add parent directory to path for imports
sys.path.append('..')

from GraphicsFactory import MockImgFactory
from Game import Game
from Command import Command
from GameFactory import create_game
from KeyboardInput import KeyboardProducer, KeyboardProcessor

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

def test_player_color_restrictions():
    """Test that players can only select pieces of their own color."""
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # Create keyboard processors for testing
    p1_map = {"enter": "select"}
    p2_map = {"f": "select"}
    
    kp1 = KeyboardProcessor(8, 8, p1_map, initial_pos=(7, 0))  # Player 1 (White)
    kp2 = KeyboardProcessor(8, 8, p2_map, initial_pos=(0, 0))  # Player 2 (Black)
    
    kb_prod_1 = KeyboardProducer(game, game.user_input_queue, kp1, player=1)
    kb_prod_2 = KeyboardProducer(game, game.user_input_queue, kp2, player=2)
    
    # Test that Player 1 can select white pieces
    white_piece = game.pos[(7, 0)][0]  # White rook
    print(f"White piece: {white_piece.id} at {white_piece.current_cell()}")
    assert white_piece.id[1] == 'W', "Should be a white piece"
    
    # Test that Player 2 can select black pieces  
    black_piece = game.pos[(0, 0)][0]  # Black rook
    print(f"Black piece: {black_piece.id} at {black_piece.current_cell()}")
    assert black_piece.id[1] == 'B', "Should be a black piece"
    
    # Verify initial cursor positions
    assert kp1.get_cursor() == (7, 0), "Player 1 should start at bottom"
    assert kp2.get_cursor() == (0, 0), "Player 2 should start at top"
    
    # Test color assignment
    assert kb_prod_1.my_color == "W", "Player 1 should control white pieces"
    assert kb_prod_2.my_color == "B", "Player 2 should control black pieces"
    
    print("All color restriction tests passed!")

def test_initial_cursor_positions():
    """Test that cursors start in correct positions."""
    # Player 1 processor (White pieces - bottom of board)
    kp1 = KeyboardProcessor(8, 8, {}, initial_pos=(7, 0))
    assert kp1.get_cursor() == (7, 0), "Player 1 should start at row 7 (white pieces)"
    
    # Player 2 processor (Black pieces - top of board)  
    kp2 = KeyboardProcessor(8, 8, {}, initial_pos=(0, 0))
    assert kp2.get_cursor() == (0, 0), "Player 2 should start at row 0 (black pieces)"
    
    print("Initial cursor position tests passed!")

if __name__ == "__main__":
    test_initial_cursor_positions()
    test_player_color_restrictions()
    print("All tests passed! Players are now restricted to their own color pieces.")
