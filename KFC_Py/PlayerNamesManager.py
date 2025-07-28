"""
Player names management system for the chess game.
Handles player name input and storage with graphical interface.
"""

import cv2
import numpy as np
import pathlib

class PlayerNamesManager:
    """
    Class for managing player names and providing graphical input interface.
    """
    
    def __init__(self):
        """Initialize player names manager with default names."""
        self.white_player_name = "White Player"
        self.black_player_name = "Black Player"
        
        # UI settings for name input
        self.window_width = 800
        self.window_height = 600
        self.current_input = ""
        self.is_entering_white = True
        self.input_complete = False
        
        # Load background image
        self.background_img = None
        self._load_background_image()
        
        # Colors (BGR format for OpenCV) - Chess board style
        self.bg_color = (139, 69, 19)  # Saddle brown like chess board
        self.light_square_color = (240, 217, 181)  # Light chess square
        self.dark_square_color = (181, 136, 99)   # Dark chess square
        self.text_color = (255, 255, 255)
        self.input_bg_color = (50, 50, 50)
        self.white_player_color = (255, 255, 255)  # White
        self.black_player_color = (0, 0, 0)        # Black
    
    def _load_background_image(self):
        """Load the background image from the pieces folder."""
        try:
            # Try to find the background image
            pieces_folder = pathlib.Path("../pieces")
            background_path = pieces_folder / "background.jpg"
            
            if background_path.exists():
                self.background_img = cv2.imread(str(background_path))
                print(f"Loaded background image from: {background_path}")
            else:
                print(f"Background image not found at: {background_path}")
                self.background_img = None
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.background_img = None
    
    def get_player_names_from_gui(self) -> tuple[str, str]:
        """
        Get player names from graphical input interface.
        
        Returns:
            tuple containing (white_player_name, black_player_name)
        """
        cv2.namedWindow("Player Names Input", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Player Names Input", self.window_width, self.window_height)
        
        # Reset state
        self.white_player_name = ""
        self.black_player_name = ""
        self.current_input = ""
        self.is_entering_white = True
        self.input_complete = False
        
        while not self.input_complete:
            # Create image with background
            if self.background_img is not None:
                # Resize background to fit window
                img = cv2.resize(self.background_img, (self.window_width, self.window_height))
            else:
                # Fallback to solid color background
                img = np.full((self.window_height, self.window_width, 3), self.bg_color, dtype=np.uint8)
            
            # Draw UI
            self._draw_input_interface(img)
            
            # Show image
            cv2.imshow("Player Names Input", img)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            self._handle_key_input(key)
        
        cv2.destroyWindow("Player Names Input")
        
        # Set default names if empty
        if not self.white_player_name:
            self.white_player_name = "White Player"
        if not self.black_player_name:
            self.black_player_name = "Black Player"
        
        # Limit name length for display purposes
        self.white_player_name = self.white_player_name[:20] if len(self.white_player_name) > 20 else self.white_player_name
        self.black_player_name = self.black_player_name[:20] if len(self.black_player_name) > 20 else self.black_player_name
        
        return self.white_player_name, self.black_player_name
    
    def _draw_input_interface(self, img):
        """Draw the input interface on the image with game background."""
        # Add semi-transparent overlay for better text visibility
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.window_width, self.window_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
        
        # Title - simple and clean
        title = "Chess Game - Enter Player Names"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        title_x = (self.window_width - title_size[0]) // 2
        
        # Draw title with strong outline for better visibility
        cv2.putText(img, title, (title_x + 3, 83), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4)  # Black outline
        cv2.putText(img, title, (title_x, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)  # White text
        
        # Current player prompt
        if self.is_entering_white:
            prompt = "Enter name for White player:"
            prompt_color = self.white_player_color
        else:
            prompt = "Enter name for Black player:"
            prompt_color = self.black_player_color
        
        # Draw prompt with strong outline
        cv2.putText(img, prompt, (53, 203), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)  # Black outline
        cv2.putText(img, prompt, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, prompt_color, 2)
        
        # Draw input box with better contrast
        input_box_x, input_box_y = 50, 230
        input_box_w, input_box_h = 700, 50
        cv2.rectangle(img, (input_box_x, input_box_y), (input_box_x + input_box_w, input_box_y + input_box_h), (20, 20, 20), -1)
        cv2.rectangle(img, (input_box_x, input_box_y), (input_box_x + input_box_w, input_box_y + input_box_h), (255, 255, 255), 3)
        
        # Draw current input
        input_text = self.current_input + "|"  # Add cursor
        cv2.putText(img, input_text, (input_box_x + 10, input_box_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show already entered names with strong outlines
        if self.white_player_name:
            white_text = f"White Player: {self.white_player_name}"
            cv2.putText(img, white_text, (53, 353), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)  # Black outline
            cv2.putText(img, white_text, (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if self.black_player_name:
            black_text = f"Black Player: {self.black_player_name}"
            cv2.putText(img, black_text, (53, 383), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 3)  # White outline
            cv2.putText(img, black_text, (50, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 2)
        
        # Instructions with better visibility
        instructions = [
            "Instructions:",
            "- Type player name and press ENTER to confirm",
            "- Press ESC to use default names",
            "- Leave empty and press ENTER for default name"
        ]
        
        for i, instruction in enumerate(instructions):
            y_pos = 450 + i * 25
            cv2.putText(img, instruction, (52, y_pos + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)  # Black outline
            cv2.putText(img, instruction, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
    
    def _handle_key_input(self, key):
        """Handle keyboard input for name entry."""
        if key == 27:  # ESC key - use defaults and finish
            if not self.white_player_name:
                self.white_player_name = "White Player"
            if not self.black_player_name:
                self.black_player_name = "Black Player"
            self.input_complete = True
            
        elif key == 13 or key == 10:  # ENTER key
            if self.is_entering_white:
                # Save white player name
                self.white_player_name = self.current_input if self.current_input else "White Player"
                self.current_input = ""
                self.is_entering_white = False
            else:
                # Save black player name and finish
                self.black_player_name = self.current_input if self.current_input else "Black Player"
                self.input_complete = True
                
        elif key == 8:  # BACKSPACE
            if self.current_input:
                self.current_input = self.current_input[:-1]
                
        elif key != 255 and key < 128:  # Regular character
            char = chr(key)
            if char.isprintable() and len(self.current_input) < 20:
                self.current_input += char
    
    def get_player_names_from_input(self) -> tuple[str, str]:
        """
        Get player names from console input (backward compatibility).
        
        Returns:
            tuple containing (white_player_name, black_player_name)
        """
        print("=" * 50)
        print("🏁 Welcome to KFC Chess Game! 🏁")
        print("=" * 50)
        print()
        
        # Get white player name
        white_name = input("Enter name for White player (default: White Player): ").strip()
        if not white_name:
            white_name = "White Player"
        
        # Get black player name
        black_name = input("Enter name for Black player (default: Black Player): ").strip()
        if not black_name:
            black_name = "Black Player"
        
        # Limit name length for display purposes
        white_name = white_name[:20] if len(white_name) > 20 else white_name
        black_name = black_name[:20] if len(black_name) > 20 else black_name
        
        self.white_player_name = white_name
        self.black_player_name = black_name
        
        print()
        print(f"🎮 Game starting: {white_name} (White) vs {black_name} (Black)")
        print("=" * 50)
        print()
        
        return white_name, black_name
    
    def set_player_names(self, white_name: str, black_name: str):
        """
        Set player names directly (for programmatic use).
        
        Args:
            white_name: Name for white player
            black_name: Name for black player
        """
        self.white_player_name = white_name[:20] if len(white_name) > 20 else white_name
        self.black_player_name = black_name[:20] if len(black_name) > 20 else black_name
    
    def get_white_player_name(self) -> str:
        """Get white player name."""
        return self.white_player_name
    
    def get_black_player_name(self) -> str:
        """Get black player name."""
        return self.black_player_name
    
    def get_player_name_by_color(self, color: str) -> str:
        """
        Get player name by color.
        
        Args:
            color: Player color ("W" or "B")
            
        Returns:
            Player name
        """
        if color == "W":
            return self.white_player_name
        elif color == "B":
            return self.black_player_name
        else:
            return f"Player {color}"
