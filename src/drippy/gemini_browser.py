"""
Gemini integration for browser automation - determines next actions in browser context.
"""

import json
import re
from io import BytesIO
from typing import Dict, Any, Optional

import google.generativeai as genai
from PIL import Image


def query_gemini_for_browser_action(page_html: str, page_screenshot: bytes, 
                                    todo_list: str, current_step: int,
                                    api_key: str) -> Dict[str, Any]:
    """
    Query Gemini to determine the next browser action based on HTML and screenshot.
    
    Args:
        page_html: HTML content of the current page
        page_screenshot: Screenshot of the current page as bytes
        todo_list: The todo list
        current_step: Current step number
        api_key: Google Gemini API key
        
    Returns:
        Dictionary with action type, selector, instructions, and other details
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    # Convert screenshot to PIL Image for dimensions
    screenshot_img = Image.open(BytesIO(page_screenshot))
    
    # Create prompt
    prompt = f"""Analyze this webpage and determine the next action to take.

TODO LIST:
{todo_list}

We are currently on step {current_step}.

Current page HTML (truncated to first 5000 chars):
{page_html[:5000]}

Based on the current state of the page and the todo list, identify:
1. What is the next action that needs to be performed?
2. What element on the page should be interacted with? (provide a CSS selector)
3. What type of action is needed? (click, type, wait, navigate)

The screenshot dimensions are {screenshot_img.width}x{screenshot_img.height}.

Return the response in the following JSON format:
{{
    "action_type": "<click|type|navigate|wait>",
    "selector": "<CSS selector for the element, or null if navigating>",
    "instructions": "<detailed instructions on what action to take>",
    "value": "<text to type if action_type is 'type', or URL if 'navigate', or null>",
    "expected_result": "<what should happen after this action - URL change, element appearance, etc>"
}}

If no action can be determined, return: {{"error": "Cannot determine next action"}}"""

    try:
        # Send HTML, screenshot, and prompt to Gemini
        response = model.generate_content([
            prompt,
            {
                "mime_type": "image/png",
                "data": page_screenshot
            }
        ])
        
        # Parse response
        response_text = response.text.strip()
        
        # Try to extract JSON from response
        start_idx = response_text.find('{')
        if start_idx != -1:
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count == 0:
                json_str = response_text[start_idx:end_idx]
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    pass
        
        # Fallback: try simple regex match
        json_match = re.search(r'\{[^}]*"action_type"[^}]*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result
            except json.JSONDecodeError:
                pass
        
        return {"error": f"Could not parse response: {response_text}"}
            
    except Exception as e:
        return {"error": f"Error querying Gemini: {str(e)}"}

