
import pyttsx3
import os
from pydub import AudioSegment

def create_check_sound():
    engine = pyttsx3.init()
    
    # Configure initial voice settings
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    for voice in voices:
        if "chinese" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    
    # Create first character with emphasis (slower and louder)
    engine.setProperty('rate', 120)    # Slower speed
    engine.setProperty('volume', 1.0)   # Full volume
    engine.save_to_file('将', 'part1.wav')
    engine.runAndWait()
    
    # Create second character (faster and slightly quieter)
    engine.setProperty('rate', 180)    # Faster speed
    engine.setProperty('volume', 0.8)   # Lower volume
    engine.save_to_file('军', 'part2.wav')
    engine.runAndWait()
    
    # Combine the audio files
    try:
        sound1 = AudioSegment.from_wav("part1.wav")
        sound2 = AudioSegment.from_wav("part2.wav")
        
        # Add a tiny pause between characters (50ms)
        pause = AudioSegment.silent(duration=50)
        
        # Combine the sounds
        combined = sound1 + pause + sound2
        
        # Export final file
        combined.export("check.wav", format="wav")
        
        # Clean up temporary files
        os.remove("part1.wav")
        os.remove("part2.wav")
        
        print("Check sound created successfully!")
        
    except Exception as e:
        print(f"Error combining audio files: {e}")

if __name__ == "__main__":
    create_check_sound()