import google.generativeai as genai
import json

# --- CONFIGURATION ---
API_KEY = "AIzaSyBJLtqEVxuADFyKoSSV8bYUOv_rVt3I3o0" 

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def decide_action(user_command, context=None):
    """
    Enhanced decision maker with expanded capabilities
    """
    
    prompt = f"""
    You are Kore, an advanced AI OS Assistant with full system control.
    
    User Command: "{user_command}"
    {f"Context: {context}" if context else ""}
    
    AVAILABLE TOOLS:
    1. OPEN_APP: Opens installed applications (Settings, Calculator, Task Manager, etc.)
       - Param: "app_name" (e.g., "Settings", "Chrome", "Notepad", "Task Manager", "Control Panel")
    
    2. OPEN_FOLDER: Opens system folders or any folder path
       - Param: "folder_name" (e.g., "Downloads", "Documents", "Desktop", "C:\\path\\to\\folder")
    
    3. FIND_FILE: Searches for files anywhere in the system
       - Param: "filename" (supports wildcards)
    
    3. CREATE_FILE: Creates a new file with content
       - Params: {{"path": "C:\\\\path\\\\to\\\\file.txt", "content": "text"}}
    
    4. CREATE_FOLDER: Creates a new directory
       - Param: "folder_path"
    
    5. DELETE_FILE: Deletes a file or folder
       - Param: "file_path"
    
    6. EDIT_FILE: Appends or modifies file content
       - Params: {{"path": "file.txt", "content": "new text", "mode": "append/overwrite"}}
    
    7. RUN_CMD: Executes system commands
       - Param: "command"
    
    8. GOOGLE: Searches the web
       - Param: "search query"
    
    9. OPEN_URL: Opens a specific URL in browser
       - Param: "https://example.com"
    
    10. LIST_FILES: Lists files in a directory
        - Param: "directory_path"
    
    11. SYSTEM_INFO: Gets system information
        - Param: "cpu/memory/disk/network/all"
    
    12. KILL_PROCESS: Terminates a running process
        - Param: "process_name"
    
    13. SCREENSHOT: Takes a screenshot
        - Param: "save_path" (optional)
    
    14. READ_FILE: Reads file content
        - Param: "file_path"
    
    15. COPY_FILE: Copies a file
        - Params: {{"source": "path1", "destination": "path2"}}
    
    16. MOVE_FILE: Moves a file
        - Params: {{"source": "path1", "destination": "path2"}}
    
    Return ONLY valid JSON:
    {{
        "thought": "Brief reasoning",
        "tool": "TOOL_NAME",
        "parameter": "value or dict"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        print(f"   [Brain Error] {e}")
        return None