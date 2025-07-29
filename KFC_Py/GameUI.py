import pathlib
import cv2
from typing import Dict, List, Tuple, Optional
from img import Img
from Board import Board
from Game import Game
from GameHistoryDisplay import GameHistoryDisplay
from PlayerNamesManager import PlayerNamesManager
from MessageBroker import MessageBroker
from MessageDisplay import MessageDisplay
import logging

logger = logging.getLogger(__name__)


class GameUI:
    """
    Enhanced Game UI class that handles the visual display of the chess game
    including background image, player scores, and move history.
    """
    
    def __init__(self, game, pieces_folder: pathlib.Path, broker: MessageBroker, player_names_manager: PlayerNamesManager = None):
        self.game = game
        self.pieces_folder = pieces_folder
        self.broker = broker
        
        # Create history display manager with names manager
        self.player_names_manager = player_names_manager if player_names_manager else PlayerNamesManager()
        self.history_display = GameHistoryDisplay(broker, self.player_names_manager)
        
        # Create message display system
        self.message_display = MessageDisplay(broker, screen_width=1200, screen_height=800)
        
        self.background_img = None
        self.ui_width = 1200  # Total UI width
        self.ui_height = 800  # Total UI height
        self.board_size = 600  # Board display size - increased from 512 to 600
        self.sidebar_width = 280  # Width for scores and moves display - reduced for better fit
        
        # Player data for UI display
        self.player1_moves: List[str] = []
        self.player2_moves: List[str] = []
        self.player1_score: int = 0
        self.player2_score: int = 0
        
        # UI colors (BGR format for OpenCV)
        self.bg_color = (40, 40, 40)  # Dark gray background
        self.text_color = (255, 255, 255)  # White text
        self.player1_color = (0, 255, 0)  # Green for player 1
        self.player2_color = (255, 0, 0)  # Blue for player 2 (BGR)
        self.panel_color = (60, 60, 60)  # Lighter gray for panels
        
        self._load_background()
        self._initialize_ui()
    
    def _load_background(self):
        """Load and resize the background image to fit the board."""
        background_path = self.pieces_folder / "background.jpg"
        
        if background_path.exists():
            try:
                self.background_img = Img()
                # Load background and resize to fit the board area
                self.background_img.read(background_path, 
                                       (self.board_size, self.board_size), 
                                       keep_aspect=False)
                logger.info(f"Background image loaded from {background_path}")
            except Exception as e:
                logger.error(f"Failed to load background image: {e}")
                self._create_default_background()
        else:
            logger.warning(f"Background image not found at {background_path}")
            self._create_default_background()
    
    def _create_default_background(self):
        """Create a default background if the image file is not found."""
        self.background_img = Img()
        # Create a simple checkered pattern as default
        import numpy as np
        default_bg = np.zeros((self.board_size, self.board_size, 3), dtype=np.uint8)
        
        # Create checkered pattern
        cell_size = self.board_size // 8
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    color = (240, 217, 181)  # Light squares
                else:
                    color = (181, 136, 99)   # Dark squares
                
                y1 = row * cell_size
                y2 = (row + 1) * cell_size
                x1 = col * cell_size
                x2 = (col + 1) * cell_size
                
                default_bg[y1:y2, x1:x2] = color
        
        self.background_img.img = default_bg
        logger.info("Created default checkered background")
    
    def _initialize_ui(self):
        """Initialize the complete UI layout."""
        # Create the main UI canvas with background image covering the entire window
        import numpy as np
        self.ui_canvas = np.zeros((self.ui_height, self.ui_width, 3), dtype=np.uint8)
        
        # Fill the entire canvas with the background image
        if self.background_img and self.background_img.img is not None:
            # Resize background to fit the entire UI canvas
            bg_resized = cv2.resize(self.background_img.img, (self.ui_width, self.ui_height))
            self.ui_canvas = bg_resized.copy()
        else:
            # Fallback to dark background if no background image
            self.ui_canvas = np.full((self.ui_height, self.ui_width, 3), 
                                    self.bg_color, dtype=np.uint8)
        
        # Draw the main panels
        self._draw_ui_panels()
    
    def _draw_ui_panels(self):
        """Draw the UI panels - areas for player information on the sides."""
        # These are just layout areas - no actual drawing needed
        # The player information will be drawn by _draw_player_info_with_history
        pass
    
    def update_board_with_background(self, board: Board):
        """Update the game board to include the original board image, not the background."""
        # Don't modify the board - keep the original board image as is
        # The background will be handled by the UI canvas
        return board
    
    def _overlay_board_on_background(self, background, board):
        """Overlay the board content on the background, showing board only where there's actual content."""
        import numpy as np
        
        # Convert images to proper format for processing
        bg = background.astype(np.float32)
        board_img = board.astype(np.float32)
        
        # Create a mask to detect where the board has actual content
        # We'll consider pixels that are significantly different from black as "content"
        gray_board = cv2.cvtColor(board.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        
        # Create a mask for board content:
        # - Chess pieces (usually colorful and bright)
        # - Board lines and elements
        # - Anything that's not pure black or very dark
        content_mask = gray_board > 15  # Threshold for detecting content
        
        # Also detect areas with color variations (not pure black/dark)
        # This helps detect subtle board elements
        hsv_board = cv2.cvtColor(board.astype(np.uint8), cv2.COLOR_BGR2HSV)
        saturation = hsv_board[:, :, 1]
        color_mask = saturation > 10  # Areas with some color
        
        # Combine masks: show board where there's content OR color
        final_mask = np.logical_or(content_mask, color_mask)
        
        # Convert to 3-channel mask
        mask_3d = np.stack([final_mask, final_mask, final_mask], axis=-1)
        
        # Apply the mask: board where there's content, background elsewhere
        result = np.where(mask_3d, board_img, bg)
        
        # Copy result back to background
        background[:] = result.astype(np.uint8)
    
    def add_player_move(self, player: int, move: str):
        """Add a move to the player's move history."""
        if player == 1:
            self.player1_moves.append(move)
            # Keep only last 10 moves for display
            if len(self.player1_moves) > 10:
                self.player1_moves.pop(0)
        elif player == 2:
            self.player2_moves.append(move)
            if len(self.player2_moves) > 10:
                self.player2_moves.pop(0)
        
        logger.debug(f"Player {player} move added: {move}")
    
    def update_player_score(self, player: int, score: int):
        """Update a player's score."""
        if player == 1:
            self.player1_score = score
        elif player == 2:
            self.player2_score = score
        
        logger.debug(f"Player {player} score updated: {score}")
    
    def _draw_player_info_with_history(self, player: int, x: int, y: int):
        """Draw player information panel with command history (without player name - shown separately)."""
        # Determine player color for MessageBroker
        player_color = "W" if player == 1 else "B"
        
        # Start display from the y position (player name is shown separately above board)
        # Add some space between name and moves section
        moves_start_y = y + 20  # Added extra space
        
        # Get history data with available height calculation
        # Calculate the actual available height based on the real panel position
        ui_height = self.ui_canvas.shape[0]  # Total UI height (800)
        moves_section_start = moves_start_y + 30  # Where moves actually start
        
        # Calculate realistic available height from the current position to bottom of screen
        # Leave some margin at the bottom for the score line
        available_height = ui_height - moves_section_start - 80  # Reserve 80px for score and margin
        
        # Make sure we have at least some reasonable space
        if available_height < 100:
            available_height = 200  # Minimum reasonable height
        
        history_lines = self.history_display.get_formatted_display_text(player_color, available_height)
        move_counts = self.history_display.get_move_counts()
        
        color = self.player1_color if player == 1 else self.player2_color
        
        # Move count
        move_count = move_counts["white"] if player == 1 else move_counts["black"]
        count_text = f"Moves: {move_count}"
        cv2.putText(self.ui_canvas, count_text, (x + 10, moves_start_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.text_color, 1, cv2.LINE_AA)
        
        # Display history - starts from line 2 since first line is player name (shown separately)
        display_lines = history_lines[1:] if len(history_lines) > 1 else []
        
        # Calculate maximum lines that can fit dynamically
        line_height = 20
        # Reserve space for the move count line and ensure score line is always visible
        max_display_lines = max(1, (available_height // line_height) - 1)  # -1 for moves count line
        
        # Always keep the score line if it exists (it's usually the last line)
        score_line = None
        if display_lines and display_lines[-1].startswith("Score:"):
            score_line = display_lines[-1]
            display_lines = display_lines[:-1]  # Remove score from display_lines temporarily
        
        # Display the moves, but leave room for the score
        lines_to_show = min(len(display_lines), max_display_lines - (1 if score_line else 0))
        
        for i, line in enumerate(display_lines[:lines_to_show]):
            line_y = moves_start_y + 30 + (i * line_height)
            # Make sure we don't draw beyond the screen
            if line_y > self.ui_height - 60:  # Leave more space at bottom for score
                break
            try:
                cv2.putText(self.ui_canvas, line, (x + 15, line_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)
            except:
                # Fallback if there's an issue with text
                cv2.putText(self.ui_canvas, f"Move {i+1}", (x + 15, line_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)
        
        # Always display the score line at the bottom if it exists
        if score_line:
            score_y = moves_start_y + 30 + (lines_to_show * line_height) + 10  # Add some spacing
            # Make sure score doesn't go off screen
            if score_y < self.ui_height - 30:
                cv2.putText(self.ui_canvas, score_line, (x + 15, score_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)  # Yellow color for score
    
    def _draw_large_player_names(self, board_x, board_y):
        """Draw large player names at the sides of the board at board level."""
        # Get player names
        white_name = self.player_names_manager.get_white_player_name()
        black_name = self.player_names_manager.get_black_player_name()
        
        # Colors for player names (BGR format)
        white_color = (255, 255, 255)  # White
        black_color = (0, 0, 0)        # Black
        
        # Font settings for large names
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 3
        
        # Position names at the same level as the board
        name_y = board_y + 30  # Same level as board top + a bit down
        
        # White player name (centered in left space)
        white_text_size = cv2.getTextSize(white_name, font, font_scale, thickness)[0]
        left_space_width = board_x - 20  # Space from left edge to board minus margin
        white_x = (left_space_width - white_text_size[0]) // 2  # Center in left space
        
        # Make sure white name fits on screen
        if white_x > 10:
            # Draw white player name with black outline for visibility
            cv2.putText(self.ui_canvas, white_name, (white_x + 2, name_y + 2), font, font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
            cv2.putText(self.ui_canvas, white_name, (white_x, name_y), font, font_scale, white_color, thickness, cv2.LINE_AA)
        
        # Black player name (centered in right space)
        black_text_size = cv2.getTextSize(black_name, font, font_scale, thickness)[0]
        right_space_start = board_x + self.board_size + 20  # Start of right space
        right_space_width = self.ui_width - right_space_start - 20  # Available space minus margin
        black_x = right_space_start + (right_space_width - black_text_size[0]) // 2  # Center in right space
        
        # Make sure black name fits on screen
        if black_x + black_text_size[0] < self.ui_width - 10:
            # Draw black player name with white outline for visibility
            cv2.putText(self.ui_canvas, black_name, (black_x + 2, name_y + 2), font, font_scale, (255, 255, 255), thickness + 1, cv2.LINE_AA)
            cv2.putText(self.ui_canvas, black_name, (black_x, name_y), font, font_scale, black_color, thickness, cv2.LINE_AA)
    
    def _draw_player_info(self, player: int, x: int, y: int):
        """Draw player information panel."""
        moves = self.player1_moves if player == 1 else self.player2_moves
        score = self.player1_score if player == 1 else self.player2_score
        color = self.player1_color if player == 1 else self.player2_color
        
        # Player title
        title = f"שחקן {player}"
        cv2.putText(self.ui_canvas, title, (x + 10, y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
        
        # Score
        score_text = f"ניקוד: {score}"
        cv2.putText(self.ui_canvas, score_text, (x + 10, y + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.text_color, 1, cv2.LINE_AA)
        
        # Moves header
        moves_header = "מהלכים אחרונים:"
        cv2.putText(self.ui_canvas, moves_header, (x + 10, y + 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.text_color, 1, cv2.LINE_AA)
        
        # List recent moves - calculate how many moves can fit in the available space
        moves_start_y = y + 120
        available_height = self.ui_height - moves_start_y - 20  # Leave 20px margin at bottom
        max_moves = max(1, available_height // 25)  # Each move takes 25px, minimum 1 move
        
        # Show the last moves that fit in the window
        moves_to_show = moves[-max_moves:] if len(moves) > max_moves else moves
        for i, move in enumerate(moves_to_show):
            move_y = moves_start_y + (i * 25)
            if move_y < self.ui_height - 10:  # Make sure we don't go off screen
                if len(moves) > max_moves:
                    move_text = f"{len(moves) - max_moves + i + 1}. {move}"
                else:
                    move_text = f"{i + 1}. {move}"
                cv2.putText(self.ui_canvas, move_text, (x + 15, move_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1, cv2.LINE_AA)
    
    def render_complete_ui(self, board: Board):
        """Render the complete UI including board and player information."""
        # Start with fresh UI canvas with background image
        import numpy as np
        
        # Place the game board in the center - the ENTIRE board image should show on top of background
        board_x = (self.ui_width - self.board_size) // 2
        board_y = (self.ui_height - self.board_size) // 2
        
        # First draw the background image covering the entire canvas
        if self.background_img and self.background_img.img is not None:
            # Resize background to fit the entire UI canvas
            bg_resized = cv2.resize(self.background_img.img, (self.ui_width, self.ui_height))
            self.ui_canvas = bg_resized.copy()
        else:
            # Fallback to dark background if no background image
            self.ui_canvas = np.full((self.ui_height, self.ui_width, 3), 
                                    self.bg_color, dtype=np.uint8)
        
        # Redraw panels (transparent ones) on top of background
        self._draw_ui_panels()
        
        # THEN place the board image on top of everything
        if board.img.img is not None:
            board_resized = cv2.resize(board.img.img, (self.board_size, self.board_size))
            
            # Handle different image formats (RGB vs RGBA)
            if board_resized.shape[2] == 4:  # RGBA image
                # Convert RGBA to RGB
                board_resized = cv2.cvtColor(board_resized, cv2.COLOR_RGBA2RGB)
            
            # Place the ENTIRE board image on top of the background
            self.ui_canvas[board_y:board_y + self.board_size, 
                          board_x:board_x + self.board_size] = board_resized
        
        # Draw player information on the sides - aligned with board top edge
        board_y = (self.ui_height - self.board_size) // 2  # Calculate board's top position
        board_x = (self.ui_width - self.board_size) // 2   # Calculate board's left position
        
        # Draw large player names at the sides of the board
        self._draw_large_player_names(board_x, board_y)
        
        # Calculate equal spacing for panels
        # Left panel - centered in the space between left edge and board
        left_panel_width = board_x - 40  # Leave 20px margin on each side
        left_panel_x = (board_x - left_panel_width) // 2
        
        # Right panel - centered in the space between board and right edge
        right_space_width = self.ui_width - (board_x + self.board_size) - 40  # Leave 20px margin on each side
        right_panel_x = board_x + self.board_size + (right_space_width - 250) // 2 + 20  # 250 is approx panel width
        
        # Position panels below the player names
        panel_start_y = board_y + 50  # Start panels below the player names
        self._draw_player_info_with_history(1, left_panel_x, panel_start_y)   # Player 1 - left side, centered
        self._draw_player_info_with_history(2, right_panel_x, panel_start_y)  # Player 2 - right side, centered
        self._draw_player_info_with_history(2, right_panel_x, panel_start_y)  # Player 2 - right side
        
        # Title removed as requested
        
        # Render game messages (start/end messages) on top of everything
        self._render_game_messages()
    
    def _render_game_messages(self):
        """Render game start/end messages overlaid on the UI."""
        # Update message display state
        self.message_display.update()
        
        current_message = self.message_display.get_current_message()
        if current_message:
            alpha = self.message_display.get_message_alpha()
            if alpha > 0.0:
                self._draw_message_overlay(current_message, alpha)
    
    def _draw_message_overlay(self, message: str, alpha: float):
        """Draw a message overlay with transparency effect."""
        import numpy as np
        
        # Create overlay
        overlay = self.ui_canvas.copy()
        
        # Message styling
        font = cv2.FONT_HERSHEY_DUPLEX
        font_scale = 2.0
        thickness = 3
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(message, font, font_scale, thickness)
        
        # Center the message
        text_x = (self.ui_width - text_width) // 2
        text_y = (self.ui_height + text_height) // 2
        
        # Create background rectangle
        padding = 40
        bg_x1 = text_x - padding
        bg_y1 = text_y - text_height - padding
        bg_x2 = text_x + text_width + padding
        bg_y2 = text_y + baseline + padding
        
        # Draw semi-transparent background
        cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
        
        # Draw border
        cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (255, 255, 255), 2)
        
        # Draw text with glow effect (multiple layers)
        # Glow layers
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            cv2.putText(overlay, message, (text_x + offset[0], text_y + offset[1]),
                       font, font_scale, (50, 50, 50), thickness + 2, cv2.LINE_AA)
        
        # Main text
        cv2.putText(overlay, message, (text_x, text_y),
                   font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        
        # Blend overlay with original canvas using alpha
        alpha_int = int(alpha * 255)
        cv2.addWeighted(overlay, alpha, self.ui_canvas, 1 - alpha, 0, self.ui_canvas)
    
    def show(self):
        """Display the complete UI."""
        cv2.imshow("KFC Chess Game", self.ui_canvas)
        
        # Handle ESC key for graceful exit
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC key
            raise KeyboardInterrupt("ESC pressed - exiting game")
    
    def simulate_sample_data(self):
        """Add some sample data for testing the UI display."""
        # Sample moves for both players
        sample_moves_p1 = ["e2-e4", "Nf3", "Bc4", "0-0", "d3"]
        sample_moves_p2 = ["e7-e5", "Nc6", "Nf6", "d6", "Be7"]
        
        for move in sample_moves_p1:
            self.add_player_move(1, move)
        
        for move in sample_moves_p2:
            self.add_player_move(2, move)
        
        # Sample scores
        self.update_player_score(1, 150)
        self.update_player_score(2, 130)


# Integration functions to be used with the existing Game class

def enhance_game_with_ui(game: Game, pieces_folder: pathlib.Path) -> GameUI:
    """
    Create and attach a GameUI to an existing Game instance.
    Returns the GameUI instance for further manipulation.
    """
    game_ui = GameUI(game, pieces_folder)
    
    # Store references to original methods
    original_draw = game._draw
    original_show = game._show
    
    def enhanced_draw():
        # First, call the original draw logic to render pieces on the board
        original_draw()
        
        # Then enhance the board with background while preserving the pieces
        if hasattr(game, 'curr_board') and game.curr_board:
            game.curr_board = game_ui.update_board_with_background(game.curr_board)
    
    def enhanced_show():
        # Render the complete UI instead of just showing the board
        if hasattr(game, 'curr_board') and game.curr_board:
            game_ui.render_complete_ui(game.curr_board)
            game_ui.show()
        else:
            # Fallback to original show if no current board
            original_show()
    
    # Replace the game's draw and show methods
    game._draw = enhanced_draw
    game._show = enhanced_show
    
    return game_ui


# Example usage and testing function
def test_ui_display():
    """Test function to display the UI with sample data."""
    import numpy as np
    from Board import Board
    from MessageBroker import MessageBroker
    
    # Create a dummy game board for testing
    dummy_img = Img()
    dummy_img.img = np.zeros((512, 512, 3), dtype=np.uint8)
    dummy_board = Board(64, 64, 8, 8, dummy_img)
    
    # Create MessageBroker for UI
    broker = MessageBroker()
    
    # Create UI with sample data
    pieces_path = pathlib.Path("../pieces")
    ui = GameUI(None, pieces_path, broker)  # Include broker parameter
    ui.simulate_sample_data()
    ui.render_complete_ui(dummy_board)
    
    print("Displaying UI test... Press ESC to exit")
    while True:
        ui.show()
        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC
            break
    
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Test the UI
    test_ui_display()
