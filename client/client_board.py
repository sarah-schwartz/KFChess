from typing import Tuple, Optional, Dict, Any
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from board_data import BoardData
from img import Img

class ClientBoard:
    def __init__(self, board_data: BoardData, img: Optional[Any] = None):
        self.data = board_data
        self.img = img
        self._local_state_version = 0
        self._local_pieces = {}  
    
    @property
    def local_state_version(self) -> int:
        return self._local_state_version
    
    def update_from_server(self, server_state: Dict[str, Any]) -> bool:
        server_version = server_state.get('state_version', 0)
        if server_version > self._local_state_version:
            board_dict = server_state.get('board_data', {})
            self.data = BoardData.from_dict(board_dict)
            
            pieces = server_state.get('pieces_positions', {})
            self._local_pieces = pieces.copy()
            
            self._local_state_version = server_version
            return True
        return False
    
    def get_board_data(self) -> BoardData:
        return self.data.clone()
    
    def get_local_pieces(self) -> Dict[str, Tuple[int, int]]:
        return self._local_pieces.copy()
    
    def get_piece_position(self, piece_id: str) -> Optional[Tuple[int, int]]:
        return self._local_pieces.get(piece_id)
    
    def set_image(self, img: Any) -> None:
        self.img = img
    
    def show(self) -> None:
        self.img.show()
       
    def clone(self) -> "ClientBoard":
        img_copy = None
        if self.img and hasattr(self.img, 'copy'):
            img_copy = self.img.copy()
        
        cloned = ClientBoard(self.data.clone(), img_copy)
        cloned._local_state_version = self._local_state_version
        cloned._local_pieces = self._local_pieces.copy()
        return cloned
    
    def m_to_cell(self, pos_m: Tuple[float, float]) -> Tuple[int, int]:
        x_m, y_m = pos_m
        col = int(round(x_m / self.data.cell_W_m))
        row = int(round(y_m / self.data.cell_H_m))
        return row, col

    def cell_to_m(self, cell: Tuple[int, int]) -> Tuple[float, float]:
        r, c = cell
        return c * self.data.cell_W_m, r * self.data.cell_H_m

    def m_to_pix(self, pos_m: Tuple[float, float]) -> Tuple[int, int]:
        x_m, y_m = pos_m
        x_px = int(round(x_m / self.data.cell_W_m * self.data.cell_W_pix))
        y_px = int(round(y_m / self.data.cell_H_m * self.data.cell_H_pix))
        return x_px, y_px
   
    def pixel_to_cell(self, pixel_pos: Tuple[int, int]) -> Tuple[int, int]:
        x_px, y_px = pixel_pos
        x_m = (x_px / self.data.cell_W_pix) * self.data.cell_W_m
        y_m = (y_px / self.data.cell_H_pix) * self.data.cell_H_m
        return self.m_to_cell((x_m, y_m))
    
    def cell_to_pixel(self, cell: Tuple[int, int]) -> Tuple[int, int]:
        pos_m = self.cell_to_m(cell)
        return self.m_to_pix(pos_m)
        
    def get_cell_at_pixel(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        try:
            cell = self.pixel_to_cell((x, y))
            row, col = cell
            if (0 <= row < self.data.H_cells and 0 <= col < self.data.W_cells):
                return cell
        except:
            pass
        return None
    
    def get_piece_at_cell(self, row: int, col: int) -> Optional[str]:
        for piece_id, pos in self._local_pieces.items():
            if pos == (row, col):
                return piece_id
        return None
    
    def get_piece_at_pixel(self, x: int, y: int) -> Optional[str]:
        cell = self.get_cell_at_pixel(x, y)
        if cell:
            return self.get_piece_at_cell(cell[0], cell[1])
        return None
   
    def get_state_for_server(self) -> Dict[str, Any]:
        return {
            'board_data': self.data.to_dict(),
            'pieces_positions': self._local_pieces.copy(),
            'local_version': self._local_state_version
        }
    
    def to_json_string(self) -> str:
        import json
        return json.dumps(self.get_state_for_server())
    
    @classmethod
    def create_from_server_state(cls, server_state: Dict[str, Any], img: Optional[Any] = None) -> "ClientBoard":
        board_dict = server_state.get('board_data', {})
        board_data = BoardData.from_dict(board_dict)
        
        client_board = cls(board_data, img)
        client_board.update_from_server(server_state)
        return client_board
    
    @classmethod
    def from_json_string(cls, json_str: str, img: Optional[Any] = None) -> "ClientBoard":
        import json
        state_data = json.loads(json_str)
        return cls.create_from_server_state(state_data, img)
    
