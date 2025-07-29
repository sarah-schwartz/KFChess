
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
import json

class CommandType(Enum):
    MOVE = "move"
    JUMP = "jump"
    CAPTURE = "capture"
    IDLE = "idle"

@dataclass
class Command:
    timestamp: int
    piece_id: str
    type: CommandType
    params: List

    def __str__(self) -> str:
        return f"Command(timestamp={self.timestamp}, piece_id={self.piece_id}, type={self.type.value}, params={self.params})"
    
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
    def from_dict(cls, data: Dict[str, Any]) -> "Command":
        return cls(
            timestamp=data['timestamp'],
            piece_id=data['piece_id'],
            type=CommandType(data['type']),
            params=data['params']
        )

    def clone(self) -> "Command":
        return Command(
            timestamp=self.timestamp,
            piece_id=self.piece_id,
            type=self.type,
            params=self.params.copy()
        )

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json_string(cls, json_str: str) -> "Command":
        data = json.loads(json_str)
        return cls.from_dict(data)


class WebSocketMessage:
    
    def __init__(self, message_type: str, command: Command, 
                 client_id: str = "", session_id: str = ""):
        self.message_type = message_type
        self.command = command
        self.client_id = client_id
        self.session_id = session_id
        self.timestamp = command.timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_type': self.message_type,
            'command_data': self.command.to_dict(),
            'client_id': self.client_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp
        }

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketMessage":
        command = Command.from_dict(data['command_data'])
        return cls(
            message_type=data['message_type'],
            command=command,
            client_id=data.get('client_id', ''),
            session_id=data.get('session_id', '')
        )

    @classmethod
    def from_json_string(cls, json_str: str) -> "WebSocketMessage":
        data = json.loads(json_str)
        return cls.from_dict(data)
