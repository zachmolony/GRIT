import os
import json
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

WAKE_WORD = os.getenv("WAKE_WORD")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = "gemini-2.0-flash-lite"

# Path to the configuration file
CONFIG_PATH = Path(__file__).parent.parent / "config" / "modes.json"

# Current active mode
current_mode = "default"

def load_modes_config():
    """Load the modes configuration from the JSON file"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading modes config: {e}")
        # Return a minimal default config if the file can't be loaded
        return {
            "default": {
                "name": "Default GRIT",
                "personality_file": "prompts/grit_personality.txt",
                "voice": {
                    "model": "gpt-4o-mini-tts",
                    "voice": "coral",
                    "instructions": None
                }
            }
        }

def get_current_mode_config():
    """Get the configuration for the current active mode"""
    modes = load_modes_config()
    return modes.get(current_mode, modes.get("default"))

def set_mode(mode_name):
    """Set the current active personality mode"""
    global current_mode
    modes = load_modes_config()
    
    if mode_name in modes:
        current_mode = mode_name
        config = modes[mode_name]
        print(f"Switched to {config['name']} mode")
        return True
    else:
        print(f"Mode '{mode_name}' not found. Available modes: {', '.join(modes.keys())}")
        return False

def get_personality_prompt():
    """Load the personality prompt for the current mode"""
    config = get_current_mode_config()
    prompt_path = Path(__file__).parent.parent / config["personality_file"]
    
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Personality file not found: {prompt_path}")
        return "You are GRIT, a helpful assistant."

def get_voice_settings():
    """Get the voice settings for the current mode"""
    config = get_current_mode_config()
    return config.get("voice", {})

def list_available_modes():
    """Return a list of available modes"""
    modes = load_modes_config()
    return [(name, config.get("name", name)) for name, config in modes.items()]

# Initialize with default mode
set_mode("default")

def ask_llm(prompt):
    """
    Send a prompt to the LLM and return the response.
    """
    try:
        print(f"Sending prompt to LLM: {prompt}")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt)
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[
                types.Part.from_text(text=get_personality_prompt())],
        )

        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")
            response_text += chunk.text
            
        print(f"LLM response: {response_text}")
        return True, response_text
        
    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return False, None
