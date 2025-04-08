import pyaudio
import time
from vosk import Model, KaldiRecognizer

# Global variables to store audio components
model = None
recognizer = None
p_audio = None
microphone = None

def initialize_speech_recognition(model_path="models/en-gb/"):
    """Initialize the speech recognition components"""
    global model, recognizer, p_audio, microphone
    
    # Clean up first if there are any existing resources
    try:
        cleanup_speech_recognition()
    except:
        pass
    
    print("Starting speech recognition...")
    try:
        model = Model(model_path)
        recognizer = KaldiRecognizer(model, 16000)
        p_audio = pyaudio.PyAudio()
        microphone = p_audio.open(rate=16000, 
                                  channels=1, 
                                  format=pyaudio.paInt16, 
                                  input=True, 
                                  frames_per_buffer=8192)
        microphone.start_stream()
        return microphone
    except Exception as e:
        print(f"Error initializing speech recognition: {e}")
        # Ensure clean state if initialization fails
        cleanup_speech_recognition()
        raise

def cleanup_speech_recognition():
    """Clean up speech recognition resources"""
    global microphone, p_audio
    if microphone:
        microphone.stop_stream()
        microphone.close()
    if p_audio:
        p_audio.terminate()

def listen():
    """
    Listen for speech and return the recognized text
    Returns the recognized text, or None if no speech was detected
    """
    global recognizer, microphone
    
    # Initialize if not already done
    if not microphone:
        initialize_speech_recognition()
    
    try:
        # Read audio data
        data = microphone.read(4096, exception_on_overflow=False)
        
        # Process audio data
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            import json
            text = json.loads(result)["text"]
            if text.strip():
                return text
    except Exception as e:
        print(f"Error in listen: {e}")
    
    return None

def listen_for_command(wake_word, timeout=3.0, silence_limit=1.0):
    """
    Listen for a complete command after wake word detection
    
    Args:
        wake_word: The wake word that was detected
        timeout: Maximum seconds to listen for (default: 3.0)
        silence_limit: Stop listening after this many seconds of silence (default: 1.0)
    
    Returns:
        The complete command text including the wake word
    """
    global recognizer, microphone
    
    if not microphone:
        initialize_speech_recognition()
    
    print(f"Listening for command after wake word '{wake_word}'...")
    
    # Store partial results
    command_parts = [wake_word]
    last_voice_time = time.time()
    start_time = time.time()
    
    # Reset the recognizer to clear any previous partial results
    recognizer.Reset()
    
    while (time.time() - start_time) < timeout:
        try:
            data = microphone.read(4096, exception_on_overflow=False)
            
            # Check for voice activity by looking at partial results
            if recognizer.AcceptWaveform(data):
                # Full result available
                result = recognizer.Result()
                import json
                text = json.loads(result)["text"].strip()
                if text:
                    command_parts.append(text)
                    last_voice_time = time.time()
                    print(f"Adding to command: {text}")
            else:
                # Check partial results for voice activity
                partial = recognizer.PartialResult()
                import json
                partial_text = json.loads(partial).get("partial", "").strip()
                if partial_text:
                    # Voice activity detected
                    last_voice_time = time.time()
            
            # Check if we've had silence long enough to consider the command complete
            if (time.time() - last_voice_time) > silence_limit:
                print("Silence detected, ending command collection")
                break
                
        except Exception as e:
            print(f"Error while listening for command: {e}")
            break
    
    # Combine all parts into a single command
    full_command = " ".join(command_parts).strip()
    print(f"Final command collected: '{full_command}'")
    return full_command

def listen_for_command(timeout=3.0, silence_limit=1.0):
    """
    Listen for additional speech after wake word detection
    
    Args:
        timeout: Maximum seconds to listen for (default: 3.0)
        silence_limit: Stop listening after this many seconds of silence (default: 1.0)
    
    Returns:
        Additional command text after wake word, or empty string if none
    """
    global recognizer, microphone
    
    if not microphone:
        initialize_speech_recognition()
    
    print(f"Listening for additional command parts...")
    
    # Store additional speech parts
    command_parts = []
    last_voice_time = time.time()
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        try:
            data = microphone.read(4096, exception_on_overflow=False)
            
            # Check for voice activity
            if recognizer.AcceptWaveform(data):
                # Full result available
                result = recognizer.Result()
                import json
                text = json.loads(result)["text"].strip()
                if text:
                    command_parts.append(text)
                    last_voice_time = time.time()
                    print(f"Captured additional speech: '{text}'")
            else:
                # Check partial results for voice activity
                partial = recognizer.PartialResult()
                import json
                partial_text = json.loads(partial).get("partial", "").strip()
                if partial_text:
                    # Voice activity detected
                    last_voice_time = time.time()
                    print(f"Detecting speech: '{partial_text}'")
            
            # Check if we've had silence long enough to consider the command complete
            if (time.time() - last_voice_time) > silence_limit and len(command_parts) > 0:
                print("Silence detected, ending command collection")
                break
                
        except Exception as e:
            print(f"Error while listening for command: {e}")
            break
    
    # Combine all parts into a single command
    additional_command = " ".join(command_parts).strip()
    print(f"Additional command parts: '{additional_command}'")
    return additional_command
