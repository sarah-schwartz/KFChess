import pathlib
import cv2
from typing import Dict, List, Tuple, Optional
from img import Img
from Board import Board
from Game import Game
import logging

logger = logging.getLogger(__name__)


class GameUI:
    """
    Enhanced Game UI class that handles the visual display of the chess game
    including background image, player scores, and move history.
    """
    
    def __init__(self, game: Game, pieces_folder: pathlib.Path):
        self.game = game
        self.pieces_folder = pieces_folder
        self.background_img = None
        self.ui_width = 1200  # Total UI width
        self.ui_height = 800  # Total UI height
        self.board_size = 512  # Board display size (8x8 cells * 64px)
        self.sidebar_width = 300  # Width for scores and moves display
        
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
        """Draw the UI panels and borders."""
        # Two panels on the sides of the board, each quarter width
        # Panels are centered vertically and don't span full height
        
        panel_width = self.ui_width // 4  # Quarter width for each panel
        panel_height = self.board_size  # Same height as the board
        panel_y = (self.ui_height - panel_height) // 2  # Center vertically
        
        # Player 1 panel (left side) - just border, no fill (transparent)
        cv2.rectangle(self.ui_canvas,
                     (0, panel_y),
                     (panel_width, panel_y + panel_height),
                     self.player1_color, 3)
        
        # Player 2 panel (right side) - just border, no fill (transparent)
        right_panel_x = self.ui_width - panel_width
        cv2.rectangle(self.ui_canvas,
                     (right_panel_x, panel_y),
                     (self.ui_width, panel_y + panel_height),
                     self.player2_color, 3)
    
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
        
        # List recent moves
        for i, move in enumerate(moves[-8:]):  # Show last 8 moves
            move_y = y + 120 + (i * 25)
            move_text = f"{len(moves) - 8 + i + 1}. {move}"
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
        
        # Draw player information on the sides - TEMPORARILY DISABLED
        # panel_width = self.ui_width // 4
        # self._draw_player_info(1, 20, self.ui_height // 2 - 100)   # Player 1 - left side
        # right_panel_x = self.ui_width - panel_width
        # self._draw_player_info(2, right_panel_x + 20, self.ui_height // 2 - 100)  # Player 2 - right side
        
        # Title removed as requested
    
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
    
    # Create a dummy game board for testing
    dummy_img = Img()
    dummy_img.img = np.zeros((512, 512, 3), dtype=np.uint8)
    dummy_board = Board(64, 64, 8, 8, dummy_img)
    
    # Create UI with sample data
    pieces_path = pathlib.Path("../pieces")
    ui = GameUI(None, pieces_path)  # None game for testing
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
