import pygame
import os

class SoundManager:
    _instance = None
    _sounds = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        if self._initialized:
            return
        
        # Ensure mixer is initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        self.sounds_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')
        
        # Preload the default fallback collision sound
        self.default_sound_file = "default_collision.wav"
        self.load_sound(self.default_sound_file)
        
        self._initialized = True

    def load_sound(self, filename):
        """Loads a sound into the memory cache. Fails loudly on first load (e.g. for default)."""
        if filename in self._sounds:
            return self._sounds[filename]
            
        filepath = os.path.join(self.sounds_dir, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: Sound file not found: {filepath}")
            self._sounds[filename] = None # Mark as failed to load
            return None
            
        try:
            sound = pygame.mixer.Sound(filepath)
            self._sounds[filename] = sound
            return sound
        except Exception as e:
            print(f"FAIL LOUDLY: Failed to load sound {filepath}: {e}")
            self._sounds[filename] = None
            return None

    def play_sound(self, filename):
        """Plays the requested sound. Automatically falls back to default if missing or invalid."""
        if not self._initialized:
            self.initialize()
            
        # Try to play the requested sound
        sound = self.load_sound(filename)
        if sound:
            sound.play()
            return

        # Fallback Logic: The requested sound is missing or failed to load.
        # Play the default fallback sound per Constitution Section 8.
        if filename != self.default_sound_file:
            print(f"SoundManager: Fallback triggered for missing '{filename}'. Playing '{self.default_sound_file}'")
            default_sound = self.load_sound(self.default_sound_file)
            if default_sound:
                default_sound.play()

# Create a singleton instance for global use
sound_manager = SoundManager()
