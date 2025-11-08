import argparse
import json
import os
import re
import sys
from io import BytesIO

import google.generativeai as genai
from PIL import Image, ImageGrab


def take_screenshot():
    """Capture a screenshot of the entire screen."""
    screenshot = ImageGrab.grab()
    return screenshot


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
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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


def main():
    parser = argparse.ArgumentParser(
        description="Take a screenshot and query Gemini to find a section on the screen"
    )
    parser.add_argument(
        "query",
        help="Description of the section to find on the screen (e.g., 'the login button', 'the search bar')"
    )
    parser.add_argument(
        "--api-key",
        help="Google Gemini API key (or set GEMINI_API_KEY environment variable)",
        default=None
    )
    parser.add_argument(
        "--save-screenshot",
        help="Save the screenshot to a file",
        default=None
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: API key required. Set GEMINI_API_KEY environment variable or use --api-key", file=sys.stderr)
        sys.exit(1)
    
    # Take screenshot
    print("Taking screenshot...")
    screenshot = take_screenshot()
    print(f"Screenshot captured: {screenshot.width}x{screenshot.height} pixels")
    
    # Save screenshot if requested
    if args.save_screenshot:
        screenshot.save(args.save_screenshot)
        print(f"Screenshot saved to: {args.save_screenshot}")
    
    # Query Gemini
    print(f"Querying Gemini to find: '{args.query}'...")
    result = query_gemini_for_section(screenshot, args.query, api_key)
    
    # Display results
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nBounding box found:")
        print(f"  X: {result.get('x', 'N/A')}")
        print(f"  Y: {result.get('y', 'N/A')}")
        print(f"  Width: {result.get('width', 'N/A')}")
        print(f"  Height: {result.get('height', 'N/A')}")
        print("\nJSON output:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
