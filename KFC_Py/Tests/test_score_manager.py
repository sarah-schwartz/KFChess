#!/usr/bin/env python3
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import from KFC_Py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ScoreManager import ScoreManager
from MessageBroker import MessageBroker
from EventType import EventType


class TestScoreManager(unittest.TestCase):
    """Test ScoreManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.broker = MessageBroker()
        self.score_manager = ScoreManager(self.broker)
    
    def test_initialization(self):
        """Test ScoreManager initialization."""
        self.assertEqual(self.score_manager.white_score, 0)
        self.assertEqual(self.score_manager.black_score, 0)
        self.assertIsNotNone(self.score_manager.broker)
    
    def test_piece_values(self):
        """Test piece value constants."""
        expected_values = {
            "P": 1,  # Pawn
            "N": 3,  # Knight
            "B": 3,  # Bishop
            "R": 5,  # Rook
            "Q": 9,  # Queen
            "K": 0   # King
        }
        self.assertEqual(ScoreManager.PIECE_VALUES, expected_values)
    
    def test_white_captures_black_pawn(self):
        """Test white player capturing black pawn."""
        # Create capture event data in the correct format
        event_data = {
            'piece_id': 'PB1',  # Black pawn captured
            'captured_by': 'W'  # Captured by white
        }
        
        # Publish event through broker to trigger handling
        self.broker.publish(EventType.PIECE_CAPTURED, event_data)
        
        # White should get 1 point for capturing pawn
        self.assertEqual(self.score_manager.white_score, 1)
        self.assertEqual(self.score_manager.black_score, 0)
    
    def test_black_captures_white_queen(self):
        """Test black player capturing white queen."""
        # Create capture event data in the correct format
        event_data = {
            'piece_id': 'QW1',  # White queen captured
            'captured_by': 'B'  # Captured by black
        }
        
        # Publish event through broker to trigger handling
        self.broker.publish(EventType.PIECE_CAPTURED, event_data)
        
        # Black should get 9 points for capturing queen
        self.assertEqual(self.score_manager.black_score, 9)
        self.assertEqual(self.score_manager.white_score, 0)
    
    def test_multiple_captures(self):
        """Test multiple captures by both players."""
        # White captures black rook (5 points)
        event_data1 = {
            'piece_id': 'RB1',
            'captured_by': 'W'
        }
        
        # Black captures white knight (3 points)
        event_data2 = {
            'piece_id': 'NW1',
            'captured_by': 'B'
        }
        
        # White captures black bishop (3 points)
        event_data3 = {
            'piece_id': 'BB1',
            'captured_by': 'W'
        }
        
        # Process all captures through broker
        self.broker.publish(EventType.PIECE_CAPTURED, event_data1)
        self.broker.publish(EventType.PIECE_CAPTURED, event_data2)
        self.broker.publish(EventType.PIECE_CAPTURED, event_data3)
        
        # Check final scores
        self.assertEqual(self.score_manager.white_score, 8)  # 5 + 3
        self.assertEqual(self.score_manager.black_score, 3)  # 3
    
    def test_get_scores(self):
        """Test getting current scores."""
        # Add some points
        event_data = {
            'piece_id': 'QB1',  # Black queen captured
            'captured_by': 'W'  # Captured by white
        }
        
        # Publish event through broker
        self.broker.publish(EventType.PIECE_CAPTURED, event_data)
        
        # Get scores
        white_score = self.score_manager.get_white_score()
        black_score = self.score_manager.get_black_score()
        scores_dict = self.score_manager.get_scores()
        
        self.assertEqual(white_score, 9)
        self.assertEqual(black_score, 0)
        self.assertEqual(scores_dict['white'], 9)
        self.assertEqual(scores_dict['black'], 0)
    
    def test_reset_scores(self):
        """Test resetting scores to zero."""
        # Add some points first
        event_data = {
            'piece_id': 'PB1',  # Black pawn captured
            'captured_by': 'W'  # Captured by white
        }
        
        # Publish event through broker
        self.broker.publish(EventType.PIECE_CAPTURED, event_data)
        
        # Verify scores are not zero
        self.assertNotEqual(self.score_manager.white_score, 0)
        
        # Reset scores
        self.score_manager.reset_scores()
        
        # Verify scores are now zero
        self.assertEqual(self.score_manager.white_score, 0)
        self.assertEqual(self.score_manager.black_score, 0)
    
    def test_invalid_piece_type(self):
        """Test handling of invalid piece types."""
        # Try to capture piece with invalid type
        event_data = {
            'piece_id': 'XB1',  # Invalid piece type
            'captured_by': 'W'
        }
        
        # Publish event through broker
        self.broker.publish(EventType.PIECE_CAPTURED, event_data)
        
        # Scores should remain 0 for invalid piece
        self.assertEqual(self.score_manager.white_score, 0)
        self.assertEqual(self.score_manager.black_score, 0)


if __name__ == '__main__':
    unittest.main()
