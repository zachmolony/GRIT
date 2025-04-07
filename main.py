# lib/stt.py
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import os
from google import genai
from google.genai import types

WAKE_WORD = "barry"

client = genai.Client(api_key="test")
model = "gemini-2.0-flash-lite"

with open("prompts/grit_personality.txt", "r") as file:
    SYSTEM_PROMPT = file.read()


def ask_grit(user_input: str) -> str:
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_input)
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text=SYSTEM_PROMPT)],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")



def ask_llm(prompt):
    """
    Send a prompt to the LLM and return the response.
    """
    try:
        print(f"Sending prompt to LLM: {prompt}")
        response = ask_grit(prompt)
        print(f"LLM response: {response}")
        return True, response
    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return False, None

def resolve_command_locally(text):
    """
    Check if the command can be resolved locally (e.g., CRT commands, lights, music/video commands).
    Returns a tuple (handled, response). If handled is True, response can be spoken directly.
    """
    text = text.lower()

    # Basic CRT controls
    if "turn on the crt" in text:
        print("Turning on the CRT wall.")

        # send message to the smart plug

        return True
    

    # if "turn off the crt" in text:
    #     return True, "CRT powered down. Enjoy the blackout, mate."
    # if "vibe mode" in text:
    #     return True, "Setting vibe mode. Let's get those lazy lights on and screens aglow."
    # if "shut up barry" in text:
    #     return True, "Alright, quiet mode activated. I'll zip it for a bit."

    # # Music and video commands
    # if "play some" in text:
    #     # Check for genre-specific commands
    #     if "rock" in text:
    #         return True, "Cranking up some rock—hope you like loud riffs and headbanging."
    #     if "pop" in text:
    #         return True, "Playing some pop tunes—let's get those catchy hooks going."
    #     if "jazz" in text:
    #         return True, "Setting the mood with a bit of jazz—smooth and soulful."
    #     if "hip hop" in text or "rap" in text:
    #         return True, "Dropping some hip hop beats—get ready to vibe."
    #     if "anime" in text:
    #         return True, "Switching the CRT wall to anime mode—time for some retro otaku classics."
    #     # If no specific genre is mentioned, use a default response
    #     return True, "Playing some tunes—let's see if it clears out the cobwebs."

    # Add other local commands as needed...
    
    return False, None

def listen(mic, rec):
    print("Listening...")
    while True:
        data = mic.read(4096, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            return result.get("text", "")
        

def main():
    print("Starting speech recognition...")
    model = Model("models/en-gb/")
    rec = KaldiRecognizer(model, 16000)
    p_audio = pyaudio.PyAudio()
    mic = p_audio.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=8192)
    mic.start_stream()
    
    try:
        while True:
            text = listen(mic, rec)
            if text:
                print(f"Recognized: {text}")
                
                if WAKE_WORD in text.lower():
                    print(f"Wake word '{WAKE_WORD}' detected!")

                    # Remove the wake word from the text
                    text = text.lower().replace(WAKE_WORD, "grit").strip()

                    print(f"Command after wake word: {text}")

                    if not text:
                        print("No command detected after wake word.")
                        continue

                    # Here we decypher the command
                    handled, response = resolve_command_locally(text)
                    if handled:
                        print(f"Local command handled: {response}")
                    else:
                        print("Command not handled locally, sending to LLM...")
                        # Send the command to the LLM
                        handled, response = ask_llm(text)
                        if handled:
                            print(f"LLM handled the command: {response}")
                        else:
                            print("LLM could not handle the command, that sucks.")


            else:
                print("No speech detected.")
            break
    finally:
        mic.stop_stream()
        mic.close()
        p_audio.terminate()

if __name__ == "__main__":
    main()
