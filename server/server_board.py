from typing import Tuple, Optional, Dict, Any
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from board_data import BoardData

class ServerBoard:    
    def __init__(self, board_data: BoardData):
        self.data = board_data
        self._state_version = 0  
        self._pieces_positions = {} 
    
    @property
    def state_version(self) -> int:
        return self._state_version
    
    def get_board_data(self) -> BoardData:
        return self.data.clone()
    
    def update_board_data(self, new_data: BoardData) -> None:
        self.data = new_data
        self._state_version += 1
    
    def validate_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if not ((0 <= from_row < self.data.H_cells and 0 <= from_col < self.data.W_cells) and 
                (0 <= to_row < self.data.H_cells and 0 <= to_col < self.data.W_cells)):
            return False   
        if from_pos == to_pos:
            return False      
        return True
    
    def execute_move(self, piece_id: str, from_pos: Tuple[int, int], 
                    to_pos: Tuple[int, int]) -> bool:
        if not self.validate_move(from_pos, to_pos):
            return False
        self._pieces_positions[piece_id] = to_pos
        self._state_version += 1
        return True
    
    def get_piece_position(self, piece_id: str) -> Optional[Tuple[int, int]]:
        return self._pieces_positions.get(piece_id)
    
    def set_piece_position(self, piece_id: str, position: Tuple[int, int]) -> None:
        row, col = position
        if (0 <= row < self.data.H_cells and 0 <= col < self.data.W_cells):
            self._pieces_positions[piece_id] = position
            self._state_version += 1
    
    def remove_piece(self, piece_id: str) -> bool:
        if piece_id in self._pieces_positions:
            del self._pieces_positions[piece_id]
            self._state_version += 1
            return True
        return False
    
    def get_all_pieces(self) -> Dict[str, Tuple[int, int]]:
        return self._pieces_positions.copy()
    
    def get_state_for_client(self) -> Dict[str, Any]:
        return {
            'board_data': self.data.to_dict(),
            'pieces_positions': self._pieces_positions.copy(),
            'state_version': self._state_version
        }
    
    def update_from_client_state(self, client_state: Dict[str, Any]) -> bool:
        try:
            board_dict = client_state.get('board_data', {})
            self.data = BoardData.from_dict(board_dict)
            
            pieces = client_state.get('pieces_positions', {})
            self._pieces_positions = pieces.copy()
            
            self._state_version += 1
            return True
        except Exception:
            return False
    
    def to_json_string(self) -> str:
        import json
        return json.dumps(self.get_state_for_client())
    
    @classmethod
    def from_json_string(cls, json_str: str) -> "ServerBoard":
        import json
        state_data = json.loads(json_str)

        board_data = BoardData.from_dict(state_data['board_data'])
        server_board = cls(board_data)
        
        server_board._pieces_positions = state_data.get('pieces_positions', {})
        server_board._state_version = state_data.get('state_version', 0)
        
        return server_board
    
    @classmethod
    def create(cls, width: int, height: int, cell_size: int = 64) -> "ServerBoard":
        board_data = BoardData(
            cell_H_pix=cell_size,
            cell_W_pix=cell_size,
            W_cells=width,
            H_cells=height,
            cell_H_m=1.0,
            cell_W_m=1.0
        )
        return cls(board_data)
