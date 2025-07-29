
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
import json

class CommandType(Enum):
    MOVE = "move"
    JUMP = "jump"
    CAPTURE = "capture"


@dataclass
class CommandData:
    timestamp: int          # ms since game start
    piece_id: str
    type: CommandType       # Type of command from CommandType enum
    params: List            # payload (e.g. ["e2", "e4"])

    def __str__(self) -> str:
        return f"CommandData(timestamp={self.timestamp}, piece_id={self.piece_id}, type={self.type.value}, params={self.params})"
    
    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'piece_id': self.piece_id,
            'type': self.type.value, 
            'params': self.params
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandData":
        return cls(
            timestamp=data['timestamp'],
            piece_id=data['piece_id'],
            type=CommandType(data['type']),  # Convert string back to enum
            params=data['params']
        )

    def clone(self) -> "CommandData":
        return CommandData(
            timestamp=self.timestamp,
            piece_id=self.piece_id,
            type=self.type,
            params=self.params.copy()  # Shallow copy of params list
        )

    def is_valid_format(self) -> bool:
        return (
            isinstance(self.timestamp, int) and
            isinstance(self.piece_id, str) and
            isinstance(self.type, CommandType) and  # Check for CommandType enum
            isinstance(self.params, list) and
            self.timestamp >= 0 and
            len(self.piece_id) > 0
        )

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json_string(cls, json_str: str) -> "CommandData":
        data = json.loads(json_str)
        return cls.from_dict(data)


class WebSocketMessage:
    
    def __init__(self, message_type: str, command_data: CommandData, 
                 client_id: str = "", session_id: str = ""):
        self.message_type = message_type  # "command", "response", "broadcast", etc.
        self.command_data = command_data
        self.client_id = client_id
        self.session_id = session_id
        self.timestamp = command_data.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'message_type': self.message_type,
            'command_data': self.command_data.to_dict(),
            'client_id': self.client_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp
        }

    def to_json_string(self) -> str:
        """Convert to JSON string for WebSocket transmission."""
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketMessage":
        """Create WebSocketMessage from dictionary."""
        command_data = CommandData.from_dict(data['command_data'])
        return cls(
            message_type=data['message_type'],
            command_data=command_data,
            client_id=data.get('client_id', ''),
            session_id=data.get('session_id', '')
        )

    @classmethod
    def from_json_string(cls, json_str: str) -> "WebSocketMessage":
        """Create WebSocketMessage from JSON string."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create_command_message(cls, command_data: CommandData, client_id: str, 
                             session_id: str = "") -> "WebSocketMessage":
        """Create a command message for client->server communication."""
        return cls("command", command_data, client_id, session_id)

    @classmethod
    def create_response_message(cls, command_data: CommandData, client_id: str,
                              session_id: str = "") -> "WebSocketMessage":
        """Create a response message for server->client communication."""
        return cls("response", command_data, client_id, session_id)

    @classmethod
    def create_broadcast_message(cls, command_data: CommandData, 
                               session_id: str = "") -> "WebSocketMessage":
        """Create a broadcast message for server->all clients communication."""
        return cls("broadcast", command_data, "", session_id)
