#!/usr/bin/env python3
"""
Simple Victory Timing Test

Tests the core victory timing logic without pygame dependencies.
"""

import sys
import os
from unittest.mock import Mock

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_victory_timing_logic():
    """Test victory timing logic directly."""
    print("🧪 Testing Victory Timing Logic")
    print("=" * 40)
    
    try:
        # Import required modules
        from Game import Game
        from Board import Board
        
        # Create mock pieces
        def create_mock_piece(piece_id, state_name='idle'):
            piece = Mock()
            piece.id = piece_id
            piece.current_cell.return_value = (0, 0)
            
            state = Mock()
            state.name = state_name
            state.physics = Mock()
            state.physics.get_start_ms.return_value = 0
            piece.state = state
            
            piece.reset = Mock()
            piece.update = Mock()
            piece.draw_on_board = Mock()
            piece.on_command = Mock()
            
            return piece
        
        # Test Case 1: Victory with all pieces idle
        print("Test 1: Victory with all pieces idle")
        board = Board(8, 8, 64, 64)
        white_king = create_mock_piece("KW1", "idle")
        white_pawn = create_mock_piece("PW1", "idle")
        pieces = [white_king, white_pawn]
        
        game = Game(pieces, board, validate_board=False)
        result = game._is_win()
        print(f"  Result: {result} ✅" if result else f"  Result: {result} ❌")
        assert result == True, "Should declare victory when only one color remains and all pieces idle"
        
        # Test Case 2: No victory with moving pieces
        print("Test 2: No victory with moving pieces")
        white_pawn.state.name = 'move'  # Set pawn to moving
        
        result = game._is_win()
        print(f"  Result: {result} ✅" if not result else f"  Result: {result} ❌")
        assert result == False, "Should NOT declare victory while pieces are moving"
        
        # Test Case 3: No victory with both kings present
        print("Test 3: No victory with both kings present")
        black_king = create_mock_piece("KB1", "idle")
        game.pieces = [white_king, black_king, white_pawn]
        white_pawn.state.name = 'idle'  # Set pawn back to idle
        
        result = game._is_win()
        print(f"  Result: {result} ✅" if not result else f"  Result: {result} ❌")
        assert result == False, "Should NOT declare victory with both kings present"
        
        # Test Case 4: Victory allowed with resting pieces
        print("Test 4: Victory allowed with resting pieces")
        game.pieces = [white_king, white_pawn]  # Remove black king
        white_pawn.state.name = 'short_rest'  # Set pawn to resting
        
        result = game._is_win()
        print(f"  Result: {result} ✅" if result else f"  Result: {result} ❌")
        assert result == True, "Should declare victory even with resting pieces"
        
        print("\n🎉 All victory timing tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_constants():
    """Test that message constants are correctly defined."""
    print("\n🧪 Testing Message Constants")
    print("=" * 40)
    
    try:
        # Test constants exist and have correct values
        from MessageDisplay import GAME_START_MESSAGE, GAME_END_MESSAGE_TEMPLATE
        
        print(f"GAME_START_MESSAGE: '{GAME_START_MESSAGE}'")
        print(f"GAME_END_MESSAGE_TEMPLATE: '{GAME_END_MESSAGE_TEMPLATE}'")
        
        # Test start message
        expected_start = "Welcome to KFC Chess!"
        assert GAME_START_MESSAGE == expected_start, f"Expected '{expected_start}', got '{GAME_START_MESSAGE}'"
        print("  ✅ Game start message correct")
        
        # Test end message template
        expected_template = "{winner_color} Wins!"
        assert GAME_END_MESSAGE_TEMPLATE == expected_template, f"Expected '{expected_template}', got '{GAME_END_MESSAGE_TEMPLATE}'"
        print("  ✅ Game end message template correct")
        
        # Test template formatting
        white_msg = GAME_END_MESSAGE_TEMPLATE.format(winner_color="White")
        black_msg = GAME_END_MESSAGE_TEMPLATE.format(winner_color="Black")
        
        assert white_msg == "White Wins!", f"Expected 'White Wins!', got '{white_msg}'"
        assert black_msg == "Black Wins!", f"Expected 'Black Wins!', got '{black_msg}'"
        print("  ✅ Message template formatting works")
        
        print("\n🎉 All message constant tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Message constant test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_system():
    """Test basic event system functionality."""
    print("\n🧪 Testing Event System")
    print("=" * 40)
    
    try:
        from MessageBroker import MessageBroker
        from EventType import EventType
        
        # Test broker creation
        broker = MessageBroker()
        print("  ✅ MessageBroker created")
        
        # Test event types exist
        assert hasattr(EventType, 'GAME_START'), "GAME_START event type missing"
        assert hasattr(EventType, 'GAME_END'), "GAME_END event type missing"
        assert hasattr(EventType, 'INVALID_MOVE'), "INVALID_MOVE event type missing"
        print("  ✅ All required event types exist")
        
        # Test subscription
        class MockSubscriber:
            def __init__(self):
                self.received_events = []
            
            def handle_event(self, event_type, data):
                self.received_events.append((event_type, data))
        
        subscriber = MockSubscriber()
        broker.subscribe(EventType.GAME_START, subscriber)
        print("  ✅ Event subscription works")
        
        # Test event publishing
        test_data = {"test": "data"}
        broker.publish(EventType.GAME_START, test_data)
        
        assert len(subscriber.received_events) == 1, "Event not received"
        assert subscriber.received_events[0] == (EventType.GAME_START, test_data), "Event data incorrect"
        print("  ✅ Event publishing works")
        
        print("\n🎉 All event system tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Event system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all simplified tests."""
    print("🚀 Running Simplified Victory Timing and Message System Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Run each test
    tests = [
        test_victory_timing_logic,
        test_message_constants,
        test_event_system
    ]
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Victory timing and message system are working correctly!")
        print("\nKey Features Verified:")
        print("  ✅ Victory detection waits for pieces to finish moving")
        print("  ✅ Victory is declared when all movement stops")
        print("  ✅ Message constants are correctly defined")
        print("  ✅ Event system functions properly")
        print("\nThe system should now:")
        print("  - Show 'Welcome to KFC Chess!' at game start")
        print("  - Wait for pieces to finish moving before declaring victory")
        print("  - Show '{Color} Wins!' and wait 5 seconds before closing")
        return True
    else:
        print("🚨 SOME TESTS FAILED! Please check the errors above.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
