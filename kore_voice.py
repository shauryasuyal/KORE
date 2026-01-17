import speech_recognition as sr
import pyttsx3
import threading
import queue

class KoreVoice:
    """Handles speech recognition and text-to-speech for Kore"""
    
    def __init__(self):
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self.setup_voice()
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise on initialization
        print("   [Voice] Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("   [Voice] Ready!")
        
        # Queue for speech output to avoid blocking
        self.speech_queue = queue.Queue()
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        
        self.is_listening = False
        self.wake_word = "kore"
    
    def setup_voice(self):
        """Configure TTS voice properties"""
        voices = self.tts_engine.getProperty('voices')
        
        # Try to find a good voice (prefer female voice for Kore)
        for voice in voices:
            if "zira" in voice.name.lower() or "hazel" in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Set speech rate and volume
        self.tts_engine.setProperty('rate', 175)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    def speak(self, text):
        """Add text to speech queue (non-blocking)"""
        if text:
            self.speech_queue.put(text)
    
    def speak_now(self, text):
        """Speak immediately (blocking)"""
        if text:
            print(f"   [Kore Speaking] {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
    
    def _speech_worker(self):
        """Background worker for processing speech queue"""
        while True:
            try:
                text = self.speech_queue.get()
                if text:
                    print(f"   [Kore Speaking] {text}")
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                self.speech_queue.task_done()
            except Exception as e:
                print(f"   [Voice Error] {e}")
    
    def listen_once(self, timeout=5):
        """Listen for a single command"""
        print("   [Voice] Listening...")
        
        try:
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            # Recognize speech using Google Speech Recognition
            print("   [Voice] Processing...")
            text = self.recognizer.recognize_google(audio)
            print(f"   [Voice] Heard: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("   [Voice] Timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            print("   [Voice] Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"   [Voice] Recognition error: {e}")
            return None
        except Exception as e:
            print(f"   [Voice] Error: {e}")
            return None
    
    def listen_for_wake_word(self, callback):
        """Continuously listen for wake word in background"""
        def listen_loop():
            print(f"   [Voice] Listening for wake word '{self.wake_word}'...")
            
            while True:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    
                    text = self.recognizer.recognize_google(audio).lower()
                    
                    if self.wake_word in text:
                        print(f"   [Voice] Wake word detected!")
                        callback()
                        
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    continue
                except Exception as e:
                    print(f"   [Voice] Wake word error: {e}")
                    continue
        
        # Run in background thread
        wake_thread = threading.Thread(target=listen_loop, daemon=True)
        wake_thread.start()
    
    def stop_speaking(self):
        """Stop current speech"""
        self.tts_engine.stop()
    
    def get_command_with_wake_word(self, timeout=5):
        """Listen for wake word followed by command"""
        print(f"   [Voice] Say '{self.wake_word}' followed by your command...")
        
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio).lower()
            print(f"   [Voice] Heard: {text}")
            
            # Check if wake word is in the text
            if self.wake_word in text:
                # Extract command after wake word
                wake_index = text.find(self.wake_word)
                command = text[wake_index + len(self.wake_word):].strip()
                
                if command:
                    print(f"   [Voice] Command extracted: {command}")
                    return command
                else:
                    print("   [Voice] No command after wake word")
                    return None
            else:
                print(f"   [Voice] Wake word '{self.wake_word}' not detected")
                return None
                
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"   [Voice] Error: {e}")
            return None
        except Exception as e:
            print(f"   [Voice] Error: {e}")
            return None