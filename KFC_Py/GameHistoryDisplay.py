from typing import Dict, List, Optional
from CommandHistoryManager import CommandHistoryManager
from ScoreManager import ScoreManager
from PlayerNamesManager import PlayerNamesManager
from MessageBroker import MessageBroker
from EventType import EventType
from Command import Command

class GameHistoryDisplay:
    """
    Class for managing history display of both players in the game.
    Manages two CommandHistoryManager instances and displays information in UI.
    """
    
    def __init__(self, broker: MessageBroker, player_names_manager: PlayerNamesManager = None):
        """
        Initialize display manager.
        
        Args:
            broker: MessageBroker for receiving events
            player_names_manager: Manager for player names (optional)
        """
        self.broker = broker
        
        # Create history managers for both players
        self.white_history = CommandHistoryManager("W", broker)
        self.black_history = CommandHistoryManager("B", broker)
        
        # Create score manager
        self.score_manager = ScoreManager(broker)
        
        # Create or use provided player names manager
        self.player_names_manager = player_names_manager if player_names_manager else PlayerNamesManager()
        
        # Display positions in interface (in pixels) - moved higher up
        self.white_display_area = {
            "x": 850,
            "y": 20,  # Moved up from 50
            "width": 300,
            "height": 280
        }
        
        self.black_display_area = {
            "x": 850,
            "y": 320,  # Moved up from 400
            "width": 300, 
            "height": 280
        }
    
    def get_white_player_history(self) -> List[str]:
        """
        Get white player history.
        
        Returns:
            List of white player moves (formatted strings)
        """
        return self.white_history.get_formatted_history()
    
    def get_black_player_history(self) -> List[str]:
        """
        Get black player history.
        
        Returns:
            List of black player moves (formatted strings)
        """
        return self.black_history.get_formatted_history()
    
    def get_formatted_display_text(self, player_color: str, available_height: int = 500) -> List[str]:
        """
        Get formatted text for display in UI.
        
        Args:
            player_color: Player color ("W" or "B")
            available_height: Available height in pixels for displaying moves
            
        Returns:
            List of text lines for display
        """
        if player_color == "W":
            history = self.white_history.get_formatted_history()
            title = self.player_names_manager.get_white_player_name()
            score = self.score_manager.get_white_score()
        else:
            history = self.black_history.get_formatted_history()
            title = self.player_names_manager.get_black_player_name()
            score = self.score_manager.get_black_score()
        
        # Just the player name without "Moves:"
        lines = [title]
        
        if not history:
            # Return title and score when no moves yet
            lines.append(f"Score: {score}")
            return lines
        
        # Calculate how many moves can fit in the display area dynamically
        # Assume each line takes about 20 pixels (matching GameUI.py), and we need space for title and score (2 lines)
        lines_per_pixel = 20  # Match the line_height in GameUI.py
        reserved_lines = 3  # title, score, and some margin - increased from 2 to 3
        max_lines_for_moves = max(1, (available_height // lines_per_pixel) - reserved_lines)
        
        # Show recent moves (dynamic based on available space)
        recent_moves = history[-max_lines_for_moves:] if len(history) > max_lines_for_moves else history
        
        for i, move_description in enumerate(recent_moves, 1):
            # If we're showing truncated history, adjust numbering
            if len(history) > max_lines_for_moves:
                move_number = len(history) - max_lines_for_moves + i
            else:
                move_number = i
            lines.append(f"{move_number:2d}. {move_description}")
        
        # Add indication if there are more moves (only if truncated)
        if len(history) > max_lines_for_moves:
            lines.append(f"... and {len(history) - max_lines_for_moves} more moves")
        
        # Add score at the bottom
        lines.append(f"Score: {score}")
        
        return lines
    
    def get_display_area(self, player_color: str) -> Dict[str, int]:
        """
        Get display area for specific player.
        
        Args:
            player_color: Player color ("W" or "B")
            
        Returns:
            Dictionary with area position and dimensions
        """
        if player_color == "W":
            return self.white_display_area.copy()
        else:
            return self.black_display_area.copy()
    
    def get_move_counts(self) -> Dict[str, int]:
        """
        Get number of moves for each player.
        
        Returns:
            Dictionary with move counts for each player
        """
        return {
            "white": self.white_history.get_move_count(),
            "black": self.black_history.get_move_count()
        }
    
    def get_scores(self) -> Dict[str, int]:
        """
        Get scores for both players.
        
        Returns:
            Dictionary with scores for each player
        """
        return self.score_manager.get_scores()
    
    def set_player_names(self, white_name: str, black_name: str):
        """
        Set player names.
        
        Args:
            white_name: Name for white player
            black_name: Name for black player
        """
        self.player_names_manager.set_player_names(white_name, black_name)
    
    def get_player_names(self) -> tuple[str, str]:
        """
        Get player names.
        
        Returns:
            tuple containing (white_player_name, black_player_name)
        """
        return (self.player_names_manager.get_white_player_name(),
                self.player_names_manager.get_black_player_name())
    
    def clear_all_history(self):
        """
        Clear all history for both players and reset scores.
        """
        self.white_history.clear_history()
        self.black_history.clear_history()
        self.score_manager.reset_scores()
    
    def print_full_history(self):
        """
        Print full history of both players to console with scores.
        """
        print("\n" + "="*60)
        print("Complete Game History")
        print("="*60)
        
        scores = self.get_scores()
        white_name = self.player_names_manager.get_white_player_name()
        black_name = self.player_names_manager.get_black_player_name()
        print(f"\nScores: {white_name} {scores['white']} - {scores['black']} {black_name}")
        
        print("\n" + self.white_history.get_history_as_table())
        print("\n" + self.black_history.get_history_as_table())
        
        counts = self.get_move_counts()
        print(f"\nSummary: {white_name} - {counts['white']} moves ({scores['white']} points)")
        print(f"         {black_name} - {counts['black']} moves ({scores['black']} points)")
        print("="*60)
