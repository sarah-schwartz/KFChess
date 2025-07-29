# Command Architecture - Client-Server Split

הקובץ `Command.py` חולק לשלושה חלקים בהתאם לארכיטקטורת Client-Server:

## 📁 SHARED (`shared/command_data.py`)
**מה שמשותף בין הלקוח והשרת**

- `CommandData` - מבנה הנתונים הבסיסי של הפקודה
- `CommandType` - Enum לסוגי הפקודות השונים
- `WebSocketMessage` - עוטף הודעות WebSocket עם metadata
- סריאליזציה ל-JSON (`to_dict`, `from_dict`, `to_json_string`)
- ולידציה בסיסית של פורמט (`is_valid_format`)

```python
from shared.command_data import CommandData, CommandType, WebSocketMessage

# יצירת פקודת מהלך
command = CommandData(
    timestamp=1640995200000,
    piece_id="king_white",
    type=CommandType.MOVE,
    params=[(0, 4), (0, 6)]  # castling
)

# המרה ל-JSON לשליחה
json_data = command.to_json_string()

# יצירת הודעת WebSocket
ws_msg = WebSocketMessage.create_command_message(command, "player_1", "game_123")
```

### CommandType Enum:
- `MOVE` - הזזת כלי
- `JUMP` - קפיצה (למשחקי דמקה)
- `ATTACK` - תקיפה
- `CAPTURE` - לכידה
- `CASTLE` - הצרחה
- `PROMOTE` - הכתרה
- `RESIGN` - וויתור
- `DRAW_OFFER` - הצעת תיקו
- `DRAW_ACCEPT` - קבלת תיקו
- `DRAW_DECLINE` - דחיית תיקו

## 🖥️ SERVER (`server/server_command.py`)
**לוגיקת השרת ואימותים**

- `ServerCommand` - מנהל ביצוע פקודות בשרת
- אימות פקודות (`validate_command`) מול מצב המשחק
- ביצוע פקודות (`execute`) ועדכון מצב
- מעקב אחרי תוצאות ביצוע (`execution_result`)
- יצירת תגובות WebSocket (`to_websocket_response`, `to_websocket_broadcast`)

```python
from server.server_command import ServerCommand

# שרת מקבל פקודה מלקוח
server_cmd = ServerCommand.from_websocket_message(ws_json)

# אימות הפקודה מול מצב המשחק
game_state = {
    'pieces_positions': {
        'king_white': (0, 4),
        'rook_white_h': (0, 7)
    }
}

if server_cmd.validate_command(game_state):
    # ביצוע הפקודה
    if server_cmd.execute(game_state):
        # שליחת אישור ללקוח ששלח
        response = server_cmd.to_websocket_response("player_1", "game_123")
        send_to_client("player_1", response)
        
        # שידור לכל הלקוחות
        broadcast = server_cmd.to_websocket_broadcast("game_123")
        broadcast_to_all_clients(broadcast)
    else:
        # שגיאה בביצוע
        error_response = server_cmd.to_websocket_response("player_1", "game_123")
        send_to_client("player_1", error_response)
```

## 💻 CLIENT (`client/client_command.py`)
**יצירת פקודות וממשק משתמש**

- `ClientCommand` - מנהל פקודות בצד הלקוח
- יצירת פקודות מממשק המשתמש
- שליחה לשרת וטיפול בתגובות (`handle_websocket_response`)
- `CommandBuilder` - עזר ליצירת פקודות מורכבות
- `CommandHistory` - ניהול היסטוריית פקודות לUndo/Redo

```python
from client.client_command import ClientCommand, CommandBuilder, CommandHistory

# יצירת פקודת מהלך פשוטה
move_cmd = ClientCommand.create_move_command(
    piece_id="pawn_e2",
    from_pos=(1, 4),  # e2
    to_pos=(3, 4)     # e4
)

# שליחה לשרת
client_id = "player_1"
session_id = "game_123"
ws_json = move_cmd.to_websocket_message(client_id, session_id)
websocket.send(ws_json)
move_cmd.mark_as_sent()

# טיפול בתגובת השרת
def on_server_response(ws_response):
    if move_cmd.handle_websocket_response(ws_response):
        print("המהלך בוצע בהצלחה!")
        result = move_cmd.get_execution_result()
        print(f"תוצאה: {result}")
    else:
        print(f"המהלך נדחה: {move_cmd.get_error_message()}")

# שימוש ב-CommandBuilder למקרים מורכבים
builder = CommandBuilder()
complex_cmd = (builder
    .set_piece("queen_d1")
    .set_type(CommandType.ATTACK)
    .add_param((4, 7))  # target position
    .add_param("capture")
    .build())

# ניהול היסטוריה
history = CommandHistory()
history.add_command(move_cmd)
recent_moves = history.get_recent_commands(5)
```

