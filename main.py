from anatomy.ears import listen, initialize_speech_recognition, cleanup_speech_recognition
from anatomy.brain import ask_llm
from anatomy.mouth import speak

import os

WAKE_WORD = os.getenv("WAKE_WORD")

def resolve_command_locally(text):
    """
    Check if the command can be resolved locally (e.g., CRT commands, lights, music/video commands).
    Returns a tuple (handled, response). If handled is True, response can be spoken directly.
    """
    text = text.lower()

    # Basic CRT controls
    if "turn on the crt" in text:
        print("Turning on the CRT wall.")

        return True, False
    
    return False, None

def main():
    try:
        initialize_speech_recognition()
        
        while True:
            try:
                text = listen()
                if text:
                    print(f"Recognized: {text}")
                    
                    if WAKE_WORD in text.lower():
                        print(f"Wake word '{WAKE_WORD}' detected!")

                        if "shut down" in text.lower():
                            # todo: add some kind of confirmation
                            print("Shutdown command detected.")
                            break

                        text = text.lower().replace(WAKE_WORD, "grit").strip()

                        print(f"Command after wake word: {text}")

                        if not text:
                            print("No command detected after wake word.")
                            continue

                        handled, response = resolve_command_locally(text)
                        if handled:
                            print(f"Local command handled: {response}")

                        else:
                            print("Command not handled locally, sending to LLM...")

                            handled, response = ask_llm(text)
                            if handled:
                                print(f"LLM handled the command")

                                if response:
                                    print(f"LLM response: {response}")
                                    speak(response)
                                    
                            else:
                                print("LLM could not handle the command, that sucks.")

            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Attempting to recover...")
                
                # Try to restart the audio system
                try:
                    cleanup_speech_recognition()
                    initialize_speech_recognition()
                except Exception as recovery_error:
                    print(f"Failed to recover: {recovery_error}")
                    # Wait a moment before trying again
                    import time
                    time.sleep(1)
    finally:
        try:
            cleanup_speech_recognition()
        except Exception as e:
            print(f"Error during final cleanup: {e}")

if __name__ == "__main__":
    main()
