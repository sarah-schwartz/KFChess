import pathlib
from Board import Board
from PieceFactory import PieceFactory
from Game import Game
from GraphicsFactory import GraphicsFactory
from GameUI import GameUI
from GameHistoryDisplay import GameHistoryDisplay
from PlayerNamesManager import PlayerNamesManager
from MessageBroker import MessageBroker

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
    game, ui, history_display, broker = create_game_with_history(pieces_root, img_factory)
    return game


def create_game_with_history(pieces_root: str | pathlib.Path, img_factory, player_names_manager: PlayerNamesManager = None) -> tuple:
    """Build a *Game* from the on-disk asset hierarchy rooted at *pieces_root*.

    This reads *board.csv* located inside *pieces_root*, creates a blank board
    (or loads board.png if present), instantiates every piece via PieceFactory
    and returns a ready-to-run *Game* instance with history management.
    
    Returns:
        tuple: (game, ui, history_display, broker)
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
    
    # Create or use provided player names manager
    if not player_names_manager:
        player_names_manager = PlayerNamesManager()
    
    # Create UI with broker and player names manager
    ui = GameUI(None, pieces_root, broker, player_names_manager)  # Pass None for game temporarily
    
    # Create game with broker and UI
    game = Game(pieces, board, broker, ui)
    
    # Set game reference in UI
    ui.game = game
    
    # Get history display from UI
    history_display = ui.history_display
    
    return game, ui, history_display, broker 