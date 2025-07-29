# Board Architecture - Client-Server Split

הקובץ `Board.py` חולק לשלושה חלקים בהתאם לארכיטקטורת Client-Server:

## 📁 SHARED (`shared/board_data.py`)
**מה שמשותף בין הלקוח והשרת**

- `BoardData` - מבנה הנתונים הבסיסי של הלוח
- פונקציות המרת קואורדינטות (מטרים ↔ תאים ↔ פיקסלים)
- סריאליזציה ל-JSON (`to_dict`, `from_dict`, `to_json_string`)
- **אין תלות בממשקי משתמש או תמונות**

```python
from shared.board_data import BoardData

# יצירת לוח בסיסי
board_data = BoardData(
    cell_H_pix=64, cell_W_pix=64,
    W_cells=8, H_cells=8
)

# המרת קואורדינטות
row, col = board_data.m_to_cell((2.5, 3.0))

# JSON לWebSocket
json_str = board_data.to_json_string()
```

## 🖥️ SERVER (`server/server_board.py`)
**לוגיקת השרת ואימותים**

- `ServerBoard` - מנהל את מצב הלוח במשחק
- אימות מהלכים (`validate_move`, `validate_position`)
- ביצוע מהלכים (`execute_move`)
- מעקב אחרי גרסת המצב (`state_version`) לסנכרון
- ניהול מיקומי כלי המשחק
- החזרת מצב ללקוחות (`get_state_for_client`)

```python
from server.server_board import ServerBoard

# שרת מתחיל משחק חדש
server_board = ServerBoard.create_default()

# הוספת כלי למשחק
server_board.set_piece_position("king_white", (0, 4))
server_board.set_piece_position("queen_white", (0, 3))

# אימות וביצוע מהלך
if server_board.validate_move((0, 3), (4, 7)):
    if server_board.execute_move("queen_white", (0, 3), (4, 7)):
        # המהלך בוצע - שלח עדכון ללקוחות
        state = server_board.get_state_for_client()
        broadcast_to_clients(state)

# JSON לWebSocket
json_str = server_board.to_json_string()
```

## 💻 CLIENT (`client/client_board.py`)
**תצוגה וממשק משתמש**

- `ClientBoard` - מנהל תצוגה מקומית של הלוח
- עבודה עם תמונות (`img.py`)
- סנכרון עם השרת (`update_from_server`)
- עזרים לממשק משתמש (המרת פיקסלים ↔ תאים)
- אינטראקציה עם עכבר (`get_piece_at_pixel`)
- מעקב מקומי אחרי כלי המשחק

```python
from client.client_board import ClientBoard

# לקוח מקבל מצב מהשרת
client_board = ClientBoard.create_from_server_state(server_state, board_image)

# התעדכנות מהשרת
if client_board.update_from_server(new_server_state):
    print("הלוח עודכן!")
    client_board.show()

# אינטראקציה עם עכבר
def on_mouse_click(x, y):
    piece_id = client_board.get_piece_at_pixel(x, y)
    if piece_id:
        print(f"נלחץ על: {piece_id}")
        cell = client_board.get_cell_at_pixel(x, y)
        print(f"בתא: {cell}")

# JSON לWebSocket
json_str = client_board.to_json_string()
```

## 🏗️ ארכיטקטורת Client-Server

```
         🌐 WebSocket Communication
              ↕️
    ┌─────────────────┐      ┌─────────────────┐
    │     CLIENT 1    │      │     CLIENT 2    │
    │                 │      │                 │
    │ ClientBoard     │      │ ClientBoard     │
    │ - UI & Display  │      │ - UI & Display  │
    │ - Local State   │      │ - Local State   │
    │ - Mouse Input   │      │ - Mouse Input   │
    └─────────────────┘      └─────────────────┘
              ↕️                       ↕️
         ┌─────────────────────────────────────┐
         │            SERVER                   │
         │                                     │
         │ ServerBoard                         │
         │ - Game Logic                        │
         │ - Move Validation                   │
         │ - Piece Positions                   │
         │ - Authoritative State               │
         │ - Sync Management                   │
         └─────────────────────────────────────┘
```

## 📡 תקשורת WebSocket

**מהלך טיפוסי:**

1. **לקוח מזיז כלי:**
   ```python
   # לקוח מגלה לחיצה על כלי
   piece_id = client_board.get_piece_at_pixel(mouse_x, mouse_y)
   from_cell = client_board.get_piece_position(piece_id)
   to_cell = client_board.get_cell_at_pixel(new_x, new_y)
   
   # שליחת בקשת מהלך לשרת
   move_request = {
       "type": "move",
       "piece_id": piece_id,
       "from": from_cell,
       "to": to_cell
   }
   websocket.send(json.dumps(move_request))
   ```

