import pygame
import pathlib
from typing import Dict
from Subscriber import Subscriber
from EventType import EventType
from MessageBroker import MessageBroker

class SoundManager(Subscriber):
    """
    Class for managing sound effects for game events.
    Plays sounds for piece movements and captures.
    """
    
    def __init__(self, broker: MessageBroker, sounds_folder: pathlib.Path):
        """
        Initialize sound manager.
        
        Args:
            broker: MessageBroker for receiving game events
            sounds_folder: Path to folder containing sound files
        """
        self.broker = broker
        self.sounds_folder = sounds_folder
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load sound files
        self._load_sounds()
        
        # Subscribe to game events
        self.broker.subscribe(EventType.PIECE_MOVED, self)
        self.broker.subscribe(EventType.PIECE_CAPTURED, self)
    
    def _load_sounds(self):
        """Load all sound files from the sounds folder."""
        try:
            move_path = self.sounds_folder / "move.wav"
            capture_path = self.sounds_folder / "capture.wav"
            
            if move_path.exists():
                self.sounds["move"] = pygame.mixer.Sound(str(move_path))
                print(f"DEBUG: Loaded move sound from {move_path}")
            else:
                print(f"WARNING: Move sound file not found at {move_path}")
            
            if capture_path.exists():
                self.sounds["capture"] = pygame.mixer.Sound(str(capture_path))
                print(f"DEBUG: Loaded capture sound from {capture_path}")
            else:
                print(f"WARNING: Capture sound file not found at {capture_path}")
                
        except Exception as e:
            print(f"ERROR: Failed to load sounds: {e}")
    
    def handle_event(self, event_type: EventType, data):
        """
        Handle events received from MessageBroker.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            if event_type == EventType.PIECE_MOVED:
                self._play_move_sound()
            elif event_type == EventType.PIECE_CAPTURED:
                self._play_capture_sound()
        except Exception as e:
            print(f"ERROR: Failed to handle sound event {event_type}: {e}")
    
    def _play_move_sound(self):
        """Play the move sound effect."""
        if "move" in self.sounds:
            self.sounds["move"].play()
            print("DEBUG: Played move sound")
        else:
            print("WARNING: Move sound not available")
    
    def _play_capture_sound(self):
        """Play the capture sound effect."""
        if "capture" in self.sounds:
            self.sounds["capture"].play()
            print("DEBUG: Played capture sound")
        else:
            print("WARNING: Capture sound not available")
    
    def set_volume(self, volume: float):
        """
        Set volume for all sounds.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        for sound in self.sounds.values():
            sound.set_volume(volume)
    
    def stop_all_sounds(self):
        """Stop all currently playing sounds."""
        pygame.mixer.stop()