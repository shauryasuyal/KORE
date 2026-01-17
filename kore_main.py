import sys
import threading
import time
import json
import os
import pyautogui
import subprocess
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import google.generativeai as genai

from kore_overlay import KoreOverlay
from kore_voice import KoreVoice
from kore_control import (
    click_desktop_icon, find_file_in_system, open_google_search, 
    run_terminal_command, create_file, create_folder, delete_file,
    edit_file, read_file, copy_file, move_file, list_files,
    get_system_info, kill_process, take_screenshot, open_url,
    open_application, open_folder, empty_recycle_bin, organize_files,
    change_wallpaper
)

API_KEY = "AIzaSyDF08pS9foVBRpEpQpK7hp9vvqh1PvmKoE"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

overlay_instance = None
voice_instance = None
voice_mode = False
command_lock = threading.Lock()  # Prevent concurrent command execution

def ask_gemini(user_input):
    """Enhanced AI decision making with system context"""
    print("\n   [Brain] Analyzing...")
    
    username = os.environ.get('USERNAME', 'User')
    computer_name = os.environ.get('COMPUTERNAME', 'Unknown')
    
    prompt = f"""
    You are Kore, an advanced AI Assistant with full Windows system control.
    You are friendly, helpful, and conversational. You can chat casually AND perform system tasks.
    
    SYSTEM CONTEXT:
    - Computer Name: {computer_name}
    - Username: {username}
    - User Desktop Path: C:\\Users\\{username}\\Desktop
    - User Documents Path: C:\\Users\\{username}\\Documents
    - User Downloads Path: C:\\Users\\{username}\\Downloads
    
    User Input: "{user_input}"
    
    AVAILABLE TOOLS:
    1. OPEN_APP: Opens applications (param: "app_name" like "Settings", "Chrome", "Task Manager", "WiFi Settings", "Network Settings")
    2. OPEN_FOLDER: Opens folders (param: "Downloads", "Documents", "Desktop", or any path)
    3. FIND_FILE: Finds files (param: "filename")
    4. CREATE_FILE: Creates file (params: {{"path": "Desktop\\\\notes.txt", "content": "..."}})
       - Use smart paths: "Desktop\\\\filename" NOT "C:\\\\Users\\\\...\\\\Desktop\\\\filename"
    5. CREATE_FOLDER: Creates directory (param: "Desktop\\\\NewFolder")
       - Use smart paths: "Desktop\\\\foldername" NOT full paths
    6. DELETE_FILE: Deletes file/folder (param: "file_path")
    7. EDIT_FILE: Modifies file (params: {{"path": "...", "content": "...", "mode": "append/overwrite"}})
    8. READ_FILE: Reads file content (param: "file_path")
    9. COPY_FILE: Copies file (params: {{"source": "...", "destination": "..."}})
    10. MOVE_FILE: Moves file (params: {{"source": "...", "destination": "..."}})
    11. LIST_FILES: Lists directory contents (param: "directory_path")
    12. GOOGLE: Web search (param: "query")
    13. OPEN_URL: Opens URL (param: "https://...")
    14. RUN_CMD: System command (param: "command")
    15. SYSTEM_INFO: Gets system info (param: "cpu/memory/disk/network/battery/basic/all")
    16. KILL_PROCESS: Terminates process (param: "process_name")
    17. SCREENSHOT: Takes screenshot (param: "save_path" or null)
    18. EMPTY_RECYCLE_BIN: Empties the Recycle Bin (param: null)
    19. ORGANIZE_FILES: Organizes files in a folder by type into subfolders
        - Param: "folder_path" (e.g., "Downloads", "Desktop\\\\MyFolder", or full path)
        - Creates subfolders: Images, Videos, Audio, Documents, Spreadsheets, Presentations, Archives, Code, Executables, Others
        - Automatically sorts all files into appropriate categories
    20. CHANGE_WALLPAPER: Changes desktop wallpaper
        - Param: null for random Windows default wallpaper, OR specific image path/name
        - Examples: null (random default), "Pictures\\\\sunset.jpg", "myimage.png"
        - Supports smart paths and will search for image if just name given
    21. CHAT: For casual conversation, greetings, questions about yourself, or non-task queries
        - Param: null (just respond conversationally)
    
    IMPORTANT RULES:
    - If the user is just chatting, asking how you are, making small talk, or asking non-task questions, use the CHAT tool
    - For CREATE_FILE and CREATE_FOLDER: Use smart paths like "Desktop\\\\file.txt" or "Documents\\\\folder"
    - When user says "on desktop" or "in documents", use paths like "Desktop\\\\filename" NOT full C:\\ paths
    - Use OPEN_FOLDER for "Downloads", "Documents", "Desktop", etc.
    - Use OPEN_APP for "Chrome", "Notepad", "Settings", "Task Manager", etc.
    - For specific settings pages like WiFi or Bluetooth, use OPEN_APP with "WiFi Settings", "Bluetooth Settings", etc.
    - Use SYSTEM_INFO when asked about computer specs, name, performance, battery, etc.
    - Use EMPTY_RECYCLE_BIN when user asks to empty trash or recycle bin
    - Use ORGANIZE_FILES when user asks to organize, sort, or clean up files in a folder
    - Use CHANGE_WALLPAPER with null param when asked to "change wallpaper" without specifics
    - Use CHANGE_WALLPAPER with image path when user specifies which image to use
    - Be friendly and conversational in your "thought" field even when performing tasks
    - Keep your "thought" responses concise and natural for voice output (under 20 words)
    
    Return ONLY valid JSON:
    {{
        "thought": "Brief reasoning or conversational response",
        "tool": "TOOL_NAME or CHAT",
        "parameter": "value or dict object or null"
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        
        # Validate the response structure
        if not isinstance(result, dict):
            raise ValueError("Response is not a dictionary")
        if "thought" not in result or "tool" not in result or "parameter" not in result:
            raise ValueError("Missing required fields in response")
            
        return result
    except json.JSONDecodeError as e:
        print(f"   [Brain Error] Invalid JSON: {e}")
        print(f"   [Brain Error] Response was: {text[:200]}")
        return None
    except Exception as e:
        print(f"   [Brain Error] {e}")
        return None

def execute_action(tool, param, speak=False):
    """Executes the AI's chosen action"""
    success = False
    
    try:
        if tool == "CHAT":
            success = True
            return
        
        elif tool == "OPEN_APP":
            coords = click_desktop_icon(param)
            if coords:
                if overlay_instance: 
                    overlay_instance.set_hand_target(coords[0], coords[1])
                time.sleep(0.8)
                pyautogui.click(coords[0], coords[1])
                time.sleep(0.1)
                pyautogui.doubleClick(coords[0], coords[1])
                print(f"   [Success] Opened {param}")
                if speak and voice_instance:
                    voice_instance.speak(f"Opening {param}")
                time.sleep(0.5)
                if overlay_instance: 
                    overlay_instance.set_hand_target(1900, 1000)
                success = True
            else:
                success = open_application(param)
                if success and speak and voice_instance:
                    voice_instance.speak(f"Opening {param}")
                if not success:
                    print("   [Error] Could not open application")
                    if speak and voice_instance:
                        voice_instance.speak(f"Sorry, I couldn't find {param}")
        
        elif tool == "OPEN_FOLDER":
            success = open_folder(param)
            if success and speak and voice_instance:
                voice_instance.speak(f"Opening {param} folder")
            elif not success and speak and voice_instance:
                voice_instance.speak(f"Couldn't open {param}")
        
        elif tool == "FIND_FILE":
            path = find_file_in_system(param)
            if path:
                print(f"   [Success] Found: {path}")
                subprocess.Popen(f'explorer /select,"{path}"')
                if speak and voice_instance:
                    voice_instance.speak(f"Found {param}")
                success = True
            else:
                print("   [Error] File not found")
                if speak and voice_instance:
                    voice_instance.speak(f"Couldn't find {param}")
        
        elif tool == "CREATE_FILE":
            if isinstance(param, dict):
                result = create_file(param.get("path"), param.get("content", ""))
                success = result is not None
                if success and speak and voice_instance:
                    voice_instance.speak("File created successfully")
            else:
                print("   [Error] Invalid parameters for CREATE_FILE")
        
        elif tool == "CREATE_FOLDER":
            result = create_folder(param)
            success = result is not None
            if success and speak and voice_instance:
                voice_instance.speak("Folder created")
        
        elif tool == "DELETE_FILE":
            success = delete_file(param)
            if success and speak and voice_instance:
                voice_instance.speak("Deleted successfully")
        
        elif tool == "EDIT_FILE":
            if isinstance(param, dict):
                success = edit_file(param.get("path"), param.get("content"), param.get("mode", "append"))
                if success and speak and voice_instance:
                    voice_instance.speak("File updated")
            else:
                print("   [Error] Invalid parameters for EDIT_FILE")
        
        elif tool == "READ_FILE":
            content = read_file(param)
            if content:
                print(f"   [Content Preview] {content[:200]}...")
                if speak and voice_instance:
                    preview = content[:100]
                    voice_instance.speak(f"Reading file: {preview}")
                success = True
        
        elif tool == "COPY_FILE":
            if isinstance(param, dict):
                success = copy_file(param.get("source"), param.get("destination"))
                if success and speak and voice_instance:
                    voice_instance.speak("File copied")
            else:
                print("   [Error] Invalid parameters for COPY_FILE")
        
        elif tool == "MOVE_FILE":
            if isinstance(param, dict):
                success = move_file(param.get("source"), param.get("destination"))
                if success and speak and voice_instance:
                    voice_instance.speak("File moved")
            else:
                print("   [Error] Invalid parameters for MOVE_FILE")
        
        elif tool == "LIST_FILES":
            files = list_files(param)
            if files:
                print(f"   [Files] {', '.join(files[:10])}")
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more")
                if speak and voice_instance:
                    voice_instance.speak(f"Found {len(files)} items")
                success = True
        
        elif tool == "GOOGLE":
            open_google_search(param)
            if speak and voice_instance:
                voice_instance.speak(f"Searching for {param}")
            success = True
        
        elif tool == "OPEN_URL":
            open_url(param)
            if speak and voice_instance:
                voice_instance.speak("Opening URL")
            success = True
        
        elif tool == "RUN_CMD":
            output = run_terminal_command(param)
            print(f"   [CMD Output] \n{output[:300]}...")
            if speak and voice_instance:
                voice_instance.speak("Command executed")
            success = True
        
        elif tool == "SYSTEM_INFO":
            info = get_system_info(param if param and param != "null" else "all")
            if info:
                print(f"   [System Info] {json.dumps(info, indent=2)}")
                if speak and voice_instance:
                    # Provide spoken summary of key info
                    if "cpu_percent" in info:
                        voice_instance.speak(f"CPU usage is at {info['cpu_percent']} percent")
                    elif "memory_percent" in info:
                        voice_instance.speak(f"Memory usage is at {info['memory_percent']} percent")
                    else:
                        voice_instance.speak("System info retrieved")
                success = True
        
        elif tool == "KILL_PROCESS":
            success = kill_process(param)
            if success and speak and voice_instance:
                voice_instance.speak(f"Terminated {param}")
        
        elif tool == "SCREENSHOT":
            path = take_screenshot(param if param and param != "null" else None)
            if path:
                print(f"   [Screenshot] Saved to {path}")
                if speak and voice_instance:
                    voice_instance.speak("Screenshot captured")
                success = True
        
        elif tool == "EMPTY_RECYCLE_BIN":
            success = empty_recycle_bin()
            if success and speak and voice_instance:
                voice_instance.speak("Recycle bin emptied")
        
        elif tool == "ORGANIZE_FILES":
            success = organize_files(param)
            if success and speak and voice_instance:
                voice_instance.speak("Files organized")
        
        elif tool == "CHANGE_WALLPAPER":
            success = change_wallpaper(param if param and param != "null" else None)
            if success and speak and voice_instance:
                voice_instance.speak("Wallpaper changed")
        
        else:
            print(f"   [Error] Unknown tool: {tool}")
            if speak and voice_instance:
                voice_instance.speak("Sorry, I don't know how to do that")
    
    except Exception as e:
        print(f"   [Execution Error] {e}")
        success = False
        if speak and voice_instance:
            voice_instance.speak("Sorry, something went wrong")
    
    # Update emotion based on success
    if overlay_instance:
        if success:
            overlay_instance.set_emotion('happy')
            time.sleep(1.5)
            overlay_instance.set_emotion('idle')
        else:
            overlay_instance.set_emotion('sad')
            time.sleep(1.5)
            overlay_instance.set_emotion('idle')

