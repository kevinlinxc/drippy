import json
import os
import re
import subprocess
import sys
import tempfile
from io import BytesIO

import cv2
import mss
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

load_dotenv()


def take_screenshot():
    """Capture a screenshot of the entire screen using mss."""
    with mss.mss() as sct:
        # Get the primary monitor
        monitor = sct.monitors[1]  # monitors[0] is all monitors, monitors[1] is primary
        # Capture the screen
        screenshot = sct.grab(monitor)
        # Convert to numpy array (BGRA format)
        img_array = np.array(screenshot)
        # Convert BGRA to RGB
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)
        # Convert to PIL Image
        return Image.fromarray(img_rgb)


def draw_bounding_box(image: Image.Image, bbox: dict) -> Image.Image:
    """
    Draw a bounding box on the image using OpenCV.
    
    Args:
        image: PIL Image object
        bbox: Dictionary with 'x', 'y', 'width', 'height' keys
        
    Returns:
        PIL Image with bounding box drawn
    """
    # Convert PIL Image to OpenCV format (numpy array)
    img_array = np.array(image)
    # Convert RGB to BGR for OpenCV
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Extract bounding box coordinates
    x = int(bbox.get('x', 0))
    y = int(bbox.get('y', 0))
    width = int(bbox.get('width', 0))
    height = int(bbox.get('height', 0))
    
    # Draw rectangle (green color, thickness 3)
    cv2.rectangle(img_cv, (x, y), (x + width, y + height), (0, 255, 0), 3)
    
    # Convert back to RGB
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    # Convert back to PIL Image
    return Image.fromarray(img_rgb)


def query_gemini_for_section(image: Image.Image, query: str, api_key: str) -> dict:
    """
    Query Gemini to find a section on the screen and return bounding box.
    
    Args:
        image: PIL Image object of the screenshot
        query: Description of what to find on the screen
        api_key: Google Gemini API key
        
    Returns:
        Dictionary with bounding box coordinates or error message
    """
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    # Convert image to bytes
    img_bytes = BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Create prompt
    prompt = f"""Analyze this screenshot and find the section described as: "{query}"

Please identify the bounding box coordinates of this section. The image dimensions are {image.width}x{image.height}.

Return the bounding box in the following JSON format:
{{
    "x": <left coordinate>,
    "y": <top coordinate>,
    "width": <width>,
    "height": <height>
}}

Coordinates should be in pixels, with (0,0) at the top-left corner.
If the section cannot be found, return: {{"error": "Section not found"}}"""

    try:
        # Send image and prompt to Gemini
        response = model.generate_content([
            prompt,
            {
                "mime_type": "image/png",
                "data": img_bytes.read()
            }
        ])
        
        # Parse response
        response_text = response.text.strip()
        
        # Try to extract JSON from response
        # Look for JSON in the response
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {"error": f"Could not parse response: {response_text}"}
            
    except Exception as e:
        return {"error": f"Error querying Gemini: {str(e)}"}


def main(query: str, api_key: str = None, save_screenshot: str = None):
    """
    Take a screenshot and query Gemini to find a section on the screen.
    
    Args:
        query: Description of the section to find on the screen (e.g., 'the login button', 'the search bar')
        api_key: Google Gemini API key (or set GEMINI_API_KEY environment variable)
        save_screenshot: Optional path to save the screenshot to
    """
    # Get API key
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: API key required. Set GEMINI_API_KEY environment variable or pass api_key parameter", file=sys.stderr)
        sys.exit(1)
    
    # Take screenshot
    print("Taking screenshot...")
    screenshot = take_screenshot()
    print(f"Screenshot captured: {screenshot.width}x{screenshot.height} pixels")
    
    # Query Gemini
    print(f"Querying Gemini to find: '{query}'...")
    result = query_gemini_for_section(screenshot, query, api_key)
    
    # Display results
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    # Draw bounding box on the image
    print("\nBounding box found:")
    print(f"  X: {result.get('x', 'N/A')}")
    print(f"  Y: {result.get('y', 'N/A')}")
    print(f"  Width: {result.get('width', 'N/A')}")
    print(f"  Height: {result.get('height', 'N/A')}")
    print("\nDrawing bounding box...")
    
    annotated_image = draw_bounding_box(screenshot, result)
    
    # Save annotated image
    if save_screenshot:
        annotated_path = save_screenshot
    else:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            annotated_path = tmp_file.name
    
    annotated_image.save(annotated_path)
    print(f"Annotated image saved to: {annotated_path}")
    
    # Open annotated image in Preview
    print("Opening annotated image in Preview...")
    subprocess.run(['open', '-a', 'Preview', annotated_path])
    
    print("\nJSON output:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Example usage - modify these parameters as needed
    query = "the firefox app"  # Change this to your desired query
    api_key = None  # Will use GEMINI_API_KEY environment variable if None
    save_screenshot = None  # Set to a path if you want to save the screenshot
    
    main(query, api_key, save_screenshot)

