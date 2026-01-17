import os
import subprocess
import webbrowser
import shutil
import psutil
import pyautogui
from datetime import datetime
from pywinauto import Desktop
import json

# --- MEMORY SYSTEM ---
def load_memory():
    """Loads Kore's memory file"""
    try:
        with open('kore_memory.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "common_locations": {},
            "user_preferences": {},
            "learned_commands": {}
        }

def save_memory(memory):
    """Saves Kore's memory"""
    try:
        with open('kore_memory.json', 'w') as f:
            json.dump(memory, indent=2, fp=f)
    except Exception as e:
        print(f"   [Memory Error] Could not save: {e}")

def click_desktop_icon(icon_name):
    """Finds and returns coordinates of desktop icon"""
    try:
        print(f"   [System] Searching Desktop for: '{icon_name}'...")
        desktop = Desktop(backend="uia").window(title="Program Manager")
        icon_list = desktop.child_window(title="Desktop", control_type="List")
        target_icon = icon_list.child_window(title=icon_name, control_type="ListItem")
        
        rect = target_icon.rectangle()
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        return (center_x, center_y)
    except Exception as e:
        print(f"   [Error] Icon not found: {e}")
        return None

def find_file_in_system(filename):
    """Searches for file OR folder using PowerShell - Enhanced for system-wide search"""
    print(f"   [System] Searching for '{filename}'...")
    
    # Search in multiple root locations
    search_paths = [
        r"C:\Users",      # User files
        r"C:\Windows",    # System files
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\\"          # Entire C drive as last resort
    ]
    
    safe_filename = f"*{filename}*"
    
    for search_path in search_paths:
        print(f"   [System] Searching in {search_path}...")
        
        # PowerShell command that searches for BOTH files and directories
        # -Directory flag searches for folders, without it searches for files
        # We'll do both in one go
        ps_command = f'''powershell -command "
        $items = Get-ChildItem -Path '{search_path}' -Filter '{safe_filename}' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
        if ($items) {{ $items }} else {{ '' }}
        "'''
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(ps_command, capture_output=True, text=True, startupinfo=startupinfo, timeout=15)
            found_path = result.stdout.strip()
            
            if found_path:
                print(f"   [Success] Found at: {found_path}")
                return found_path
                
        except subprocess.TimeoutExpired:
            print(f"   [Warning] Search timeout in {search_path}, trying next location...")
            continue
        except Exception as e:
            print(f"   [Error] {e}")
            continue
    
    # Fallback: If "Cursors" failed, try searching just the first word
    if " " in filename:
        first_part = filename.split(" ")[0]
        print(f"   [System] Trying fallback: '{first_part}'...")
        return find_file_in_system(first_part)
    
    print(f"   [Error] Could not find '{filename}' anywhere")
    return None

def create_file(path, content=""):
    """Creates a new file with optional content - Handles smart path resolution"""
    try:
        # Smart path resolution for common locations
        username = os.environ.get('USERNAME', 'User')
        
        # If path doesn't contain a drive letter or absolute path, check for keywords
        if not (":\\" in path or path.startswith("\\\\")):
            path_lower = path.lower()
            
            # Map common location keywords to actual paths
            location_map = {
                "desktop": f"C:\\Users\\{username}\\Desktop",
                "documents": f"C:\\Users\\{username}\\Documents",
                "downloads": f"C:\\Users\\{username}\\Downloads",
                "pictures": f"C:\\Users\\{username}\\Pictures",
                "videos": f"C:\\Users\\{username}\\Videos",
                "music": f"C:\\Users\\{username}\\Music",
            }
            
            # Check if the path starts with a common location
            for location, real_path in location_map.items():
                if path_lower.startswith(location):
                    # Replace the location keyword with the actual path
                    remaining_path = path[len(location):].lstrip("\\/")
                    path = os.path.join(real_path, remaining_path)
                    break
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Create the file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   [Success] Created: {path}")
        return path
    except Exception as e:
        print(f"   [Error] {e}")
        return None