2. **שרת מעבד ומאמת:**
   ```python
   # שרת מקבל בקשה
   if server_board.validate_move(from_cell, to_cell):
       if server_board.execute_move(piece_id, from_cell, to_cell):
           # מהלך חוקי - שידור לכולם
           updated_state = server_board.get_state_for_client()
           broadcast_to_all_clients(updated_state)
       else:
           # שגיאה בביצוע
           send_error_to_client(client_id, "Failed to execute move")
   else:
       # מהלך לא חוקי
       send_error_to_client(client_id, "Invalid move")
   ```

3. **לקוחות מעדכנים תצוגה:**
   ```python
   # כל הלקוחות מקבלים עדכון
   def on_server_update(server_state):
       if client_board.update_from_server(server_state):
           # הלוח השתנה - עדכן תצוגה
           client_board.show()
           update_ui_elements()
   ```

## 🎯 יתרונות החלוקה

- **הפרדת אחריויות**: UI, לוגיקה, ונתונים נפרדים
- **ביטחון**: השרת שולט על חוקי המשחק ומיקומי הכלים
- **סנכרון**: כל השחקנים רואים את אותו מצב
- **גמישות**: ניתן להחליף UI בלי לשנות לוגיקה
- **אינטראקטיביות**: תמיכה מלאה באינטראקציה עם עכבר
- **JSON WebSocket**: תקשורת מהירה ויעילה

## 🔧 דוגמת שימוש מלאה

### שרת WebSocket
```python
import asyncio
import websockets
import json
from server.server_board import ServerBoard

class GameServer:
    def __init__(self):
        self.board = ServerBoard.create_default()
        self.clients = {}
        
        # הגדרת כלים ראשונית
        self.setup_initial_pieces()
    
    def setup_initial_pieces(self):
        # מלך לבן
        self.board.set_piece_position("king_white", (0, 4))
        # מלכה לבנה
        self.board.set_piece_position("queen_white", (0, 3))
        # מלך שחור
        self.board.set_piece_position("king_black", (7, 4))
        # מלכה שחורה
        self.board.set_piece_position("queen_black", (7, 3))
    
    async def handle_client(self, websocket, path):
        client_id = f"player_{len(self.clients) + 1}"
        self.clients[client_id] = websocket
        
        # שלח מצב ראשוני ללקוח
        initial_state = self.board.get_state_for_client()
        await websocket.send(json.dumps(initial_state))
        
        try:
            async for message in websocket:
                await self.process_move(json.loads(message), client_id)
        except websockets.exceptions.ConnectionClosed:
            del self.clients[client_id]
    
    async def process_move(self, move_data, client_id):
        piece_id = move_data["piece_id"]
        from_pos = tuple(move_data["from"])
        to_pos = tuple(move_data["to"])
        
        if self.board.execute_move(piece_id, from_pos, to_pos):
            # מהלך הצליח - שדר לכולם
            updated_state = self.board.get_state_for_client()
            message = json.dumps(updated_state)
            
            for client_ws in self.clients.values():
                await client_ws.send(message)
        else:
            # מהלך נכשל - שלח שגיאה
            error_msg = {"error": "Invalid move"}
            await self.clients[client_id].send(json.dumps(error_msg))

# הפעלת השרת
start_server = websockets.serve(GameServer().handle_client, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
```

### לקוח
```python
import websocket
import json
from client.client_board import ClientBoard

class GameClient:
    def __init__(self, server_url):
        self.board = None
        self.ws = websocket.WebSocketApp(server_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
    
    def on_message(self, ws, message):
        data = json.loads(message)
        
        if "error" in data:
            print(f"שגיאה: {data['error']}")
            return
        
        # עדכון הלוח מהשרת
        if self.board is None:
            self.board = ClientBoard.create_from_server_state(data)
        else:
            self.board.update_from_server(data)
        
        self.board.show()
        print(f"גרסת מצב: {self.board.local_state_version}")
    
    def move_piece(self, piece_id, from_pos, to_pos):
        move_data = {
            "type": "move",
            "piece_id": piece_id,
            "from": from_pos,
            "to": to_pos
        }
        self.ws.send(json.dumps(move_data))
    
    def on_mouse_click(self, x, y):
        if self.board:
            piece_id = self.board.get_piece_at_pixel(x, y)
            if piece_id:
                current_pos = self.board.get_piece_position(piece_id)
                # כאן תוכל להוסיף לוגיקה לבחירת יעד
                print(f"נבחר כלי: {piece_id} במיקום: {current_pos}")

# התחברות לשרת
client = GameClient("ws://localhost:8765")
client.ws.run_forever()
```

זה מראה איך הלוח עובד בארכיטקטורת Client-Server עם WebSocket מלא! 🚀