## 🔄 ארכיטקטורת Client-Server

```
         🌐 WebSocket Communication
              ↕️
    ┌─────────────────┐      ┌─────────────────┐
    │     CLIENT 1    │      │     CLIENT 2    │
    │                 │      │                 │
    │ ClientCommand   │      │ ClientCommand   │
    │ - Create        │      │ - Create        │
    │ - Send          │      │ - Send          │
    │ - Track Status  │      │ - Track Status  │
    │ - Command Hist. │      │ - Command Hist. │
    └─────────────────┘      └─────────────────┘
              ↕️                       ↕️
         ┌─────────────────────────────────────┐
         │            SERVER                   │
         │                                     │
         │ ServerCommand                       │
         │ - Validate Commands                 │
         │ - Execute Game Logic                │
         │ - Update Game State                 │
         │ - Send Results to Clients           │
         └─────────────────────────────────────┘
```

## 📡 זרימת פקודה טיפוסית

### 1. לקוח יוצר ושולח פקודה:
```json
{
  "message_type": "command",
  "command_data": {
    "timestamp": 1640995200000,
    "piece_id": "pawn_e2",
    "type": "move",
    "params": [[1, 4], [3, 4]]
  },
  "client_id": "player_1",
  "session_id": "game_123"
}
```

### 2. שרת מאמת ומבצע:
```python
# אימות
if server_cmd.validate_command(game_state):
    # ביצוע
    if server_cmd.execute(game_state):
        # עדכון מצב המשחק
        game_state['pieces_positions']['pawn_e2'] = (3, 4)
```

### 3. שרת מחזיר תשובה:
```json
{
  "message_type": "response",
  "command_data": {
    "timestamp": 1640995200001,
    "piece_id": "pawn_e2",
    "type": "move",
    "params": [{
      "success": true,
      "execution_result": {
        "type": "move_executed",
        "piece_id": "pawn_e2",
        "from": [1, 4],
        "to": [3, 4],
        "timestamp": 1640995200001
      },
      "error_message": null
    }]
  },
  "client_id": "player_1",
  "session_id": "game_123"
}
```

### 4. שרת משדר לכל הלקוחות:
```json
{
  "message_type": "broadcast",
  "command_data": {
    "timestamp": 1640995200001,
    "piece_id": "pawn_e2",
    "type": "move",
    "params": [{
      "type": "move_executed",
      "piece_id": "pawn_e2",
      "from": [1, 4],
      "to": [3, 4],
      "timestamp": 1640995200001
    }]
  },
  "client_id": "",
  "session_id": "game_123"
}
```

## 🎯 יתרונות החלוקה

- **טיפ-בטיחות**: שימוש ב-Enum למניעת שגיאות טיפוס
- **אימות מרכזי**: השרת שולט על חוקיות הפקודות
- **מעקב סטטוס**: לקוח יודע מצב הפקודה בכל רגע
- **היסטוריה**: תמיכה ב-Undo/Redo על הלקוח
- **גמישות**: קל להוסיף סוגי פקודות חדשים
- **דבגינג**: מעקב מלא אחרי ביצוע פקודות
- **אסינכרוני**: לקוח לא נחסם בזמן ביצוע
- **WebSocket מלא**: תקשורת JSON מובנית

## 🔧 הוספת סוג פקודה חדש

### 1. הוסף ל-Enum (SHARED):
```python
class CommandType(Enum):
    # ... existing types
    SPECIAL_MOVE = "special_move"
```

### 2. הוסף ולידציה בשרת (SERVER):
```python
def validate_command(self, game_state):
    if self.type == CommandType.SPECIAL_MOVE:
        return self._validate_special_move_command(game_state)

def _validate_special_move_command(self, game_state):
    # validation logic
    return True
```

### 3. הוסף ביצוע בשרת (SERVER):
```python
def execute(self, game_state):
    if self.type == CommandType.SPECIAL_MOVE:
        self.execution_result = self._execute_special_move(game_state)

def _execute_special_move(self, game_state):
    # execution logic
    return {"type": "special_move_executed", ...}
```

