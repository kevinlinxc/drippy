#!/usr/bin/env python3
"""
Main script that orchestrates the todo list workflow.
Loads todo list, queries Gemini for next steps, and shows overlay with instructions.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.drippy.gemini_query import take_screenshot, query_gemini_for_next_action, draw_bounding_box
from src.drippy.overlay import show_overlay

load_dotenv()


def convert_coordinates_for_macos(x, y, width, height, screenshot_image, screen_geometry):
    """
    Convert coordinates from screenshot image space to macOS screen coordinate space.
    
    On macOS with Retina displays, screenshots may be captured at 2x resolution,
    but window coordinates use logical points (1x). This function converts between them.
    
    Args:
        x, y, width, height: Coordinates in screenshot image space
        screenshot_image: PIL Image of the screenshot
        screen_geometry: QRect of the screen geometry from PyQt
        
    Returns:
        Tuple of (x, y, width, height) in screen coordinate space
    """
    # Get screenshot dimensions
    screenshot_width = screenshot_image.width
    screenshot_height = screenshot_image.height
    
    # Get screen logical dimensions from PyQt
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()
    
    # Calculate scaling factors
    scale_x = screen_width / screenshot_width
    scale_y = screen_height / screenshot_height
    
    # Convert coordinates
    converted_x = int(x * scale_x)
    converted_y = int(y * scale_y)
    converted_width = int(width * scale_x)
    converted_height = int(height * scale_y)
    
    return converted_x, converted_y, converted_width, converted_height


def adjust_for_dock(x, y, width, height, screen_geometry):
    """
    Adjust bounding box coordinates if they would be obscured by the macOS dock.
    
    Args:
        x, y, width, height: Bounding box coordinates in screen space
        screen_geometry: QRect of the screen geometry from PyQt
        
    Returns:
        Tuple of (adjusted_x, adjusted_y, width, height) with y adjusted if needed
    """
    screen_height = screen_geometry.height()
    bbox_bottom = y + height
    
    # Dock is typically at the bottom, about 50-80 pixels tall
    # Use a conservative estimate of 100 pixels from bottom
    dock_area_start = screen_height - 100
    
    # Check if bounding box would be in dock area
    if bbox_bottom > dock_area_start:
        # Calculate how much to move up
        # Move up enough to clear the dock, plus some padding
        overlap = bbox_bottom - dock_area_start
        padding = 20  # Extra padding above dock
        move_up = overlap + padding
        
        # Adjust y coordinate
        adjusted_y = y - move_up
        
        # Make sure we don't go off the top of the screen
        if adjusted_y < 0:
            adjusted_y = 0
        
        print(f"  Bounding box would be obscured by dock, moving up by {move_up} pixels")
        return x, adjusted_y, width, height
    
    return x, y, width, height


def load_todo_list(todo_file_path: str) -> str:
    """Load the todo list from a file."""
    try:
        with open(todo_file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Could not find todo list file at {todo_file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading todo list file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main workflow loop."""
    # Get project root directory
    project_root = Path(__file__).parent
    todo_list_path = project_root / "ideal-todo-list.txt"
    
    # Create debug folder with current date/time
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    debug_folder = project_root / "debug" / timestamp
    debug_folder.mkdir(parents=True, exist_ok=True)
    print(f"Debug folder created: {debug_folder}")
    
    # Load todo list
    print("Loading todo list...")
    todo_list = load_todo_list(str(todo_list_path))
    print(f"Todo list loaded:\n{todo_list}\n")
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    
    # Initialize QApplication early so we can get screen geometry for coordinate conversion
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Initialize step counter
    step = 0
    
    # Main loop
    while True:
        step += 1
        print(f"\n=== Step {step} ===")
        
        # Take screenshot
        print("Taking screenshot...")
        screenshot = take_screenshot()
        print(f"Screenshot captured: {screenshot.width}x{screenshot.height} pixels")
        
        # Query Gemini for next action
        print("Querying Gemini for next action...")
        
        # Modify todo list prompt to include step information
        todo_prompt = f"""TODO LIST:
{todo_list}

We are currently on step {step}. Please determine what action needs to be taken next based on the current state of the screen and the todo list."""
        
        result = query_gemini_for_next_action(screenshot, todo_prompt, api_key)
        
        # Check for errors
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            print("Exiting...")
            break
        
        # Validate required fields
        required_fields = ["x", "y", "width", "height", "instructions"]
        for field in required_fields:
            if field not in result:
                print(f"Error: Invalid response from Gemini: missing field '{field}'", file=sys.stderr)
                print("Exiting...")
                break
        
        # Extract values (these are in screenshot image coordinate space)
        x = int(result.get("x", 0))
        y = int(result.get("y", 0))
        width = int(result.get("width", 0))
        height = int(result.get("height", 0))
        instructions = str(result.get("instructions", ""))
        
        print(f"Next action found:")
        print(f"  Bounding box (screenshot space): ({x}, {y}) {width}x{height}")
        print(f"  Screenshot size: {screenshot.width}x{screenshot.height}")
        print(f"  Instructions: {instructions}")
        
        # Draw bounding box on screenshot and save to debug folder (use original coordinates)
        bbox_dict = {"x": x, "y": y, "width": width, "height": height}
        annotated_image = draw_bounding_box(screenshot, bbox_dict)
        
        # Save annotated screenshot
        screenshot_filename = debug_folder / f"step_{step:03d}_bbox.png"
        annotated_image.save(screenshot_filename)
        print(f"  Saved annotated screenshot to: {screenshot_filename}")
        
        # Convert coordinates for macOS screen coordinate system
        screen_geometry = app.primaryScreen().geometry()
        
        converted_x, converted_y, converted_width, converted_height = convert_coordinates_for_macos(
            x, y, width, height, screenshot, screen_geometry
        )
        
        print(f"  Bounding box (screen space): ({converted_x}, {converted_y}) {converted_width}x{converted_height}")
        print(f"  Screen size: {screen_geometry.width()}x{screen_geometry.height()}")
        
        # Adjust for dock if needed (macOS only)
        if sys.platform == 'darwin':
            final_x, final_y, final_width, final_height = adjust_for_dock(
                converted_x, converted_y, converted_width, converted_height, screen_geometry
            )
            if final_y != converted_y:
                print(f"  Adjusted bounding box: ({final_x}, {final_y}) {final_width}x{final_height}")
        else:
            final_x, final_y, final_width, final_height = converted_x, converted_y, converted_width, converted_height
        
        # Show overlay with adjusted coordinates
        print("\nShowing overlay...")
        button_result = show_overlay(final_x, final_y, final_width, final_height, instructions)
        
        # Handle button result
        if button_result == 'cancel':
            print("\nExit button clicked. Exiting workflow.")
            break
        elif button_result == 'done':
            print("\nContinue button clicked. Moving to next step...")
            # Continue loop to next iteration
            continue
        else:
            print("\nOverlay closed. Exiting workflow.")
            break
    
    print("\nWorkflow completed.")


if __name__ == '__main__':
    main()

