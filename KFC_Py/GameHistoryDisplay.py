from typing import Dict, List, Optional
from CommandHistoryManager import CommandHistoryManager
from ScoreManager import ScoreManager
from MessageBroker import MessageBroker
from EventType import EventType
from Command import Command

class GameHistoryDisplay:
    """
    Class for managing history display of both players in the game.
    Manages two CommandHistoryManager instances and displays information in UI.
    """
    
    def __init__(self, broker: MessageBroker):
        """
        Initialize display manager.
        
        Args:
            broker: MessageBroker for receiving events
        """
        self.broker = broker
        
        # Create history managers for both players
        self.white_history = CommandHistoryManager("W", broker)
        self.black_history = CommandHistoryManager("B", broker)
        
        # Create score manager
        self.score_manager = ScoreManager(broker)
        
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
    
    def get_formatted_display_text(self, player_color: str) -> List[str]:
        """
        Get formatted text for display in UI.
        
        Args:
            player_color: Player color ("W" or "B")
            
        Returns:
            List of text lines for display
        """
        if player_color == "W":
            history = self.white_history.get_formatted_history()
            title = "White Player"
            score = self.score_manager.get_white_score()
        else:
            history = self.black_history.get_formatted_history()
            title = "Black Player"
            score = self.score_manager.get_black_score()
        
        lines = [f"{title} Moves:"]
        
        if not history:
            # Return title and score when no moves yet
            lines.append(f"Score: {score}")
            return lines
        
        # Show recent moves (up to 8 to make room for score line at bottom)
        recent_moves = history[-8:] if len(history) > 8 else history
        
        for i, move_description in enumerate(recent_moves, 1):
            lines.append(f"{i:2d}. {move_description}")
        
        # Add indication if there are more moves
        if len(history) > 8:
            lines.append(f"... and {len(history) - 8} more moves")
        
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
        print(f"\nScores: White {scores['white']} - {scores['black']} Black")
        
        print("\n" + self.white_history.get_history_as_table())
        print("\n" + self.black_history.get_history_as_table())
        
        counts = self.get_move_counts()
        print(f"\nSummary: White player - {counts['white']} moves ({scores['white']} points)")
        print(f"         Black player - {counts['black']} moves ({scores['black']} points)")
        print("="*60)
