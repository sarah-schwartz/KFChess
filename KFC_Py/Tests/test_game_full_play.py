import pathlib, time
import logging

from GraphicsFactory import MockImgFactory
from Game import Game
from Command import Command
from GameFactory import create_game

import numpy as np

import pytest

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

PIECES_ROOT = pathlib.Path(__file__).parent.parent.parent / "pieces"
BOARD_CSV = PIECES_ROOT / "board.csv"


# ---------------------------------------------------------------------------
#                          GAMEPLAY TESTS
# ---------------------------------------------------------------------------




def test_gameplay_pawn_move_and_capture():
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()
    pw = game.pos[(6, 0)][0]
    pb = game.pos[(1, 1)][0]
    game.user_input_queue.put(Command(game.game_time_ms(), pw.id, "move", [(6, 0), (4, 0)]))
    game.user_input_queue.put(Command(game.game_time_ms(), pb.id, "move", [(1, 1), (3, 1)]))
    time.sleep(0.5)
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    assert pw.current_cell() == (4, 0)
    assert pb.current_cell() == (3, 1)
    time.sleep(0.5)
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    game.user_input_queue.put(Command(game.game_time_ms(), pw.id, "move", [(4, 0), (3, 1)]))
    time.sleep(0.5)
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    assert pw.current_cell() == (3, 1)
    assert pw in game.pieces
    assert pb not in game.pieces


# ---------------------------------------------------------------------------
#                          ADDITIONAL GAMEPLAY SCENARIO TESTS
# ---------------------------------------------------------------------------


def test_piece_blocked_by_own_color():
    """A rook cannot move through a friendly pawn that blocks its path."""
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000  # speed-up time for fast tests
    game._update_cell2piece_map()

    rook = game.pos[(7, 0)][0]  # White rook initially at a1

    # Attempt to move the rook two squares forward but the white pawn on (6,0) blocks it
    game.user_input_queue.put(Command(game.game_time_ms(), rook.id, "move", [(7, 0), (5, 0)]))
    time.sleep(0.2)
    game._run_game_loop(num_iterations=50, is_with_graphics=False)

    # Rook must stay in place because the path is blocked by its own pawn
    assert rook.current_cell() == (7, 0)


def test_illegal_move_rejected():
    """A bishop attempting a vertical move (illegal) should be rejected."""
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    bishop = game.pos[(7, 2)][0]  # White bishop on c1

    # Vertical move is illegal for a bishop
    game.user_input_queue.put(Command(game.game_time_ms(), bishop.id, "move", [(7, 2), (5, 2)]))
    time.sleep(0.2)
    game._run_game_loop(num_iterations=50, is_with_graphics=False)

    assert bishop.current_cell() == (7, 2)


def test_knight_jumps_over_friendly_pieces():
    """A knight should be able to jump over friendly pieces."""
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    knight = game.pos[(7, 1)][0]  # White knight on b1

    # Knight jumps to c3 over own pawns
    game.user_input_queue.put(Command(game.game_time_ms(), knight.id, "move", [(7, 1), (5, 2)]))
    time.sleep(0.2)
    game._run_game_loop(num_iterations=100, is_with_graphics=False)

    assert knight.current_cell() == (5, 2)


def test_piece_capture():
    """Knight captures an opposing pawn after a sequence of moves."""
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    # 1. Advance the black pawn from d7 to d5.
    bp = game.pos[(1, 3)][0]  # Black pawn on d7
    print(f"Black pawn at {bp.current_cell()}")
    game.user_input_queue.put(Command(game.game_time_ms(), bp.id, "move", [(1, 3), (3, 3)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"Black pawn moved to {bp.current_cell()}")

    # 2. Move white knight (b1) to c3.
    wn = game.pos[(7, 1)][0]
    print(f"White knight at {wn.current_cell()}")
    game.user_input_queue.put(Command(game.game_time_ms(), wn.id, "move", [(7, 1), (5, 2)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"White knight moved to {wn.current_cell()}")
    print(f"White knight state: {wn.state.name}")

    # 3. Knight captures the pawn on d5 (3,3).
    print(f"Attempting to move knight from {wn.current_cell()} to (3,3)")
    print(f"Knight state before move: {wn.state.name}")
    game.user_input_queue.put(Command(game.game_time_ms(), wn.id, "move", [(5, 2), (3, 3)]))
    game._run_game_loop(num_iterations=150, is_with_graphics=False)
    print(f"Knight final position: {wn.current_cell()}")
    print(f"Knight state after move: {wn.state.name}")

    assert wn.current_cell() == (3, 3)
    assert bp not in game.pieces  # Pawn was captured


def test_pawn_double_step_only_first_move():
    """Pawn may move two squares only on its initial move; afterwards only one square."""
    game = create_game("../pieces", MockImgFactory())
    game._time_factor = 1_000_000_000
    game._update_cell2piece_map()

    pawn = game.pos[(6, 0)][0]  # White pawn on a2
    print(f"Pawn at {pawn.current_cell()}")
    print(f"Pawn state: {pawn.state.name}")

    # First move: two squares forward (allowed)
    game.user_input_queue.put(Command(game.game_time_ms(), pawn.id, "move", [(6, 0), (4, 0)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"Pawn after first move: {pawn.current_cell()}")
    print(f"Pawn state after first move: {pawn.state.name}")
    assert pawn.current_cell() == (4, 0)

    # Second move: one square forward (allowed)
    game.user_input_queue.put(Command(game.game_time_ms(), pawn.id, "move", [(4, 0), (3, 0)]))
    game._run_game_loop(num_iterations=100, is_with_graphics=False)
    print(f"Pawn after second move: {pawn.current_cell()}")
    print(f"Pawn state after second move: {pawn.state.name}")
    assert pawn.current_cell() == (3, 0)

    # Third move: two squares forward (should be rejected)
    game.user_input_queue.put(Command(game.game_time_ms(), pawn.id, "move", [(3, 0), (1, 0)]))
    game._run_game_loop(num_iterations=50, is_with_graphics=False)
    print(f"Pawn after third move: {pawn.current_cell()}")
    print(f"Pawn state after third move: {pawn.state.name}")
    assert pawn.current_cell() == (3, 0)  # Should still be at (3,0)