### 4. הוסף factory method בלקוח (CLIENT):
```python
@classmethod
def create_special_move_command(cls, piece_id, special_params):
    command_data = CommandData(
        timestamp=int(time.time() * 1000),
        piece_id=piece_id,
        type=CommandType.SPECIAL_MOVE,
        params=special_params
    )
    return cls(command_data)
```

## 🛠️ דוגמת שימוש מלאה

### שרת WebSocket מלא:
```python
import asyncio
import websockets
import json
from server.server_command import ServerCommand

class GameServer:
    def __init__(self):
        self.game_state = {
            'pieces_positions': {
                'king_white': (0, 4),
                'queen_white': (0, 3),
                'pawn_e2': (1, 4)
            }
        }
        self.clients = {}
    
    async def handle_client(self, websocket, path):
        client_id = f"player_{len(self.clients) + 1}"
        self.clients[client_id] = websocket
        
        try:
            async for message in websocket:
                await self.process_command(message, client_id)
        except websockets.exceptions.ConnectionClosed:
            del self.clients[client_id]
    
    async def process_command(self, ws_json, client_id):
        server_cmd = ServerCommand.from_websocket_message(ws_json)
        
        if server_cmd.validate_command(self.game_state):
            if server_cmd.execute(self.game_state):
                # תשובה ללקוח ששלח
                response = server_cmd.to_websocket_response(client_id, "game_123")
                await self.clients[client_id].send(response)
                
                # שידור לכולם
                broadcast = server_cmd.to_websocket_broadcast("game_123")
                await self.broadcast_to_all(broadcast)
            else:
                # שגיאה בביצוע
                error_response = server_cmd.to_websocket_response(client_id, "game_123")
                await self.clients[client_id].send(error_response)
        else:
            # פקודה לא חוקית
            error_response = server_cmd.to_websocket_response(client_id, "game_123")
            await self.clients[client_id].send(error_response)
    
    async def broadcast_to_all(self, message):
        for client_ws in self.clients.values():
            await client_ws.send(message)

# הפעלת השרת
start_server = websockets.serve(GameServer().handle_client, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
```

### לקוח עם UI:
```python
import websocket
import json
from client.client_command import ClientCommand, CommandHistory

class GameClient:
    def __init__(self, server_url, client_id):
        self.client_id = client_id
        self.session_id = "game_123"
        self.command_history = CommandHistory()
        self.pending_commands = {}  # track sent commands
        
        self.ws = websocket.WebSocketApp(server_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
    
    def send_move(self, piece_id, from_pos, to_pos):
        move_cmd = ClientCommand.create_move_command(piece_id, from_pos, to_pos)
        if move_cmd:
            ws_json = move_cmd.to_websocket_message(self.client_id, self.session_id)
            self.ws.send(ws_json)
            move_cmd.mark_as_sent()
            
            # Track pending command
            self.pending_commands[move_cmd.timestamp] = move_cmd
            self.command_history.add_command(move_cmd)
    
    def on_message(self, ws, message):
        data = json.loads(message)
        msg_type = data.get('message_type')
        
        if msg_type == 'response':
            # טיפול בתשובה לפקודה שלי
            self.handle_response(message)
        elif msg_type == 'broadcast':
            # טיפול בשידור מהמשחק
            self.handle_broadcast(message)
    
    def handle_response(self, ws_json):
        # מצא את הפקודה המתאימה
        for cmd in self.pending_commands.values():
            if cmd.handle_websocket_response(ws_json):
                if cmd.is_confirmed():
                    print(f"הפקודה {cmd.type.value} בוצעה בהצלחה!")
                else:
                    print(f"הפקודה נדחתה: {cmd.get_error_message()}")
                break
    
    def handle_broadcast(self, ws_json):
        broadcast_cmd = ClientCommand.from_websocket_broadcast(ws_json)
        if broadcast_cmd:
            print(f"עדכון מהמשחק: {broadcast_cmd.type.value}")
            # עדכן UI בהתאם
    
    def get_command_history(self, piece_id=None):
        if piece_id:
            return self.command_history.get_commands_by_piece(piece_id)
        return self.command_history.get_recent_commands()

# שימוש
client = GameClient("ws://localhost:8765", "player_1")
client.ws.run_forever()

# בממשק המשתמש:
# client.send_move("pawn_e2", (1, 4), (3, 4))
```

זה מראה איך ה-Command עובד במלואו עם WebSocket ו-JSON בארכיטקטורת Client-Server! 🚀
