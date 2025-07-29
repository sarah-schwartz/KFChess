import queue, threading, time, math, logging
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict

from Board import Board
from Command import Command
from Piece import Piece
from GameEventPublisher import GameEventPublisher
from MessageBroker import MessageBroker
from EventType import EventType

from KeyboardInput import KeyboardProcessor, KeyboardProducer

# set up a module-level logger – real apps can configure handlers/levels
logger = logging.getLogger(__name__)


class InvalidBoard(Exception): ...


class Game:
    def __init__(self, pieces: List[Piece], board: Board, broker: MessageBroker = None, ui=None, validate_board=True):
        # Validate board configuration before initialization (can be disabled for tests)
        if validate_board and not self._validate(pieces):
            raise InvalidBoard("Invalid board configuration: missing kings or duplicate positions")
            
        self.pieces = pieces
        self.board = board
        self.curr_board = None
        self.user_input_queue = queue.Queue()
        self.piece_by_id = {p.id: p for p in pieces}
        self.pos: Dict[Tuple[int, int], List[Piece]] = defaultdict(list)
        self.START_NS = time.monotonic_ns()  # Use monotonic time for consistency
        self._time_factor = 1  
        self.kp1 = None
        self.kp2 = None
        self.kb_prod_1 = None
        self.kb_prod_2 = None
        self.selected_id_1: Optional[str] = None
        self.selected_id_2: Optional[str] = None  
        self.last_cursor1 = (0, 0)
        self.last_cursor2 = (0, 0)
        
        # Add support for event publishing
        self.broker = broker if broker else MessageBroker()
        self.event_publisher = GameEventPublisher(self.broker)
        
        # UI instance for rendering
        self.ui = ui
        
        # Support for new user interface
        self.ui = ui

    def game_time_ms(self) -> int:
        return self._time_factor * (time.monotonic_ns() - self.START_NS) // 1_000_000

    def clone_board(self) -> Board:
        return self.board.clone()

    def start_user_input_thread(self):

        # player 1 key‐map
        p1_map = {
            "up": "up", "down": "down", "left": "left", "right": "right",
            "enter": "select", "space": "select", "+": "jump"
        }
        # player 2 key‐map
        p2_map = {
            "w": "up", "s": "down", "a": "left", "d": "right",
            "f": "select", "space": "select", "g": "jump"
        }

        # create two processors with initial positions
        # Player 1 (white) starts at bottom (row 7), Player 2 (black) starts at top (row 0)
        self.kp1 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p1_map,
                                     initial_pos=(7, 0))  # White pieces start at bottom
        self.kp2 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p2_map,
                                     initial_pos=(0, 0))  # Black pieces start at top

        # **pass the player number** as the 4th argument!
        self.kb_prod_1 = KeyboardProducer(self,
                                          self.user_input_queue,
                                          self.kp1,
                                          player=1)
        self.kb_prod_2 = KeyboardProducer(self,
                                          self.user_input_queue,
                                          self.kp2,
                                          player=2)

        self.kb_prod_1.start()
        self.kb_prod_2.start()

    def _update_cell2piece_map(self):
        self.pos.clear()
        for p in self.pieces:
            self.pos[p.current_cell()].append(p)

    def _run_game_loop(self, num_iterations=None, is_with_graphics=True):
        it_counter = 0
        while not self._is_win():
            now = self.game_time_ms()

            for p in self.pieces:
                p.update(now)

            self._update_cell2piece_map()

            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)

            if is_with_graphics:
                self._draw()
                self._show()

            self._resolve_collisions()

            # for testing
            if num_iterations is not None:
                it_counter += 1
                if num_iterations <= it_counter:
                    return

    def run(self, num_iterations=None, is_with_graphics=True):
        # Publish game start event
        self.event_publisher.send(EventType.GAME_START, {
            "timestamp": self.game_time_ms(),
            "player_count": 2,
            "board_size": (self.board.H_cells, self.board.W_cells)
        })
        
        self.start_user_input_thread()
        start_ms = self.START_NS
        for p in self.pieces:
            p.reset(start_ms)

        self._run_game_loop(num_iterations, is_with_graphics)

        self._announce_win()
        if self.kb_prod_1:
            self.kb_prod_1.stop()
            self.kb_prod_2.stop()

    def _draw(self):
        self.curr_board = self.clone_board()
        for p in self.pieces:
            p.draw_on_board(self.curr_board, now_ms=self.game_time_ms())

        # overlay both players' cursors, but only log on change
        if self.kp1 and self.kp2:
            for player, kp, last in (
                    (1, self.kp1, 'last_cursor1'),
                    (2, self.kp2, 'last_cursor2')
            ):
                r, c = kp.get_cursor()
                # draw rectangle
                y1 = r * self.board.cell_H_pix
                x1 = c * self.board.cell_W_pix
                y2 = y1 + self.board.cell_H_pix - 1
                x2 = x1 + self.board.cell_W_pix - 1
                color = (0, 255, 0) if player == 1 else (255, 0, 0)
                self.curr_board.img.draw_rect(x1, y1, x2, y2, color)

                # only print if moved
                prev = getattr(self, last)
                if prev != (r, c):
                    logger.debug("Marker P%s moved to (%s, %s)", player, r, c)
                    setattr(self, last, (r, c))

    def _show(self):
        if self.ui:
            # Use new user interface
            self.ui.render_complete_ui(self.curr_board)
            self.ui.show()
        else:
            # Fallback to old interface
            self.curr_board.show()

    def _side_of(self, piece_id: str) -> str:
        return piece_id[1]

    def _process_input(self, cmd: Command):
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            logger.debug("Unknown piece id %s", cmd.piece_id)
            return

        # Store previous position and state to check for actual movement
        old_position = mover.current_cell()
        old_state_name = mover.state.name
        print(f"DEBUG: {cmd.piece_id} is at {old_position} in state {old_state_name} before processing command {cmd.type}")

        # Process the command - Piece.on_command() determines my_color internally
        mover.on_command(cmd, self.pos)
        
        # Check if piece actually moved or changed state meaningfully
        new_position = mover.current_cell()
        new_state_name = mover.state.name
        print(f"DEBUG: {cmd.piece_id} is at {new_position} in state {new_state_name} after processing command")
        
        # Publish event only if:
        # 1. Position actually changed, OR
        # 2. State changed to a movement state (move, jump) indicating valid command acceptance
        position_changed = old_position != new_position
        state_changed_to_movement = (old_state_name != new_state_name and 
                                   new_state_name in ["move", "jump"])
        
        if position_changed or state_changed_to_movement:
            print(f"DEBUG: Publishing move event for {cmd.piece_id} - valid action detected")
            self.event_publisher.send(EventType.PIECE_MOVED, cmd)
            logger.info(f"Valid action: {cmd.piece_id} {cmd.type} - pos change: {position_changed}, state change: {state_changed_to_movement}")
        else:
            print(f"DEBUG: No move event for {cmd.piece_id} - command rejected or ineffective")
            # Publish INVALID_MOVE event for rejected commands (especially move commands)
            if cmd.type == "move":
                print(f"DEBUG: Publishing INVALID_MOVE event for {cmd.piece_id}")
                self.event_publisher.send(EventType.INVALID_MOVE, {
                    "piece_id": cmd.piece_id,
                    "attempted_move": cmd.cells if hasattr(cmd, 'cells') else cmd.params,
                    "command": cmd,
                    "reason": "Move validation failed or command was ineffective"
                })
                logger.info(f"Invalid move attempted: {cmd.piece_id} {cmd.type}")
        
        logger.info(f"Processed command: {cmd} for piece {cmd.piece_id}")

    def _resolve_collisions(self):
        self._update_cell2piece_map()
        occupied = self.pos

        for cell, plist in occupied.items():
            if len(plist) < 2:
                continue

            logger.debug(f"Collision detected at {cell}: {[p.id for p in plist]}")

            # Choose the piece that most recently entered the square
            # But prioritize pieces that are actually moving over idle pieces
            moving_pieces = [p for p in plist if p.state.name != 'idle']
            if moving_pieces:
                winner = max(moving_pieces, key=lambda p: p.state.physics.get_start_ms())
                logger.debug(f"Winner (moving): {winner.id} (state: {winner.state.name})")
            else:
                # If no moving pieces, choose the most recent idle piece
                winner = max(plist, key=lambda p: p.state.physics.get_start_ms())
                logger.debug(f"Winner (idle): {winner.id} (state: {winner.state.name})")

            # Determine if captures allowed: default allow
            if not winner.state.can_capture():
                # Allow capture even for idle pieces to satisfy game rules
                pass

            # Remove every other piece that *can be captured*
            for p in plist:
                if p is winner:
                    continue
                if p.state.can_be_captured():
                    logger.debug(f"Checking if {p.id} can be captured (state: {p.state.name})")
                    
                    # Don't remove knights that are moving (they're jumping in the air)
                    if p.id.startswith(('NW', 'NB')) and p.state.name == 'move':
                        logger.debug(f"Knight {p.id} is moving (jumping) - not removing")
                        continue
                    # Don't remove pieces that are jumping (they're in the air)
                    if p.state.name == 'jump':
                        logger.debug(f"Piece {p.id} is jumping - not removing")
                        continue
                    # Don't remove pieces if the winner is jumping (winner is in the air)
                    if winner.state.name == 'jump':
                        logger.debug(f"Winner {winner.id} is jumping - not removing {p.id}")
                        continue
                    # Don't remove pieces if the winner is a knight moving (knight is jumping in the air)
                    if winner.id.startswith(('NW', 'NB')) and winner.state.name == 'move':
                        logger.debug(f"Winner knight {winner.id} is moving (jumping) - not removing {p.id}")
                        continue
                    
                    # Don't capture pieces of the same color (friendly pieces)
                    if winner.id[1] == p.id[1]:  # Same color (W/B)
                        logger.debug(f"Winner {winner.id} and {p.id} are same color - not capturing")
                        continue
                    
                    logger.info(f"CAPTURE: {winner.id} captures {p.id} at {cell}")
                    
                    # Publish capture event for score tracking
                    capture_data = {
                        "piece_id": p.id,
                        "captured_by": winner.id[1],  # Color (W/B) of capturing piece
                        "captured_at": cell
                    }
                    self.event_publisher.send(EventType.PIECE_CAPTURED, capture_data)
                    
                    self.pieces.remove(p)
                else:
                    logger.debug(f"Piece {p.id} cannot be captured (state: {p.state.name})")

    def _validate(self, pieces):
        """Ensure both kings present and no two pieces share a cell."""
        has_white_king = has_black_king = False
        seen_cells: dict[tuple[int, int], str] = {}
        for p in pieces:
            cell = p.current_cell()
            if cell in seen_cells:
                # No overlap allowed - any duplicate position is invalid
                return False
            else:
                seen_cells[cell] = p.id[1]
            if p.id.startswith("KW"):
                has_white_king = True
            elif p.id.startswith("KB"):
                has_black_king = True
        return has_white_king and has_black_king

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces if p.id.startswith(('KW', 'KB'))]
        has_win_condition = len(kings) < 2
        
        # Only declare victory if there's a win condition AND no pieces are actively moving/capturing
        if has_win_condition:
            # Check if no pieces are in active movement states (move, jump)
            # Allow pieces in other states like 'idle', 'short_rest', 'long_rest', etc.
            no_pieces_moving = all(p.state.name not in ['move', 'jump'] for p in self.pieces)
            
            if no_pieces_moving:
                print(f"DEBUG: Victory condition met - {len(kings)} kings remaining, no pieces moving")
                for p in self.pieces:
                    print(f"DEBUG: Piece {p.id} is in state {p.state.name}")
                return True
            else:
                # Wait for moving pieces to finish their movements
                moving_pieces = [p for p in self.pieces if p.state.name in ['move', 'jump']]
                print(f"DEBUG: Waiting for {len(moving_pieces)} pieces to finish moving: {[p.id for p in moving_pieces]}")
                return False
        
        return False

    def _announce_win(self):
        # Determine winner
        winner_color = 'Black' if any(p.id.startswith('KB') for p in self.pieces) else 'White'
        winner_piece = next((p for p in self.pieces if p.id.startswith('K')), None)
        winner_id = winner_piece.id if winner_piece else 'Unknown'
        
        # Get actual player name if UI is available
        winner_player_name = winner_color  # Default fallback
        if self.ui and hasattr(self.ui, 'player_names_manager'):
            if winner_color == 'White':
                winner_player_name = self.ui.player_names_manager.get_white_player_name()
            else:
                winner_player_name = self.ui.player_names_manager.get_black_player_name()
        
        text = f'{winner_player_name} wins!'
        logger.info(text)
        
        # Publish game end event with winner information
        self.event_publisher.send(EventType.GAME_END, {
            "winner": winner_id,
            "winner_color": winner_color,
            "winner_player_name": winner_player_name,
            "timestamp": self.game_time_ms(),
            "total_pieces_remaining": len(self.pieces)
        })
        
        # Give time for the victory message to display before the game closes
        # Show the final game state with the victory message until it disappears
        if self.ui:
            # Display the final state with the victory message until the message is gone
            max_display_time = 5.0  # Maximum time to show victory message
            start_time = time.time()
            
            while True:
                # Check for timeout to prevent infinite loops in tests
                if time.time() - start_time > max_display_time:
                    break
                    
                # Keep updating the display to show the victory message
                self._draw()
                self._show()
                
                # Update message display and check if message is still visible
                if hasattr(self.ui, 'message_display'):
                    self.ui.message_display.update()
                    # Exit when message is no longer visible
                    if self.ui.message_display.current_message is None:
                        break
                else:
                    # Fallback: if no message display, wait 4 seconds
                    time.sleep(4.0)
                    break
                
                time.sleep(0.1)  # Small delay to avoid consuming too much CPU
