from dataclasses import dataclass
from typing import Tuple, Dict, Any
import json

@dataclass
class BoardData:
    cell_H_pix: int  
    cell_W_pix: int  
    W_cells: int     
    H_cells: int    
    cell_H_m: float = 1.0  
    cell_W_m: float = 1.0  

    def clone(self) -> "BoardData":
        return BoardData(
            self.cell_H_pix, self.cell_W_pix,
            self.W_cells, self.H_cells,
            self.cell_H_m, self.cell_W_m
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'cell_H_pix': self.cell_H_pix,
            'cell_W_pix': self.cell_W_pix,
            'W_cells': self.W_cells,
            'H_cells': self.H_cells,
            'cell_H_m': self.cell_H_m,
            'cell_W_m': self.cell_W_m
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BoardData":
        return cls(
            cell_H_pix=data['cell_H_pix'],
            cell_W_pix=data['cell_W_pix'],
            W_cells=data['W_cells'],
            H_cells=data['H_cells'],
            cell_H_m=data.get('cell_H_m', 1.0),
            cell_W_m=data.get('cell_W_m', 1.0)
        )

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json_string(cls, json_str: str) -> "BoardData":
        data = json.loads(json_str)
        return cls.from_dict(data)
