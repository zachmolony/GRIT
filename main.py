from anatomy.ears import listen, listen_for_command, initialize_speech_recognition, cleanup_speech_recognition
from anatomy.brain import ask_llm, set_mode, list_available_modes
from anatomy.mouth import speak

import os
import time  # Add this import if not already present

WAKE_WORD = os.getenv("WAKE_WORD")

def resolve_command_locally(text):
    """
    Check if the command can be resolved locally (e.g., CRT commands, lights, music/video commands).
    Returns a tuple (handled, response). If handled is True, response can be spoken directly.
    """
    text = text.lower()

    # Mode switching commands
    if any(phrase in text for phrase in ["yard man mode", "yardman mode", "jamaican mode"]):
        print("Switching to Yardman mode...")
        success = set_mode("yardman")
        if success:
            return True, "Yardman mode activated. Mi ready fi chat wid yuh now, seen?"
        else:
            return True, "Could not switch to Yardman mode. Staying in current mode."
    
    # Switch back to default mode
    elif any(phrase in text for phrase in ["default mode", "normal mode", "standard mode"]):
        print("Switching to default mode...")
        success = set_mode("default")
        if success:
            return True, "Back to default mode. What's up, fam?"
        else:
            return True, "Could not switch to default mode."
            
    # List available modes
    elif "list modes" in text or "what modes do you have" in text:
        modes = list_available_modes()
        mode_names = ", ".join([f"{mode[1]}" for mode in modes])
        return True, f"I have these different personalities: {mode_names}. Just say the mode name followed by 'mode' to switch."
    
    # Basic CRT controls
    elif "turn on the crt" in text:
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
                        
                        initial_command = text.lower().replace(WAKE_WORD, "").strip()
                        print(f"Initial command part: '{initial_command}'")
                        
                        # Get additional command parts by continuing to listen
                        additional_speech = listen_for_command(timeout=3.0, silence_limit=1.0)
                        
                        # Combine the initial part and any additional speech
                        command = f"{initial_command} {additional_speech}".strip()
                        print(f"Full command: '{command}'")

                        if "shut down" in command:
                            print("Shutdown command detected.")
                            break

                        print(f"Processing command: {command}")

                        if not command:
                            print("No command detected after wake word.")
                            continue

                        handled, response = resolve_command_locally(command)
                        if handled:
                            print(f"Local command handled: {response}")

                        if response:
                            print(f"Local response: {response}")
                            
                            # Cleanup before speaking to prevent resource conflicts
                            cleanup_speech_recognition()
                            
                            speak(response)
                            
                            time.sleep(0.5)
                            
                            initialize_speech_recognition()
                            continue  # Skip the rest of the loop and start listening again
                            
                        else:
                            print("Command not handled locally, sending to LLM...")
                            
                            handled, response = ask_llm(command)
                            if handled:
                                print(f"LLM handled the command")

                                if response:
                                    print(f"LLM response: {response}")
                                    
                                    # Same pattern: cleanup, speak, delay, reinitialize
                                    cleanup_speech_recognition()
                                    speak(response)
                                    time.sleep(0.5)
                                    initialize_speech_recognition()
                                    
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
                    time.sleep(1)
    finally:
        try:
            cleanup_speech_recognition()
        except Exception as e:
            print(f"Error during final cleanup: {e}")

if __name__ == "__main__":
    main()
