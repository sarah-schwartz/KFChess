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

def test_jump_command():
    """Test that the jump command correctly transitions a piece to the jump state."""
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # Get a piece to test with (e.g., a white knight)
    piece_to_jump = game.pos[(7, 1)][0]  # White knight on b1
    print(f"Piece to jump: {piece_to_jump.id} at {piece_to_jump.current_cell()}")
    
    # Ensure the piece is initially in the 'idle' state
    assert piece_to_jump.state.name == 'idle', f"Piece should be idle, but is in {piece_to_jump.state.name} state"
    
    # Create a jump command with the current cell as a parameter
    jump_command = Command(game.game_time_ms(), piece_to_jump.id, "jump", [piece_to_jump.current_cell()])
    
    # Process the jump command
    game._process_input(jump_command)
    
    # The piece should now be in the 'jump' state
    print(f"Piece state after jump command: {piece_to_jump.state.name}")
    assert piece_to_jump.state.name == 'jump', f"Piece should be in jump state, but is in {piece_to_jump.state.name} state"
    
    print("✓ Jump command test passed!")

def test_keyboard_jump_action():
    """Test that pressing the jump key queues a jump command."""
    game = create_game("../pieces", MockImgFactory())
    
    # Create a keyboard processor and producer for Player 1
    p1_map = {"enter": "select", "+": "jump"}
    kp1 = KeyboardProcessor(8, 8, p1_map, initial_pos=(7, 1))  # Cursor on white knight
    kb_prod_1 = KeyboardProducer(game, game.user_input_queue, kp1, player=1)
    
    # Simulate selecting the piece
    kb_prod_1.selected_id = "NW_1"
    kb_prod_1.selected_cell = (7, 1)
    
    # Simulate pressing the jump key (+)
    class MockEvent:
        event_type = "down"
        name = "+"
        
    kb_prod_1._on_event(MockEvent())
    
    # Check if a jump command was added to the queue
    assert not game.user_input_queue.empty(), "Input queue should not be empty"
    
    queued_command = game.user_input_queue.get()
    print(f"Queued command: {queued_command}")
    
    assert queued_command.type == "jump", f"Command should be 'jump', but is '{queued_command.type}'"
    assert queued_command.piece_id == "NW_1", f"Piece ID should be 'NW_1', but is '{queued_command.piece_id}'"
    
    print("✓ Keyboard jump action test passed!")

if __name__ == "__main__":
    test_jump_command()
    test_keyboard_jump_action()
    print("All jump tests passed!")
