import cv2
import numpy as np
import pyautogui
import os

def find_icon(icon_name):
    """
    Scans the screen for an icon image (e.g., 'recycle_bin.png').
    Returns: (x, y) coordinates of the center, or None if not found.
    """
    
    # 1. Take a screenshot of the screen
    screenshot = pyautogui.screenshot()
    
    # Convert screenshot to a format OpenCV understands (RGB -> BGR)
    screen_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    # 2. Load the template image (the icon we are looking for)
    asset_path = os.path.join("assets", icon_name)
    if not os.path.exists(asset_path):
        print(f"Error: Could not find asset {asset_path}")
        return None
        
    template = cv2.imread(asset_path)
    
    # Get dimensions of the icon
    h, w = template.shape[:2]
    
    # 3. Perform Template Matching (The "Scanning" part)
    # TM_CCOEFF_NORMED gives a score between 0 (no match) and 1 (perfect match)
    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    
    # Find the best match
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    # 4. Threshold Check (Is it actually there?)
    # 0.8 is a good baseline. If it's lower, it's probably a false positive.
    if max_val >= 0.8:
        top_left = max_loc
        center_x = top_left[0] + w // 2
        center_y = top_left[1] + h // 2
        return (center_x, center_y)
    else:
        return None

# --- TEST IT ---
if __name__ == "__main__":
    print("Looking for Recycle Bin...")
    coords = find_icon("recycle_bin.png")
    
    if coords:
        print(f"FOUND IT at: {coords}")
        # Move mouse there to prove it works
        pyautogui.moveTo(coords[0], coords[1], duration=0.5)
    else:
        print("Could not find the icon. Check your 'assets' folder.")