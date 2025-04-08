import os
import tempfile
import subprocess
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from anatomy.brain import get_voice_settings

# Store the current audio process so we can stop it if needed
current_audio_process = None

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def speak(text):
    """
    Function to convert text to speech using OpenAI's TTS
    Uses the voice settings from the current mode
    """
    if not text:
        print("No text to speak")
        return False

    try:
        print(f"Converting to speech: '{text}'")
        
        voice_settings = get_voice_settings()
        
        temp_file_path = Path(tempfile.mktemp(suffix=".mp3"))
        
        # Prepare parameters for API call
        params = {
            "model": voice_settings.get("model", "gpt-4o-mini-tts"),
            "voice": voice_settings.get("voice", "onyx"),
            "input": text
        }
        
        # Add instructions if provided
        if voice_settings.get("instructions"):
            params["instructions"] = voice_settings["instructions"]
        
        # Stream the audio response to a file
        with client.audio.speech.with_streaming_response.create(**params) as response:
            response.stream_to_file(temp_file_path)
        
        # Play the audio
        play_audio(str(temp_file_path))
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        return True
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")
        return False

def play_audio(file_path):
    """
    Play audio file using system audio player
    This works well on Raspberry Pi and most Unix systems
    
    Returns when audio playback is complete.
    Can be stopped by calling stop_audio()
    """
    global current_audio_process
    
    try:
        # Determine the platform and use appropriate player
        if os.name == 'posix':  # Linux/Mac
            if os.path.exists("/usr/bin/aplay"):  # Raspberry Pi / Linux
                # Using Popen instead of call allows us to store the process reference
                current_audio_process = subprocess.Popen(
                    ["aplay", file_path], 
                    stderr=subprocess.DEVNULL
                )
                # Wait for completion (blocks until done)
                current_audio_process.wait()
            elif os.path.exists("/usr/bin/afplay"):  # macOS
                current_audio_process = subprocess.Popen(["afplay", file_path])
                current_audio_process.wait()
            else:  # Fallback to mpg123 which is commonly available
                current_audio_process = subprocess.Popen(
                    ["mpg123", file_path], 
                    stderr=subprocess.DEVNULL
                )
                current_audio_process.wait()
        
        current_audio_process = None
        
    except Exception as e:
        print(f"Error playing audio: {str(e)}")
        current_audio_process = None

def stop_audio():
    """
    Stop any currently playing audio
    """
    global current_audio_process
    if current_audio_process is not None:
        try:
            current_audio_process.terminate()
            
            try:
                current_audio_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                current_audio_process.kill()
            
            print("Audio playback stopped")
        except Exception as e:
            print(f"Error stopping audio: {str(e)}")
        
        current_audio_process = None
