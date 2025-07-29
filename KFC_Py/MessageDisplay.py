import pygame
import time
from typing import Optional, Dict, Any
from Subscriber import Subscriber
from EventType import EventType
from MessageBroker import MessageBroker

# Message constants - easy to modify
GAME_START_MESSAGE = "Welcome to KFC Chess!"
GAME_END_MESSAGE_TEMPLATE = "{winner_color} Wins!"

class MessageDisplay(Subscriber):
    """
    Class for displaying animated messages on screen during game events.
    Shows welcome messages at game start and victory messages at game end.
    """
    
    def __init__(self, broker: MessageBroker, screen_width: int = 800, screen_height: int = 600):
        """
        Initialize message display system.
        
        Args:
            broker: MessageBroker for receiving game events
            screen_width: Width of the game screen
            screen_height: Height of the game screen
        """
        self.broker = broker
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Message state
        self.current_message: Optional[str] = None
        self.message_start_time: Optional[float] = None
        self.message_duration: float = 3.0  # Default 3 seconds
        self.message_fade_duration: float = 0.5  # Fade in/out duration
        
        # Font setup (will be initialized when pygame is available)
        self.font_large = None
        self.font_medium = None
        
        # Subscribe to relevant events
        self.broker.subscribe(EventType.GAME_START, self)
        self.broker.subscribe(EventType.GAME_END, self)
        
        # Initialize fonts if pygame is available
        self._init_fonts()
    
    def _init_fonts(self):
        """Initialize pygame fonts if pygame is available."""
        try:
            pygame.font.init()
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 48)
            print("DEBUG: MessageDisplay fonts initialized")
        except Exception as e:
            print(f"WARNING: Could not initialize fonts: {e}")
    
    def handle_event(self, event_type: EventType, data: Dict[str, Any]):
        """
        Handle events received from MessageBroker.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            if event_type == EventType.GAME_START:
                self._show_game_start_message()
            elif event_type == EventType.GAME_END:
                self._show_game_end_message(data)
        except Exception as e:
            print(f"ERROR: Failed to handle message event {event_type}: {e}")
    
    def _show_game_start_message(self):
        """Show welcome message at game start."""
        self._display_message(GAME_START_MESSAGE, duration=2.5)
        print(f"DEBUG: Showing game start message: {GAME_START_MESSAGE}")
    
    def _show_game_end_message(self, data: Dict[str, Any]):
        """Show victory message at game end."""
        winner = data.get('winner', 'Unknown')
        winner_color = data.get('winner_color', 'Unknown')
        
        message = GAME_END_MESSAGE_TEMPLATE.format(winner_color=winner_color)
        self._display_message(message, duration=4.0)
        print(f"DEBUG: Showing game end message: {message}")
    
    def _show_custom_message(self, data: Dict[str, Any]):
        """Show a custom message."""
        message = data.get('message', 'Custom Message')
        duration = data.get('duration', 3.0)
        self._display_message(message, duration=duration)
        print(f"DEBUG: Showing custom message: {message}")
    
    def _display_message(self, message: str, duration: float = 3.0):
        """Display a message for the specified duration."""
        self.current_message = message
        self.message_start_time = time.time()
        self.message_duration = duration
        print(f"INFO: Displaying message: '{message}' for {duration} seconds")
    
    def _hide_current_message(self):
        """Hide the current message immediately."""
        self.current_message = None
        self.message_start_time = None
        print("DEBUG: Message hidden")
    
    def update(self):
        """Update message display state. Call this regularly from game loop."""
        if self.current_message and self.message_start_time is not None:
            elapsed = time.time() - self.message_start_time
            
            if elapsed >= self.message_duration:
                # Message duration expired, hide it
                self._hide_current_message()
    
    def get_current_message(self) -> Optional[str]:
        """Get the currently displayed message, if any."""
        return self.current_message
    
    def get_message_alpha(self) -> float:
        """
        Get the alpha value for message display (for fade effects).
        Returns value between 0.0 (invisible) and 1.0 (fully visible).
        """
        if not self.current_message or self.message_start_time is None:
            return 0.0
        
        elapsed = time.time() - self.message_start_time
        
        # Fade in
        if elapsed < self.message_fade_duration:
            return elapsed / self.message_fade_duration
        
        # Fade out
        fade_start = self.message_duration - self.message_fade_duration
        if elapsed > fade_start:
            fade_progress = (elapsed - fade_start) / self.message_fade_duration
            return max(0.0, 1.0 - fade_progress)
        
        # Fully visible
        return 1.0
    
    def render_message(self, surface):
        """
        Render the current message to the given surface.
        
        Args:
            surface: pygame surface to render to
        """
        if not self.current_message or not self.font_large:
            return
        
        alpha = self.get_message_alpha()
        if alpha <= 0.0:
            return
        
        try:
            # Create text surface
            text_surface = self.font_large.render(self.current_message, True, (255, 255, 255))
            
            # Apply alpha
            if alpha < 1.0:
                text_surface.set_alpha(int(alpha * 255))
            
            # Center the text
            text_rect = text_surface.get_rect()
            text_rect.center = (self.screen_width // 2, self.screen_height // 2)
            
            # Create background rectangle with transparency
            bg_rect = text_rect.inflate(40, 20)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(int(alpha * 128))  # Semi-transparent background
            bg_surface.fill((0, 0, 0))
            
            # Render background and text
            surface.blit(bg_surface, bg_rect)
            surface.blit(text_surface, text_rect)
            
        except Exception as e:
            print(f"ERROR: Failed to render message: {e}")
