
import logging
from GameFactory import create_game_with_history
from GraphicsFactory import ImgFactory
from PlayerNamesManager import PlayerNamesManager

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get player names using graphical interface
    player_names_manager = PlayerNamesManager()
    white_name, black_name = player_names_manager.get_player_names_from_gui()
    
    # Create game with new system and player names
    game, ui, history_display, broker = create_game_with_history("../pieces", ImgFactory(), player_names_manager)
    
    # Print message about new system activation
    print("Command history management system activated!")
    print("History will be displayed in real-time in the UI.")
    print(f"Game players: {white_name} vs {black_name}")
    
    # Run the game
    game.run()
    
    # Display game history summary at the end
    print(f"\nGame Summary for {white_name} vs {black_name}:")
    history_display.print_full_history()