def handle_voice_command():
    """Handle voice command when sprite is double-clicked or Shift+Enter is pressed"""
    global voice_mode
    
    # Prevent concurrent voice commands
    if not command_lock.acquire(blocking=False):
        print("   [Voice] Already processing a command, please wait...")
        return
    
    try:
        if not voice_instance:
            print("   [Error] Voice system not initialized")
            return
        
        voice_mode = True
        
        if overlay_instance:
            overlay_instance.set_listening(True)
        
        # Listen for command
        voice_instance.speak("Yes? I'm listening")
        command = voice_instance.listen_once(timeout=8)
        
        if overlay_instance:
            overlay_instance.set_listening(False)
        
        if command:
            print(f"\n   [Voice Command] {command}")
            process_command(command, speak=True)
        else:
            if overlay_instance:
                overlay_instance.set_emotion('sad')
            voice_instance.speak("I didn't catch that")
            time.sleep(1.5)
            if overlay_instance:
                overlay_instance.set_emotion('idle')
        
        voice_mode = False
        
    finally:
        command_lock.release()

def process_command(command, speak=False):
    """Process a command (from text or voice)"""
    if not command or not command.strip():
        return
    
    if overlay_instance:
        overlay_instance.set_emotion('thinking')
    
    plan = ask_gemini(command)
    if not plan:
        if overlay_instance:
            overlay_instance.set_emotion('sad')
            time.sleep(1.5)
            overlay_instance.set_emotion('idle')
        if speak and voice_instance:
            voice_instance.speak("Sorry, I had trouble understanding that")
        return
    
    # Speak the thought
    thought = plan.get('thought', 'Processing...')
    print(f"KORE: {thought}")
    if speak and voice_instance and overlay_instance:
        overlay_instance.set_speaking(True)
        voice_instance.speak(thought)
        overlay_instance.set_speaking(False)
    
    # Execute the action
    execute_action(plan.get('tool'), plan.get('parameter'), speak=speak)

