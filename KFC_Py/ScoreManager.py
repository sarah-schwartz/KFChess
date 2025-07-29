from typing import Dict
from Subscriber import Subscriber
from EventType import EventType
from MessageBroker import MessageBroker

class ScoreManager(Subscriber):
    """
    Class for managing player scores based on captured pieces.
    Tracks points earned by each player when capturing opponent pieces.
    """
    
    # Point values for different pieces
    PIECE_VALUES = {
        "P": 1,  # Pawn
        "N": 3,  # Knight 
        "B": 3,  # Bishop
        "R": 5,  # Rook
        "Q": 9,  # Queen
        "K": 0   # King - typically not captured in regular play
    }
    
    def __init__(self, broker: MessageBroker):
        """
        Initialize score manager.
        
        Args:
            broker: MessageBroker for receiving capture events
        """
        self.broker = broker
        self.white_score = 0
        self.black_score = 0
        
        # Subscribe to piece capture events
        self.broker.subscribe(EventType.PIECE_CAPTURED, self)
    
    def handle_event(self, event_type: EventType, data):
        """
        Handle events received from MessageBroker.
        
        Args:
            event_type: Type of event
            data: Event data (captured piece info)
        """
        if event_type == EventType.PIECE_CAPTURED:
            self._handle_piece_captured(data)
    
    def _handle_piece_captured(self, captured_piece_data):
        """
        Handle piece capture event and update scores.
        
        Args:
            captured_piece_data: Information about captured piece
        """
        # Extract piece info - expect format: {"piece_id": "PB", "captured_by": "W"}
        if isinstance(captured_piece_data, dict):
            piece_id = captured_piece_data.get("piece_id", "")
            captured_by_color = captured_piece_data.get("captured_by", "")
        else:
            # Handle simple piece_id string format
            piece_id = str(captured_piece_data)
            # Determine who captured based on piece color (opposite of captured piece)
            if len(piece_id) >= 2:
                captured_piece_color = piece_id[1]
                captured_by_color = "W" if captured_piece_color == "B" else "B"
            else:
                return
        
        # Get piece type and value
        if len(piece_id) >= 1:
            piece_type = piece_id[0]
            piece_value = self.PIECE_VALUES.get(piece_type, 0)
            
            # Add points to capturing player
            if captured_by_color == "W":
                self.white_score += piece_value
                print(f"DEBUG: White player captured {piece_id} (+{piece_value} points) - Total: {self.white_score}")
            elif captured_by_color == "B":
                self.black_score += piece_value
                print(f"DEBUG: Black player captured {piece_id} (+{piece_value} points) - Total: {self.black_score}")
    
    def get_white_score(self) -> int:
        """Get white player's current score."""
        return self.white_score
    
    def get_black_score(self) -> int:
        """Get black player's current score."""
        return self.black_score
    
    def get_scores(self) -> Dict[str, int]:
        """Get scores for both players."""
        return {
            "white": self.white_score,
            "black": self.black_score
        }
    
    def reset_scores(self):
        """Reset scores for both players to 0."""
        self.white_score = 0
        self.black_score = 0
        print("DEBUG: Scores reset to 0")
