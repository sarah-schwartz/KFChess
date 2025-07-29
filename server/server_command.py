"""
Server-side Command implementation
Handles command validation, execution, and game state management.
"""
from typing import List, Dict, Any, Optional
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from command_data import CommandData, CommandType, WebSocketMessage


class ServerCommand:
    
    def __init__(self, command_data: CommandData):
        self.data = command_data
        self.executed = False
        self.execution_result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
    
    @property
    def timestamp(self) -> int:
        return self.data.timestamp
    
    @property
    def piece_id(self) -> str:
        return self.data.piece_id
    
    @property
    def type(self) -> CommandType:
        return self.data.type
    
    @property
    def params(self) -> List:
        return self.data.params
    
    def validate_command(self, game_state: Dict[str, Any]) -> bool:
        if not self.data.is_valid_format():
            self.error_message = "Invalid command format"
            return False
        
        # Check if piece exists in game state
        pieces = game_state.get('pieces_positions', {})
        if self.piece_id not in pieces:
            self.error_message = f"Piece {self.piece_id} not found"
            return False
        
        # Validate based on command type
        if self.type == CommandType.MOVE:
            return self._validate_move_command(game_state)
        elif self.type == CommandType.ATTACK:
            return self._validate_attack_command(game_state)
        elif self.type == CommandType.CASTLE:
            return self._validate_castle_command(game_state)
        elif self.type == CommandType.JUMP:
            return self._validate_jump_command(game_state)
        # Add more validation for other command types
        
        return True
    
    def _validate_move_command(self, game_state: Dict[str, Any]) -> bool:
        """Validate move command specific logic."""
        if len(self.params) < 2:
            self.error_message = "Move command requires 'from' and 'to' positions"
            return False
        
        from_pos = tuple(self.params[0]) if isinstance(self.params[0], list) else self.params[0]
        to_pos = tuple(self.params[1]) if isinstance(self.params[1], list) else self.params[1]
        
        # Check if source position matches piece's current position
        pieces = game_state.get('pieces_positions', {})
        current_pos = pieces.get(self.piece_id)
        
        if current_pos != from_pos:
            self.error_message = f"Piece {self.piece_id} is not at position {from_pos}"
            return False
        
        # Add more move-specific validation logic here
        return True
    
    def _validate_attack_command(self, game_state: Dict[str, Any]) -> bool:
        if len(self.params) < 1:
            self.error_message = "Attack command requires target position"
            return False
        return True
    
    
    def _validate_jump_command(self, game_state: Dict[str, Any]) -> bool:
        """Validate jump command specific logic."""
        if len(self.params) < 2:
            self.error_message = "Jump command requires 'from' and 'to' positions"
            return False
        
        # Add jump-specific validation logic here
        return True
    
    def execute(self, game_state: Dict[str, Any]) -> bool:
        """
        Execute the command and modify game state.
        Returns True if execution was successful, False otherwise.
        """
        if not self.validate_command(game_state):
            return False
        
        try:
            if self.type == CommandType.MOVE:
                self.execution_result = self._execute_move(game_state)
            elif self.type == CommandType.ATTACK:
                self.execution_result = self._execute_attack(game_state)
            elif self.type == CommandType.CASTLE:
                self.execution_result = self._execute_castle(game_state)
            elif self.type == CommandType.JUMP:
                self.execution_result = self._execute_jump(game_state)
            # Add more execution logic for other command types
            
            self.executed = True
            return True
            
        except Exception as e:
            self.error_message = str(e)
            return False
    
    def _execute_move(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute move command."""
        from_pos = tuple(self.params[0]) if isinstance(self.params[0], list) else self.params[0]
        to_pos = tuple(self.params[1]) if isinstance(self.params[1], list) else self.params[1]
        
        # Update piece position in game state
        pieces = game_state.get('pieces_positions', {})
        pieces[self.piece_id] = to_pos
        
        result = {
            'type': 'move_executed',
            'piece_id': self.piece_id,
            'from': from_pos,
            'to': to_pos,
            'timestamp': int(time.time() * 1000)
        }
        
        return result
    
    def _execute_attack(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute attack command."""
        target_pos = tuple(self.params[0]) if isinstance(self.params[0], list) else self.params[0]
        
        # Find target piece at position
        pieces = game_state.get('pieces_positions', {})
        target_piece = None
        for piece_id, pos in pieces.items():
            if pos == target_pos:
                target_piece = piece_id
                break
        
        result = {
            'type': 'attack_executed',
            'attacker_id': self.piece_id,
            'target_pos': target_pos,
            'target_piece': target_piece,
            'timestamp': int(time.time() * 1000)
        }
        
        # Remove target piece if found
        if target_piece:
            del pieces[target_piece]
            result['captured'] = True
        else:
            result['captured'] = False
        
        return result
    
    def _execute_castle(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute castle command."""
        side = self.params[0] if self.params else "kingside"
        
        result = {
            'type': 'castle_executed',
            'king_id': self.piece_id,
            'side': side,
            'timestamp': int(time.time() * 1000)
        }
        
        return result
    
    def _execute_jump(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute jump command."""
        from_pos = tuple(self.params[0]) if isinstance(self.params[0], list) else self.params[0]
        to_pos = tuple(self.params[1]) if isinstance(self.params[1], list) else self.params[1]
        
        # Update piece position in game state
        pieces = game_state.get('pieces_positions', {})
        pieces[self.piece_id] = to_pos
        
        result = {
            'type': 'jump_executed',
            'piece_id': self.piece_id,
            'from': from_pos,
            'to': to_pos,
            'timestamp': int(time.time() * 1000)
        }
        
        return result
    
    def get_command_data(self) -> CommandData:
        """Get the underlying command data."""
        return self.data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        result = self.data.to_dict()
        result.update({
            'executed': self.executed,
            'execution_result': self.execution_result,
            'error_message': self.error_message
        })
        return result
    
    def to_websocket_response(self, client_id: str, session_id: str = "") -> str:
        """Create WebSocket response JSON string."""
        response_data = {
            'success': self.executed and self.error_message is None,
            'command_data': self.data.to_dict(),
            'execution_result': self.execution_result,
            'error_message': self.error_message
        }
        
        # Create response command data
        response_command = CommandData(
            timestamp=int(time.time() * 1000),
            piece_id=self.piece_id,
            type=self.type,
            params=[response_data]  # Wrap response in params
        )
        
        # Create WebSocket message
        ws_message = WebSocketMessage.create_response_message(
            response_command, client_id, session_id
        )
        
        return ws_message.to_json_string()

    def to_websocket_broadcast(self, session_id: str = "") -> str:
        """Create WebSocket broadcast JSON string for all clients."""
        if not self.executed or self.execution_result is None:
            return ""
        
        # Create broadcast command data with execution result
        broadcast_command = CommandData(
            timestamp=int(time.time() * 1000),
            piece_id=self.piece_id,
            type=self.type,
            params=[self.execution_result]  # Broadcast the execution result
        )
        
        # Create WebSocket message
        ws_message = WebSocketMessage.create_broadcast_message(
            broadcast_command, session_id
        )
        
        return ws_message.to_json_string()

    @classmethod
    def from_websocket_message(cls, ws_json: str) -> "ServerCommand":
        """Create server command from WebSocket JSON message."""
        ws_message = WebSocketMessage.from_json_string(ws_json)
        return cls(ws_message.command_data)
    
    @classmethod
    def from_client_command(cls, client_data: Dict[str, Any]) -> "ServerCommand":
        """Create server command from client command data."""
        command_data = CommandData.from_dict(client_data)
        return cls(command_data)
    
    @classmethod
    def create_system_command(cls, command_type: CommandType, piece_id: str, 
                            params: List, timestamp: Optional[int] = None) -> "ServerCommand":
        """Create a system-generated command."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        command_data = CommandData(
            timestamp=timestamp,
            piece_id=piece_id,
            type=command_type,
            params=params
        )
        return cls(command_data)
