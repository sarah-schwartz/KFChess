
import logging
from GameFactory import create_game_with_history
from GraphicsFactory import ImgFactory

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create game with new system including sound effects and message display
    game, ui, history_display, broker, sound_manager, message_display = create_game_with_history("../pieces", ImgFactory())
    
    # Print message about new system activation
    print("Command history management system activated!")
    print("Sound effects system activated!")
    print("Message display system activated!")
    print("History will be displayed in real-time in the UI.")
    
    # Run the game
    game.run()
    
    # Display game history summary at the end
    print("\nGame Summary:")
    history_display.print_full_history()