def create_folder(path):
    """Creates a new directory - Handles smart path resolution"""
    try:
        # Smart path resolution for common locations
        username = os.environ.get('USERNAME', 'User')
        
        # If path doesn't contain a drive letter or absolute path, check for keywords
        if not (":\\" in path or path.startswith("\\\\")):
            path_lower = path.lower()
            
            # Map common location keywords to actual paths
            location_map = {
                "desktop": f"C:\\Users\\{username}\\Desktop",
                "documents": f"C:\\Users\\{username}\\Documents",
                "downloads": f"C:\\Users\\{username}\\Downloads",
                "pictures": f"C:\\Users\\{username}\\Pictures",
                "videos": f"C:\\Users\\{username}\\Videos",
                "music": f"C:\\Users\\{username}\\Music",
            }
            
            # Check if the path starts with a common location
            for location, real_path in location_map.items():
                if path_lower.startswith(location):
                    # Replace the location keyword with the actual path
                    remaining_path = path[len(location):].lstrip("\\/")
                    path = os.path.join(real_path, remaining_path)
                    break
        
        os.makedirs(path, exist_ok=True)
        print(f"   [Success] Created folder: {path}")
        return path
    except Exception as e:
        print(f"   [Error] {e}")
        return None

def delete_file(path):
    """Deletes a file or folder"""
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        print(f"   [Success] Deleted: {path}")
        return True
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def edit_file(path, content, mode="append"):
    """Edits file content"""
    try:
        file_mode = 'a' if mode == "append" else 'w'
        with open(path, file_mode, encoding='utf-8') as f:
            f.write(content)
        print(f"   [Success] Modified: {path}")
        return True
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def read_file(path):
    """Reads file content"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"   [Success] Read {len(content)} characters from {path}")
        return content
    except Exception as e:
        print(f"   [Error] {e}")
        return None

def copy_file(source, destination):
    """Copies a file"""
    try:
        shutil.copy2(source, destination)
        print(f"   [Success] Copied: {source} -> {destination}")
        return True
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def move_file(source, destination):
    """Moves a file"""
    try:
        shutil.move(source, destination)
        print(f"   [Success] Moved: {source} -> {destination}")
        return True
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def list_files(directory):
    """Lists files in directory"""
    try:
        files = os.listdir(directory)
        print(f"   [Success] Found {len(files)} items in {directory}")
        return files
    except Exception as e:
        print(f"   [Error] {e}")
        return None

def get_system_info(info_type="all"):
    """Gets comprehensive system information"""
    try:
        import platform
        import socket
        
        info = {}
        
        if info_type in ["basic", "all"]:
            # Computer identification
            info["computer_name"] = socket.gethostname()
            info["username"] = os.environ.get('USERNAME', 'Unknown')
            info["os"] = platform.system()
            info["os_version"] = platform.version()
            info["os_release"] = platform.release()
            info["architecture"] = platform.machine()
            info["processor"] = platform.processor()
        
        if info_type in ["cpu", "all"]:
            info["cpu_percent"] = psutil.cpu_percent(interval=1)
            info["cpu_count_physical"] = psutil.cpu_count(logical=False)
            info["cpu_count_logical"] = psutil.cpu_count(logical=True)
            info["cpu_frequency_mhz"] = psutil.cpu_freq().current if psutil.cpu_freq() else "N/A"
        
        if info_type in ["memory", "all"]:
            mem = psutil.virtual_memory()
            info["memory_total_gb"] = round(mem.total / (1024**3), 2)
            info["memory_available_gb"] = round(mem.available / (1024**3), 2)
            info["memory_used_gb"] = round(mem.used / (1024**3), 2)
            info["memory_percent"] = mem.percent
        
        if info_type in ["disk", "all"]:
            disk = psutil.disk_usage('C:\\')
            info["disk_total_gb"] = round(disk.total / (1024**3), 2)
            info["disk_used_gb"] = round(disk.used / (1024**3), 2)
            info["disk_free_gb"] = round(disk.free / (1024**3), 2)
            info["disk_percent"] = disk.percent
            
            # Get all disk partitions
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2)
                    })
                except:
                    pass
            info["disk_partitions"] = partitions
        
        if info_type in ["network", "all"]:
            net = psutil.net_io_counters()
            info["bytes_sent_mb"] = round(net.bytes_sent / (1024**2), 2)
            info["bytes_recv_mb"] = round(net.bytes_recv / (1024**2), 2)
            
            # Get IP address
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                info["local_ip"] = s.getsockname()[0]
                s.close()
            except:
                info["local_ip"] = "Unable to determine"
        
        if info_type in ["battery", "all"]:
            # Battery info if available (for laptops)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info["battery_percent"] = battery.percent
                    info["battery_plugged"] = battery.power_plugged
                    info["battery_time_left_hours"] = round(battery.secsleft / 3600, 2) if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Charging"
                else:
                    info["battery"] = "No battery detected (Desktop PC)"
            except:
                info["battery"] = "Battery info unavailable"
        
        print(f"   [Success] System info retrieved")
        return info
    except Exception as e:
        print(f"   [Error] {e}")
        return None

def kill_process(process_name):
    """Terminates a process"""
    try:
        killed = False
        for proc in psutil.process_iter(['name']):
            if process_name.lower() in proc.info['name'].lower():
                proc.kill()
                killed = True
                print(f"   [Success] Killed: {proc.info['name']}")
        
        if not killed:
            print(f"   [Warning] Process not found: {process_name}")
        return killed
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def take_screenshot(save_path=None):
    """Takes a screenshot"""
    try:
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"screenshot_{timestamp}.png"
        
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        print(f"   [Success] Screenshot saved: {save_path}")
        return save_path
    except Exception as e:
        print(f"   [Error] {e}")
        return None

def empty_recycle_bin():
    """Empties the Recycle Bin"""
    try:
        import winshell
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        print(f"   [Success] Recycle Bin emptied")
        return True
    except ImportError:
        # Fallback method using PowerShell
        try:
            ps_command = 'powershell -command "Clear-RecycleBin -Force"'
            subprocess.run(ps_command, shell=True, capture_output=True)
            print(f"   [Success] Recycle Bin emptied")
            return True
        except Exception as e:
            print(f"   [Error] {e}")
            return False
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def organize_files(folder_path):
    """Organizes files in a folder by type into subfolders"""
    try:
        print(f"   [System] Organizing files in: {folder_path}")
        
        # Resolve smart paths
        username = os.environ.get('USERNAME', 'User')
        if not (":\\" in folder_path or folder_path.startswith("\\\\")):
            folder_lower = folder_path.lower()
            location_map = {
                "desktop": f"C:\\Users\\{username}\\Desktop",
                "documents": f"C:\\Users\\{username}\\Documents",
                "downloads": f"C:\\Users\\{username}\\Downloads",
                "pictures": f"C:\\Users\\{username}\\Pictures",
                "videos": f"C:\\Users\\{username}\\Videos",
                "music": f"C:\\Users\\{username}\\Music",
            }
            for location, real_path in location_map.items():
                if folder_lower.startswith(location):
                    remaining = folder_path[len(location):].lstrip("\\/")
                    folder_path = os.path.join(real_path, remaining) if remaining else real_path
                    break
        
        if not os.path.exists(folder_path):
            print(f"   [Error] Folder does not exist: {folder_path}")
            return False
        
        # File type categories with extensions
        file_categories = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp", ".tiff", ".raw"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".tex"],
            "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
            "Presentations": [".ppt", ".pptx", ".odp"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".php", ".rb", ".go", ".rs"],
            "Executables": [".exe", ".msi", ".bat", ".sh", ".app", ".dmg"],
            "Others": []  # Catch-all for unrecognized types
        }
        
        # Get all files in the folder (not subfolders)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        if not files:
            print(f"   [Warning] No files to organize in {folder_path}")
            return False
        
        files_moved = 0
        
        # Organize files by category
        for filename in files:
            file_path = os.path.join(folder_path, filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Find which category this file belongs to
            category_found = False
            for category, extensions in file_categories.items():
                if file_ext in extensions:
                    category_folder = os.path.join(folder_path, category)
                    
                    # Create category folder if it doesn't exist
                    os.makedirs(category_folder, exist_ok=True)
                    
                    # Move file to category folder
                    destination = os.path.join(category_folder, filename)
                    
                    # Handle duplicate filenames
                    if os.path.exists(destination):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(destination):
                            new_name = f"{base}_{counter}{ext}"
                            destination = os.path.join(category_folder, new_name)
                            counter += 1
                    
                    shutil.move(file_path, destination)
                    files_moved += 1
                    category_found = True
                    break
            
            # If no category matched, move to "Others"
            if not category_found and file_ext:  # Only if it has an extension
                others_folder = os.path.join(folder_path, "Others")
                os.makedirs(others_folder, exist_ok=True)
                
                destination = os.path.join(others_folder, filename)
                if os.path.exists(destination):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(destination):
                        new_name = f"{base}_{counter}{ext}"
                        destination = os.path.join(others_folder, new_name)
                        counter += 1
                
                shutil.move(file_path, destination)
                files_moved += 1
        
        print(f"   [Success] Organized {files_moved} files into categories")
        return True
        
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def change_wallpaper(image_path=None):
    """Changes desktop wallpaper - uses default Windows wallpapers or custom image"""
    try:
        import ctypes
        import random
        
        # If no image specified, use a random Windows default wallpaper
        if image_path is None or image_path == "null":
            # Default Windows wallpaper locations
            default_wallpaper_paths = [
                r"C:\Windows\Web\Wallpaper\Windows\img0.jpg",
                r"C:\Windows\Web\4K\Wallpaper\Windows\*.jpg",
                r"C:\Windows\Web\Wallpaper\Theme1\*.jpg",
                r"C:\Windows\Web\Wallpaper\Theme2\*.jpg"
            ]
            
            # Collect all available wallpapers
            available_wallpapers = []
            for path in default_wallpaper_paths:
                if "*" in path:
                    import glob
                    available_wallpapers.extend(glob.glob(path))
                elif os.path.exists(path):
                    available_wallpapers.append(path)
            
            if available_wallpapers:
                image_path = random.choice(available_wallpapers)
                print(f"   [System] Selected random wallpaper: {os.path.basename(image_path)}")
            else:
                print(f"   [Error] No default wallpapers found")
                return False
        else:
            # Resolve smart paths for custom images
            username = os.environ.get('USERNAME', 'User')
            if not (":\\" in image_path or image_path.startswith("\\\\")):
                path_lower = image_path.lower()
                location_map = {
                    "desktop": f"C:\\Users\\{username}\\Desktop",
                    "documents": f"C:\\Users\\{username}\\Documents",
                    "downloads": f"C:\\Users\\{username}\\Downloads",
                    "pictures": f"C:\\Users\\{username}\\Pictures",
                }
                for location, real_path in location_map.items():
                    if path_lower.startswith(location):
                        remaining = image_path[len(location):].lstrip("\\/")
                        image_path = os.path.join(real_path, remaining)
                        break
            
            # If just a filename, search for it
            if not os.path.exists(image_path):
                found_path = find_file_in_system(image_path)
                if found_path:
                    image_path = found_path
                else:
                    print(f"   [Error] Image not found: {image_path}")
                    return False
        
        # Verify the image exists and is a valid format
        if not os.path.exists(image_path):
            print(f"   [Error] Image file does not exist: {image_path}")
            return False
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
            print(f"   [Error] Invalid image format. Use JPG, PNG, or BMP")
            return False
        
        # Set the wallpaper using Windows API
        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
        
        print(f"   [Success] Wallpaper changed to: {os.path.basename(image_path)}")
        return True
        
    except Exception as e:
        print(f"   [Error] {e}")
        return False

def run_terminal_command(command):
    """Runs CMD command"""
    print(f"   [System] Executing: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

def open_google_search(query):
    """Opens Google search"""
    print(f"   [System] Searching: {query}")
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return True

def open_url(url):
    """Opens specific URL"""
    print(f"   [System] Opening: {url}")
    webbrowser.open(url)
    return True

def open_application(app_name):
    """Opens application by name or path - Enhanced with Windows Apps"""
    try:
        app_lower = app_name.lower().strip()
        
        # Common applications mapping
        app_map = {
            # Basic Windows Apps
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            
            # Browsers
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "internet explorer": "iexplore.exe",
            
            # Windows Settings & Control Panel
            "settings": "ms-settings:",
            "windows settings": "ms-settings:",
            "control panel": "control.exe",
            "control": "control.exe",
            
            # Specific Settings Pages
            "wifi settings": "ms-settings:network-wifi",
            "network settings": "ms-settings:network",
            "bluetooth settings": "ms-settings:bluetooth",
            "sound settings": "ms-settings:sound",
            "display settings": "ms-settings:display",
            "personalization": "ms-settings:personalization",
            "privacy settings": "ms-settings:privacy",
            "update settings": "ms-settings:windowsupdate",
            "storage settings": "ms-settings:storagesense",
            "apps settings": "ms-settings:appsfeatures",
            "power settings": "ms-settings:powersleep",
            "battery settings": "ms-settings:batterysaver",
            "notifications settings": "ms-settings:notifications",
            "accounts settings": "ms-settings:yourinfo",
            "time settings": "ms-settings:dateandtime",
            "region settings": "ms-settings:regionlanguage",
            "accessibility settings": "ms-settings:easeofaccess",
            
            # System Tools
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "registry editor": "regedit.exe",
            "regedit": "regedit.exe",
            "system information": "msinfo32.exe",
            "msinfo32": "msinfo32.exe",
            "device manager": "devmgmt.msc",
            "disk management": "diskmgmt.msc",
            "services": "services.msc",
            "event viewer": "eventvwr.msc",
            "performance monitor": "perfmon.exe",
            "resource monitor": "resmon.exe",
            
            # Office & Productivity
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "onenote": "onenote.exe",
            "teams": "teams.exe",
            "microsoft teams": "teams.exe",
            
            # Media
            "media player": "wmplayer.exe",
            "windows media player": "wmplayer.exe",
            "movies": "ms-video:",
            "photos": "ms-photos:",
            "camera": "microsoft.windows.camera:",
            "voice recorder": "ms-voicerecorder:",
            
            # Accessories
            "snipping tool": "SnippingTool.exe",
            "snip": "SnippingTool.exe",
            "screenshot": "SnippingTool.exe",
            "sticky notes": "ms-stickynotes:",
            "notes": "ms-stickynotes:",
            "magnifier": "magnify.exe",
            "narrator": "narrator.exe",
            "on-screen keyboard": "osk.exe",
            "character map": "charmap.exe",
            
            # Store & Xbox
            "store": "ms-windows-store:",
            "microsoft store": "ms-windows-store:",
            "xbox": "xbox:",
            "xbox game bar": "xbox:",
            
            # Communication
            "mail": "outlookmail:",
            "calendar": "outlookcal:",
            "skype": "skype.exe",
            
            # Development
            "visual studio code": "code.exe",
            "vscode": "code.exe",
            "vs code": "code.exe",
            "visual studio": "devenv.exe",
            "git bash": "git-bash.exe",
            
            # Other
            "clock": "ms-clock:",
            "alarms": "ms-clock:",
            "weather": "bingweather:",
            "maps": "bingmaps:",
            "news": "bingnews:",
            "cortana": "ms-cortana:",
        }
        
        # Check if it's a known application
        if app_lower in app_map:
            command = app_map[app_lower]
            
            # Handle ms-settings and other URI schemes
            if command.startswith("ms-") or ":" in command and not command.endswith(".exe"):
                subprocess.Popen(f'start {command}', shell=True)
            else:
                subprocess.Popen(command, shell=True)
            
            print(f"   [Success] Opened {app_name}")
            return True
        
        # Try to search for the app in Start Menu
        else:
            # Method 1: Use Windows Run command
            print(f"   [System] Searching for {app_name} in Start Menu...")
            
            # Try opening via start command
            result = subprocess.run(f'start "" "{app_name}"', shell=True, capture_output=True)
            if result.returncode == 0:
                print(f"   [Success] Opened {app_name}")
                return True
            
            # Method 2: Search in Program Files
            program_paths = [
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                f"C:\\Users\\{os.environ.get('USERNAME', 'User')}\\AppData\\Local\\Programs"
            ]
            
            for base_path in program_paths:
                if os.path.exists(base_path):
                    for root, dirs, files in os.walk(base_path):
                        for file in files:
                            if app_name.lower() in file.lower() and file.endswith('.exe'):
                                full_path = os.path.join(root, file)
                                subprocess.Popen(full_path)
                                print(f"   [Success] Opened {app_name} at {full_path}")
                                return True
            
            print(f"   [Error] Could not find application: {app_name}")
            return False
            
    except Exception as e:
        print(f"   [Error] Could not open {app_name}: {e}")
        return False

def open_folder(folder_name):
    """Opens common system folders or any folder path"""
    try:
        # Get username for dynamic paths
        username = os.environ.get('USERNAME', 'User')
        
        # Common folder mappings
        folder_map = {
            "downloads": f"C:\\Users\\{username}\\Downloads",
            "documents": f"C:\\Users\\{username}\\Documents",
            "desktop": f"C:\\Users\\{username}\\Desktop",
            "pictures": f"C:\\Users\\{username}\\Pictures",
            "videos": f"C:\\Users\\{username}\\Videos",
            "music": f"C:\\Users\\{username}\\Music",
            "onedrive": f"C:\\Users\\{username}\\OneDrive",
            "appdata": f"C:\\Users\\{username}\\AppData",
            "temp": os.environ.get('TEMP', f"C:\\Users\\{username}\\AppData\\Local\\Temp"),
            "program files": "C:\\Program Files",
            "program files (x86)": "C:\\Program Files (x86)",
            "windows": "C:\\Windows",
            "system32": "C:\\Windows\\System32",
            "users": "C:\\Users",
            "c:": "C:\\",
            "d:": "D:\\",
            "this pc": "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}",
            "recycle bin": "::{645FF040-5081-101B-9F08-00AA002F954E}",
            "network": "::{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}"
        }
        
        # Normalize the folder name
        folder_lower = folder_name.lower().strip()
        
        # Check if it's a known folder
        if folder_lower in folder_map:
            path = folder_map[folder_lower]
            subprocess.Popen(f'explorer "{path}"')
            print(f"   [Success] Opened {folder_name} at {path}")
            return True
        
        # Check if it's a direct path
        elif os.path.exists(folder_name):
            subprocess.Popen(f'explorer "{folder_name}"')
            print(f"   [Success] Opened {folder_name}")
            return True
        
        # Try to find the folder
        else:
            found_path = find_file_in_system(folder_name)
            if found_path and os.path.isdir(found_path):
                subprocess.Popen(f'explorer "{found_path}"')
                print(f"   [Success] Opened {folder_name} at {found_path}")
                return True
            else:
                print(f"   [Error] Folder not found: {folder_name}")
                return False
                
    except Exception as e:
        print(f"   [Error] Could not open folder {folder_name}: {e}")
        return False