from queue import Queue
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from Command import Command
from Subscriber import Subscriber
from EventType import EventType
from MessageBroker import MessageBroker

class CommandHistoryManager(Subscriber):
    """
    Class for managing command history for a single player.
    Each player gets a separate instance of this class.
    """
    
    def __init__(self, player_color: str, broker: MessageBroker):
        """
        Initialize history manager for a specific player.
        
        Args:
            player_color: Player color ("W" or "B")
            broker: MessageBroker for receiving events
        """
        self.player_color = player_color
        self.broker = broker
        self.command_history: Queue = Queue()
        self.formatted_history: List[Dict[str, str]] = []
        
        # Subscribe to piece movement events
        self.broker.subscribe(EventType.PIECE_MOVED, self)
    
    def handle_event(self, event_type: EventType, data):
        """
        Handle events received from MessageBroker.
        
        Args:
            event_type: Type of event
            data: Event data (Command object)
        """
        if event_type == EventType.PIECE_MOVED and isinstance(data, Command):
            # Check if command belongs to current player
            if self._is_my_piece(data.piece_id):
                # Only record moves that are likely valid
                # (for now, record all move/jump commands as the game logic handles validation)
                if data.type in ["move", "jump"]:
                    self._add_command_to_history(data)
    
    def _is_my_piece(self, piece_id: str) -> bool:
        """
        Check if piece belongs to current player.
        
        Args:
            piece_id: Piece identifier (e.g. "KB", "PW" etc.)
            
        Returns:
            True if piece belongs to current player
        """
        if len(piece_id) < 2:
            return False
        return piece_id[1] == self.player_color
    
    def _add_command_to_history(self, command: Command):
        """
        Add command to history.
        
        Args:
            command: Command to add
        """
        # Add to queue
        self.command_history.put(command)
        
        # Create textual description of command, including the timestamp
        description = self._format_command_description_with_time(command)
        
        # Add to formatted list
        self.formatted_history.append({
            "description": description
        })
    
    def _format_command_description_with_time(self, command: Command) -> str:
        """
        Create textual description of command, prepended with a formatted timestamp.
        
        Args:
            command: Command to format
            
        Returns:
            Textual description of command with timestamp (e.g. "HH:MM:SS King: (x,y) -> (x,y)")
        """
        time_str = self._format_timestamp(command.timestamp)
        piece_type = self._get_piece_type_name(command.piece_id)
        
        if command.type == "move" and len(command.params) >= 2:
            from_pos = command.params[0]
            to_pos = command.params[1]
            return f"{time_str} {piece_type}: {from_pos} -> {to_pos}"
        elif command.type == "jump":
            if len(command.params) >= 2:
                # Jump with from -> to positions
                from_pos = command.params[0]
                to_pos = command.params[1]
                return f"{time_str} {piece_type}: jump {from_pos} -> {to_pos}"
            elif len(command.params) >= 1:
                # Jump with only current position
                pos = command.params[0]
                return f"{time_str} {piece_type}: jump at {pos}"
            else:
                # Jump without position info
                return f"{time_str} {piece_type}: jump"
        else:
            return f"{time_str} {piece_type}: {command.type}"

    def _format_command_description(self, command: Command) -> str:
        """
        Create textual description of command.
        
        Args:
            command: Command to format
            
        Returns:
            Textual description of command
        """
        piece_type = self._get_piece_type_name(command.piece_id)
        
        if command.type == "move" and len(command.params) >= 2:
            from_pos = command.params[0]
            to_pos = command.params[1]
            return f"{piece_type}: {from_pos} -> {to_pos}"
        elif command.type == "jump":
            if len(command.params) >= 2:
                # Jump with from -> to positions
                from_pos = command.params[0]
                to_pos = command.params[1]
                return f"{piece_type}: jump {from_pos} -> {to_pos}"
            elif len(command.params) >= 1:
                # Jump with only current position
                pos = command.params[0]
                return f"{piece_type}: jump at {pos}"
            else:
                # Jump without position info
                return f"{piece_type}: jump"
        else:
            return f"{piece_type}: {command.type}"
    
    def _get_piece_type_name(self, piece_id: str) -> str:
        """
        Convert piece identifier to readable name.
        
        Args:
            piece_id: Piece identifier
            
        Returns:
            Piece name in English
        """
        if len(piece_id) < 1:
            return "Unknown"
            
        piece_type = piece_id[0]
        type_names = {
            "K": "King",
            "Q": "Queen", 
            "R": "Rook",
            "B": "Bishop",
            "N": "Knight",
            "P": "Pawn"
        }
        
        return type_names.get(piece_type, f"Piece {piece_type}")
    
    def _format_timestamp(self, timestamp_ms: int) -> str:
        """
        Format timestamp for display as elapsed time from game start in HH:MM:SS format.
        
        Args:
            timestamp_ms: Time in milliseconds from game start
            
        Returns:
            Formatted time for display (HH:MM:SS showing elapsed time)
        """
        # Convert timestamp to seconds - handle both positive and negative values
        if timestamp_ms < 0:
            # If negative, use absolute value
            total_seconds = abs(timestamp_ms) // 1000
        else:
            total_seconds = timestamp_ms // 1000
            
        # Calculate hours, minutes, seconds from elapsed time
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        # Format as HH:MM:SS
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return time_str
    
    def get_formatted_history(self) -> List[str]:
        """
        Get formatted history list.
        
        Returns:
            List of commands with time and description
        """
        return [entry['description'] for entry in self.formatted_history]
    
    def get_history_as_table(self) -> str:
        """
        Get history as formatted table for display.
        
        Returns:
            String containing formatted table
        """
        if not self.formatted_history:
            return f"No history for player {self.player_color}"
        
        # Table header
        color_name = "White" if self.player_color == "W" else "Black"
        table = f"Move History - {color_name} Player\n"
        table += "=" * 50 + "\n"
        table += f"{'Time':<8} | {'Move Description':<35}\n"
        table += "-" * 50 + "\n"
        
        # Add rows
        for entry in self.formatted_history:
            table += f"{entry['description']}\n"
        
        return table
    
    def clear_history(self):
        """
        Clear all history.
        """
        # Clear queue
        while not self.command_history.empty():
            self.command_history.get()
        
        # Clear formatted list
        self.formatted_history.clear()
    
    def get_move_count(self) -> int:
        """
        Get number of moves made.
        
        Returns:
            Number of moves
        """
        return len(self.formatted_history)
