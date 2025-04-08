import pyaudio
from vosk import Model, KaldiRecognizer

# Global variables to store audio components
model = None
recognizer = None
p_audio = None
microphone = None

def initialize_speech_recognition(model_path="models/en-gb/"):
    """Initialize the speech recognition components"""
    global model, recognizer, p_audio, microphone
    
    print("Starting speech recognition...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    p_audio = pyaudio.PyAudio()
    microphone = p_audio.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=8192)
    microphone.start_stream()
    return microphone

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
    
    # Read audio data
    data = microphone.read(4096)
    
    # Process audio data
    if recognizer.AcceptWaveform(data):
        result = recognizer.Result()
        import json
        text = json.loads(result)["text"]
        if text.strip():
            return text
    
    return None
