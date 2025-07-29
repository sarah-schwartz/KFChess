"""
Client-side Command implementation
Handles command creation, validation, and communication with server.
"""
from typing import List, Dict, Any, Optional, Callable
import sys
import os
import time

# Add shared directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

try:
    from command_data import CommandData, CommandType, WebSocketMessage
except ImportError:
    # Fallback for import issues
    pass


class ClientCommand:
    """Client-side command implementation with UI and communication functionality."""
    
    def __init__(self, command_data: Any):  # CommandData type
        """Initialize client command with command data."""
        self.data = command_data
        self.sent_to_server = False
        self.server_response: Optional[Dict[str, Any]] = None
        self.status = "created"  # created -> sent -> confirmed/rejected
    
    @property
    def timestamp(self) -> int:
        return self.data.timestamp
    
    @property
    def piece_id(self) -> str:
        return self.data.piece_id
    
    @property
    def type(self) -> Any:  # CommandType
        return self.data.type
    
    @property
    def params(self) -> List:
        return self.data.params
    
    def prepare_for_server(self) -> Dict[str, Any]:
        """Prepare command data for sending to server."""
        return self.data.to_dict()
    
    def to_websocket_message(self, client_id: str, session_id: str = "") -> str:
        """Create WebSocket JSON message for sending to server."""
        try:
            ws_message = WebSocketMessage.create_command_message(
                self.data, client_id, session_id
            )
            return ws_message.to_json_string()
        except:
            # Fallback to basic JSON
            import json
            return json.dumps(self.prepare_for_server())
    
    def mark_as_sent(self) -> None:
        """Mark command as sent to server."""
        self.sent_to_server = True
        self.status = "sent"
    
    def handle_server_response(self, response: Dict[str, Any]) -> bool:
        """
        Handle response from server.
        Returns True if command was accepted, False if rejected.
        """
        self.server_response = response
        
        if response.get('success', False):
            self.status = "confirmed"
            return True
        else:
            self.status = "rejected"
            return False
    
    def handle_websocket_response(self, ws_json: str) -> bool:
        """
        Handle WebSocket response from server.
        Returns True if command was accepted, False if rejected.
        """
        try:
            ws_message = WebSocketMessage.from_json_string(ws_json)
            # Extract response data from command params
            if ws_message.command_data.params:
                response_data = ws_message.command_data.params[0]
                return self.handle_server_response(response_data)
        except:
            # Fallback to basic JSON parsing
            import json
            try:
                response = json.loads(ws_json)
                return self.handle_server_response(response)
            except:
                pass
        
        return False
    
    def is_confirmed(self) -> bool:
        """Check if command was confirmed by server."""
        return self.status == "confirmed"
    
    def is_rejected(self) -> bool:
        """Check if command was rejected by server."""
        return self.status == "rejected"
    
    def get_error_message(self) -> Optional[str]:
        """Get error message if command was rejected."""
        if self.server_response:
            return self.server_response.get('error_message')
        return None
    
    def get_execution_result(self) -> Optional[Dict[str, Any]]:
        """Get execution result if command was confirmed."""
        if self.server_response:
            return self.server_response.get('execution_result')
        return None
    
    def get_command_data(self) -> Any:  # CommandData
        """Get the underlying command data."""
        return self.data
    
    def clone(self) -> "ClientCommand":
        """Create a copy of this client command."""
        cloned_data = self.data.clone()
        cloned_command = ClientCommand(cloned_data)
        cloned_command.sent_to_server = self.sent_to_server
        cloned_command.server_response = self.server_response.copy() if self.server_response else None
        cloned_command.status = self.status
        return cloned_command
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI display/logging."""
        result = self.data.to_dict()
        result.update({
            'sent_to_server': self.sent_to_server,
            'status': self.status,
            'server_response': self.server_response
        })
        return result
    
    # ──────────────────────────────────────────────────────────────
    # Factory methods for common commands
    # ──────────────────────────────────────────────────────────────
    
    @classmethod
    def create_move_command(cls, piece_id: str, from_pos: Any, to_pos: Any, 
                          timestamp: Optional[int] = None) -> Optional["ClientCommand"]:
        """Create a move command."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        try:
            command_data = CommandData(
                timestamp=timestamp,
                piece_id=piece_id,
                type=CommandType.MOVE,
                params=[from_pos, to_pos]
            )
            return cls(command_data)
        except:
            # Fallback if CommandType not available
            return None
    
    @classmethod
    def create_attack_command(cls, piece_id: str, target_pos: Any, 
                            timestamp: Optional[int] = None) -> Optional["ClientCommand"]:
        """Create an attack command."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        try:
            command_data = CommandData(
                timestamp=timestamp,
                piece_id=piece_id,
                type=CommandType.ATTACK,
                params=[target_pos]
            )
            return cls(command_data)
        except:
            return None
    
    @classmethod
    def create_jump_command(cls, piece_id: str, from_pos: Any, to_pos: Any,
                          timestamp: Optional[int] = None) -> Optional["ClientCommand"]:
        """Create a jump command."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        try:
            command_data = CommandData(
                timestamp=timestamp,
                piece_id=piece_id,
                type=CommandType.JUMP,
                params=[from_pos, to_pos]
            )
            return cls(command_data)
        except:
            return None
    
    @classmethod
    def create_castle_command(cls, king_id: str, side: str, 
                            timestamp: Optional[int] = None) -> Optional["ClientCommand"]:
        """Create a castle command."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        try:
            command_data = CommandData(
                timestamp=timestamp,
                piece_id=king_id,
                type=CommandType.CASTLE,
                params=[side]  # "kingside" or "queenside"
            )
            return cls(command_data)
        except:
            return None
    
    @classmethod
    def from_server_update(cls, server_data: Dict[str, Any]) -> Optional["ClientCommand"]:
        """Create client command from server update data."""
        try:
            command_data = CommandData.from_dict(server_data)
            return cls(command_data)
        except:
            return None

    @classmethod
    def from_websocket_broadcast(cls, ws_json: str) -> Optional["ClientCommand"]:
        """Create client command from WebSocket broadcast message."""
        try:
            ws_message = WebSocketMessage.from_json_string(ws_json)
            if ws_message.message_type == "broadcast":
                return cls(ws_message.command_data)
        except:
            # Fallback to basic JSON parsing
            import json
            try:
                data = json.loads(ws_json)
                return cls.from_server_update(data)
            except:
                pass
        
        return None


class CommandBuilder:
    """Helper class for building commands in the UI."""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        """Reset builder state."""
        self.piece_id = ""
        self.command_type = None
        self.params = []
        self.timestamp = None
    
    def set_piece(self, piece_id: str) -> "CommandBuilder":
        """Set the piece ID for the command."""
        self.piece_id = piece_id
        return self
    
    def set_type(self, command_type: Any) -> "CommandBuilder":  # CommandType
        """Set the command type."""
        self.command_type = command_type
        return self
    
    def add_param(self, param: Any) -> "CommandBuilder":
        """Add a parameter to the command."""
        self.params.append(param)
        return self
    
    def set_params(self, params: List[Any]) -> "CommandBuilder":
        """Set all parameters for the command."""
        self.params = params.copy()
        return self
    
    def set_timestamp(self, timestamp: int) -> "CommandBuilder":
        """Set custom timestamp (optional)."""
        self.timestamp = timestamp
        return self
    
    def build(self) -> Optional[ClientCommand]:
        """Build the command."""
        if not self.piece_id or not self.command_type:
            return None
        
        timestamp = self.timestamp or int(time.time() * 1000)
        
        try:
            command_data = CommandData(
                timestamp=timestamp,
                piece_id=self.piece_id,
                type=self.command_type,
                params=self.params
            )
            return ClientCommand(command_data)
        except:
            return None


class CommandHistory:
    """Manages command history for undo/redo functionality."""
    
    def __init__(self, max_history: int = 100):
        self.commands: List[ClientCommand] = []
        self.max_history = max_history
    
    def add_command(self, command: ClientCommand) -> None:
        """Add a command to history."""
        self.commands.append(command)
        
        # Keep history within limits
        if len(self.commands) > self.max_history:
            self.commands.pop(0)
    
    def get_recent_commands(self, count: int = 10) -> List[ClientCommand]:
        """Get the most recent commands."""
        return self.commands[-count:]
    
    def get_commands_by_piece(self, piece_id: str) -> List[ClientCommand]:
        """Get all commands for a specific piece."""
        return [cmd for cmd in self.commands if cmd.piece_id == piece_id]
    
    def get_commands_by_type(self, command_type: Any) -> List[ClientCommand]:  # CommandType
        """Get all commands of a specific type."""
        return [cmd for cmd in self.commands if cmd.type == command_type]
    
    def clear_history(self) -> None:
        """Clear all command history."""
        self.commands.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert history to dictionary for serialization."""
        return {
            'commands': [cmd.to_dict() for cmd in self.commands],
            'max_history': self.max_history
        }
