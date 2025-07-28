import pathlib
from Board import Board
from PieceFactory import PieceFactory
from Game import Game
from GraphicsFactory import GraphicsFactory
from GameUI import GameUI
from GameHistoryDisplay import GameHistoryDisplay
from MessageBroker import MessageBroker
from PlayerNamesManager import PlayerNamesManager
from SoundManager import SoundManager
from MessageDisplay import MessageDisplay

CELL_PX = 64


def create_game(pieces_root: str | pathlib.Path, img_factory) -> Game:
    """Build a *Game* from the on-disk asset hierarchy rooted at *pieces_root*.

    This reads *board.csv* located inside *pieces_root*, creates a blank board
    (or loads board.png if present), instantiates every piece via PieceFactory
    and returns a ready-to-run *Game* instance.
    
    For backward compatibility, this returns only the Game object.
    Use create_game_with_history() for the full tuple with history management.
    
    Returns:
        Game: The game instance
    """
    game, ui, history_display, broker, sound_manager = create_game_with_history(pieces_root, img_factory)
    return game


def create_game_with_history(pieces_root: str | pathlib.Path, img_factory) -> tuple:
    """Build a *Game* from the on-disk asset hierarchy rooted at *pieces_root*.

    This reads *board.csv* located inside *pieces_root*, creates a blank board
    (or loads board.png if present), instantiates every piece via PieceFactory
    and returns a ready-to-run *Game* instance with history management, sound effects,
    and message display system.
    
    Returns:
        tuple: (game, ui, history_display, broker, sound_manager, message_display)
    """
    pieces_root = pathlib.Path(pieces_root)
    board_csv = pieces_root / "board.csv"
    if not board_csv.exists():
        raise FileNotFoundError(board_csv)

    # Try to load board.png for the actual board, background.jpg will be handled by GameUI
    board_png = pieces_root / "board.png"
    
    loader = img_factory
    
    # Load board image (the actual chess board, not the background)
    if board_png.exists():
        board_img = loader(board_png, (CELL_PX*8, CELL_PX*8), keep_aspect=False)
    else:
        raise FileNotFoundError(f"Board image {board_png} not found")

    board = Board(CELL_PX, CELL_PX, 8, 8, board_img)

    gfx_factory = GraphicsFactory(img_factory)
    pf = PieceFactory(board, pieces_root, graphics_factory=gfx_factory)

    pieces = []
    with board_csv.open() as f:
        for r, line in enumerate(f):
            for c, code in enumerate(line.strip().split(",")):
                if code:
                    pieces.append(pf.create_piece(code, (r, c)))

    # Create the game with history management system
    broker = MessageBroker()
    
    # Create sound manager with sounds from pieces/sound folder
    sounds_folder = pieces_root / "sound"
    sound_manager = SoundManager(broker, sounds_folder)
    
    # Create message display system
    message_display = MessageDisplay(broker, screen_width=800, screen_height=600)
    
    # Get player names from user before creating the game
    print("Welcome to KFC Chess!")
    player_names_manager = PlayerNamesManager()
    white_name, black_name = player_names_manager.get_player_names_from_gui()
    print(f"Starting game: {white_name} (White) vs {black_name} (Black)")
    
    # Create UI with broker and player names
    ui = GameUI(None, pieces_root, broker, player_names_manager)  # Pass the names manager
    
    # Create game with broker and UI
    game = Game(pieces, board, broker, ui)
    
    # Set game reference in UI
    ui.game = game
    
    # Get history display from UI
    history_display = ui.history_display
    
    return game, ui, history_display, broker, sound_manager, message_display