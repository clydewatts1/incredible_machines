import os
import wave
import struct
import math

def generate_tone(filename, frequency, duration_ms, volume=0.5, decay=True):
    sample_rate = 44100
    num_samples = int(sample_rate * (duration_ms / 1000.0))
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            env = 1.0
            if decay:
                env = max(0, 1.0 - (float(i) / num_samples))
            
            value = math.sin(2.0 * math.pi * frequency * t) * volume * env
            # 16-bit encoding
            packed_value = struct.pack('h', int(value * 32767.0))
            wav_file.writeframes(packed_value)
            
    print(f"Generated {filename}")

if __name__ == "__main__":
    sounds_dir = os.path.join(os.path.dirname(__file__), 'assets', 'sounds')
    os.makedirs(sounds_dir, exist_ok=True)
    
    # Default Thud
    generate_tone(os.path.join(sounds_dir, 'default_collision.wav'), frequency=150.0, duration_ms=100, volume=0.8, decay=True)
    
    # High Pitch Bounce
    generate_tone(os.path.join(sounds_dir, 'bounce.wav'), frequency=800.0, duration_ms=150, volume=0.6, decay=True)
    
    # Spawn Blip
    generate_tone(os.path.join(sounds_dir, 'spawn.wav'), frequency=440.0, duration_ms=50, volume=0.4, decay=False)