def logic_thread():
    """Main logic loop for text input"""
    time.sleep(2)
    print("\n" + "="*60)
    print(" KORE ADVANCED SYSTEM ASSISTANT ONLINE")
    print(" - Type commands in this console")
    print(" - Press Shift+Enter for voice mode")
    print(" - Double-click Kore avatar for voice mode")
    print(" - Type 'exit' to quit")
    print("="*60 + "\n")
    
    while True:
        try:
            command = input("YOU: ")
            if command.lower() in ['exit', 'quit', 'q']:
                print("\n   [System] Shutting down Kore...")
                sys.exit()
            
            if command.strip():
                threading.Thread(target=process_command, args=(command, False), daemon=True).start()
            
        except EOFError:
            # Handle Ctrl+C or input closure
            break
        except Exception as e:
            print(f"   [Loop Error] {e}")
            if overlay_instance:
                overlay_instance.set_emotion('sad')
                time.sleep(1.5)
                overlay_instance.set_emotion('idle')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Initialize voice system
    try:
        print("   [System] Initializing voice recognition...")
        voice_instance = KoreVoice()
        print("   [System] Voice system ready!")
    except Exception as e:
        print(f"   [Warning] Voice system failed to initialize: {e}")
        print("   [Warning] Voice features will be disabled")
        print("   [Warning] Make sure you have installed: pip install SpeechRecognition pyttsx3 pyaudio")
        voice_instance = None
    
    # Initialize overlay
    screen = app.primaryScreen()
    screen_size = screen.size()
    
    overlay = KoreOverlay()
    overlay.setGeometry(0, 0, screen_size.width(), screen_size.height())
    
    # Make sure it's on top and visible
    overlay.raise_()
    overlay.activateWindow()
    
    # Connect signals to voice command handler
    overlay.double_click.connect(lambda: threading.Thread(target=handle_voice_command, daemon=True).start())
    overlay.voice_hotkey.connect(lambda: threading.Thread(target=handle_voice_command, daemon=True).start())
    
    overlay.show()
    overlay_instance = overlay
    
    print(f"\n   [System] Overlay created at size: {screen_size.width()}x{screen_size.height()}")
    print(f"   [System] Look for Kore in the BOTTOM LEFT corner of your screen!")
    print(f"   [System] Press Shift+Enter or Double-click the laptop avatar for voice mode\n")
    
    # Start text input thread
    thread = threading.Thread(target=logic_thread, daemon=True)
    thread.start()
    
    sys.exit(app.exec())