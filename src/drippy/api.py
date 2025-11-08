import os
import subprocess
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PyQt5.QtWidgets import QApplication

from .gemini_query import take_screenshot, query_gemini_for_section, query_gemini_for_next_action
from .overlay import show_overlay

app = FastAPI(
    title="Drippy API",
    description="Screen search API using Gemini AI to find elements on screen and return bounding boxes",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
TODO_LIST_PATH = PROJECT_ROOT / "ideal-todo-list.txt"


class SearchRequest(BaseModel):
    query: str = Field(..., description="Description of what to find on the screen (e.g., 'the login button', 'the firefox app')")


class BoundingBoxResponse(BaseModel):
    x: int = Field(..., description="Left coordinate of the bounding box in pixels")
    y: int = Field(..., description="Top coordinate of the bounding box in pixels")
    width: int = Field(..., description="Width of the bounding box in pixels")
    height: int = Field(..., description="Height of the bounding box in pixels")


class TodoListRequest(BaseModel):
    todo_list: str = Field(..., description="A long string containing the todo list of tasks to complete")


class NextActionResponse(BaseModel):
    x: int = Field(..., description="Left coordinate of the area to interact with in pixels")
    y: int = Field(..., description="Top coordinate of the area to interact with in pixels")
    width: int = Field(..., description="Width of the area to interact with in pixels")
    height: int = Field(..., description="Height of the area to interact with in pixels")
    instructions: str = Field(..., description="Detailed instructions on what action to take next")


class TaskRequest(BaseModel):
    task: str = Field(..., description="Description of the task to complete (e.g., 'How to download a youtube video and convert it to mp3')")


class OverlayRequest(BaseModel):
    x: int = Field(..., description="X coordinate of the bounding box")
    y: int = Field(..., description="Y coordinate of the bounding box")
    width: int = Field(..., description="Width of the bounding box")
    height: int = Field(..., description="Height of the bounding box")
    text: str = Field(..., description="Instructions text to display")


@app.post(
    "/search_on_screen",
    response_model=BoundingBoxResponse,
    summary="Search for element on screen",
    description="Takes a screenshot, uses Gemini AI to find the specified element, and returns its bounding box coordinates",
    tags=["Screen Search"],
    responses={
        200: {
            "description": "Successfully found the element",
            "content": {
                "application/json": {
                    "example": {
                        "x": 100,
                        "y": 200,
                        "width": 150,
                        "height": 50
                    }
                }
            }
        },
        404: {
            "description": "Element not found on screen",
            "content": {
                "application/json": {
                    "example": {"detail": "Section not found"}
                }
            }
        },
        500: {
            "description": "Server error (API key missing or invalid response)",
            "content": {
                "application/json": {
                    "example": {"detail": "GEMINI_API_KEY environment variable is not set"}
                }
            }
        }
    }
)
async def search_on_screen(request: SearchRequest):
    """
    Search for an element on the screen and return its bounding box.
    
    This endpoint:
    1. Takes a screenshot of the primary monitor
    2. Sends it to Gemini AI with your query
    3. Returns the bounding box coordinates (x, y, width, height) of the found element
    
    **Example request:**
    ```json
    {
        "query": "the firefox app"
    }
    ```
    
    **Example response:**
    ```json
    {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 50
    }
    ```
    """
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set"
        )
    
    # Take screenshot
    screenshot = take_screenshot()
    
    # Query Gemini for the section
    result = query_gemini_for_section(screenshot, request.query, api_key)
    
    # Check for errors
    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )
    
    # Validate that we have all required fields
    required_fields = ["x", "y", "width", "height"]
    for field in required_fields:
        if field not in result:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Gemini: missing field '{field}'"
            )
    
    # Return bounding box
    return BoundingBoxResponse(
        x=int(result["x"]),
        y=int(result["y"]),
        width=int(result["width"]),
        height=int(result["height"])
    )


@app.post(
    "/next_action",
    response_model=NextActionResponse,
    summary="Get next action from todo list",
    description="Takes a screenshot, analyzes it with a todo list, and returns the next action to take with bounding box and instructions",
    tags=["Screen Search"],
    responses={
        200: {
            "description": "Successfully determined next action",
            "content": {
                "application/json": {
                    "example": {
                        "x": 100,
                        "y": 200,
                        "width": 150,
                        "height": 50,
                        "instructions": "Click the login button to proceed"
                    }
                }
            }
        },
        404: {
            "description": "Cannot determine next action",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot determine next action"}
                }
            }
        },
        500: {
            "description": "Server error (API key missing or invalid response)",
            "content": {
                "application/json": {
                    "example": {"detail": "GEMINI_API_KEY environment variable is not set"}
                }
            }
        }
    }
)
async def next_action(request: TodoListRequest):
    """
    Determine the next action to take based on a todo list and current screen state.
    
    This endpoint:
    1. Takes a screenshot of the primary monitor
    2. Analyzes the screenshot along with the provided todo list
    3. Determines what action should be taken next
    4. Returns the bounding box of the area to interact with and detailed instructions
    
    **Example request:**
    ```json
    {
        "todo_list": "1. Log into the application\\n2. Navigate to settings\\n3. Update profile information"
    }
    ```
    
    **Example response:**
    ```json
    {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 50,
        "instructions": "Click the login button to proceed with authentication"
    }
    ```
    """
    print(f"[API] /next_action called with todo_list: {request.todo_list[:100]}...")
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[API] ERROR: GEMINI_API_KEY not set")
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set"
        )
    
    print("[API] Taking screenshot...")
    # Take screenshot
    screenshot = take_screenshot()
    print(f"[API] Screenshot captured: {screenshot.width}x{screenshot.height}")
    
    print("[API] Querying Gemini for next action...")
    # Query Gemini for the next action
    result = query_gemini_for_next_action(screenshot, request.todo_list, api_key)
    print(f"[API] Gemini response: {result}")
    
    # Check for errors
    if "error" in result:
        print(f"[API] ERROR from Gemini: {result['error']}")
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )
    
    # Validate that we have all required fields
    required_fields = ["x", "y", "width", "height", "instructions"]
    for field in required_fields:
        if field not in result:
            print(f"[API] ERROR: Missing field '{field}' in response")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Gemini: missing field '{field}'"
            )
    
    # Extract coordinates (these are in screenshot image coordinate space)
    x = int(result["x"])
    y = int(result["y"])
    width = int(result["width"])
    height = int(result["height"])
    instructions = str(result["instructions"])
    print(f"[API] Extracted: x={x}, y={y}, width={width}, height={height}, instructions={instructions[:50]}...")
    
    # Convert coordinates for macOS screen coordinate system if needed
    if sys.platform == 'darwin':
        print("[API] Converting coordinates for macOS...")
        # Initialize QApplication if needed for screen geometry
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        screen_geometry = app.primaryScreen().geometry()
        
        # Get screenshot dimensions
        screenshot_width = screenshot.width
        screenshot_height = screenshot.height
        
        # Get screen logical dimensions from PyQt
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        print(f"[API] Screenshot: {screenshot_width}x{screenshot_height}, Screen: {screen_width}x{screen_height}")
        
        # Calculate scaling factors
        scale_x = screen_width / screenshot_width
        scale_y = screen_height / screenshot_height
        
        # Convert coordinates
        x = int(x * scale_x)
        y = int(y * scale_y)
        width = int(width * scale_x)
        height = int(height * scale_y)
        
        print(f"[API] Converted: x={x}, y={y}, width={width}, height={height}")
        
        # Adjust for dock if needed (move up if in dock area)
        bbox_bottom = y + height
        dock_area_start = screen_height - 100
        if bbox_bottom > dock_area_start:
            overlap = bbox_bottom - dock_area_start
            padding = 20
            move_up = overlap + padding
            y = max(0, y - move_up)
            print(f"[API] Adjusted for dock: moved up by {move_up}, new y={y}")
    
    print("[API] Showing overlay...")
    # Show overlay with converted coordinates
    show_overlay(x, y, width, height)
    print("[API] Overlay shown")
    
    # Return next action with bounding box and instructions
    response = NextActionResponse(
        x=x,
        y=y,
        width=width,
        height=height,
        instructions=instructions
    )
    print(f"[API] Returning response: {response}")
    return response


@app.get(
    "/todo-list",
    summary="Get todo list",
    description="Returns the todo list from ideal-todo-list.txt",
    tags=["Todo List"],
    responses={
        200: {
            "description": "Successfully loaded todo list",
            "content": {
                "application/json": {
                    "example": {
                        "todo_list": [
                            "1. Open the browser app (firefox)",
                            "2. Open the url youtube.com"
                        ]
                    }
                }
            }
        }
    }
)
async def get_todo_list():
    """Load and return the todo list from ideal-todo-list.txt."""
    print(f"[API] /todo-list called")
    try:
        print(f"[API] Looking for todo list at: {TODO_LIST_PATH}")
        if not TODO_LIST_PATH.exists():
            print(f"[API] ERROR: Todo list file not found")
            raise HTTPException(
                status_code=404,
                detail=f"Todo list file not found: {TODO_LIST_PATH}"
            )
        
        with open(TODO_LIST_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"[API] Read {len(lines)} lines from todo list file")
        
        # Parse todo list - extract just the task text (remove numbers)
        todo_items = []
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                print(f"[API] Skipping empty line {idx + 1}")
                continue
            
            print(f"[API] Processing line {idx + 1}: '{line}'")
            
            # Remove leading numbers and dots (e.g., "1. " or "12. " or "2.2. ")
            # Match pattern like "1. " or "12. " or "2.2. " (handle double numbering)
            # Use a pattern that matches one or more "number." sequences at the start
            cleaned = re.sub(r'^(\d+\.\s*)+', '', line)
            
            print(f"[API]   After cleaning: '{cleaned}'")
            if cleaned and cleaned.strip():
                todo_items.append(cleaned.strip())
                print(f"[API]   Added todo item: '{cleaned.strip()}'")
            else:
                print(f"[API]   Skipping line (empty after cleaning)")
        
        print(f"[API] Parsed {len(todo_items)} todo items: {todo_items}")
        if len(todo_items) == 0:
            print(f"[API] WARNING: No todo items parsed! Original lines: {lines}")
        return JSONResponse(content={"todo_list": todo_items})
    except Exception as e:
        print(f"[API] ERROR loading todo list: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading todo list: {str(e)}"
        )


@app.post(
    "/process_task",
    response_model=NextActionResponse,
    summary="Process a task description and get first step",
    description="Takes a task description, converts it to a todo list, takes a screenshot, and returns the first action to take with bounding box and instructions",
    tags=["Task Processing"],
    responses={
        200: {
            "description": "Successfully determined first action",
            "content": {
                "application/json": {
                    "example": {
                        "x": 100,
                        "y": 200,
                        "width": 150,
                        "height": 50,
                        "instructions": "Click the YouTube video URL to open it"
                    }
                }
            }
        },
        404: {
            "description": "Cannot determine next action",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot determine next action"}
                }
            }
        },
        500: {
            "description": "Server error (API key missing or invalid response)",
            "content": {
                "application/json": {
                    "example": {"detail": "GEMINI_API_KEY environment variable is not set"}
                }
            }
        }
    }
)
async def process_task(request: TaskRequest):
    """
    Process a task description and determine the first action to take.
    
    This endpoint:
    1. Takes a task description (e.g., "How to download a youtube video and convert it to mp3")
    2. Converts it to a structured todo list using Gemini
    3. Takes a screenshot of the current screen
    4. Determines the first action to take based on the todo list
    5. Returns the bounding box and instructions for the first step
    
    **Example request:**
    ```json
    {
        "task": "How to download a youtube video and convert it to mp3"
    }
    ```
    
    **Example response:**
    ```json
    {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 50,
        "instructions": "Open Firefox browser to access YouTube"
    }
    ```
    """
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set"
        )
    
    # Import here to avoid circular imports
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    # Convert task to todo list using Gemini
    todo_prompt = f"""Convert the following task into a step-by-step todo list. 
    Be specific and actionable. Format as a numbered list.

    Task: {request.task}

    Return only the todo list, one step per line, numbered. For example:
    1. Open Firefox browser
    2. Navigate to YouTube
    3. Search for the video
    4. Copy the video URL
    5. Open a YouTube downloader website
    6. Paste the URL and download the video
    7. Convert the downloaded video to MP3 format
    """
    
    try:
        todo_response = model.generate_content(todo_prompt)
        todo_list = todo_response.text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating todo list: {str(e)}"
        )
    
    # Take screenshot
    screenshot = take_screenshot()
    
    # Query Gemini for the next action
    result = query_gemini_for_next_action(screenshot, todo_list, api_key)
    
    # Check for errors
    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )
    
    # Validate that we have all required fields
    required_fields = ["x", "y", "width", "height", "instructions"]
    for field in required_fields:
        if field not in result:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Gemini: missing field '{field}'"
            )
    
    # Return next action with bounding box and instructions
    return NextActionResponse(
        x=int(result["x"]),
        y=int(result["y"]),
        width=int(result["width"]),
        height=int(result["height"]),
        instructions=str(result["instructions"])
    )


@app.post(
    "/process_task",
    response_model=NextActionResponse,
    summary="Process a task description and get first step",
    description="Takes a task description, converts it to a todo list, takes a screenshot, and returns the first action to take with bounding box and instructions",
    tags=["Task Processing"],
    responses={
        200: {
            "description": "Successfully determined first action",
            "content": {
                "application/json": {
                    "example": {
                        "x": 100,
                        "y": 200,
                        "width": 150,
                        "height": 50,
                        "instructions": "Click the YouTube video URL to open it"
                    }
                }
            }
        },
        404: {
            "description": "Cannot determine next action",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot determine next action"}
                }
            }
        },
        500: {
            "description": "Server error (API key missing or invalid response)",
            "content": {
                "application/json": {
                    "example": {"detail": "GEMINI_API_KEY environment variable is not set"}
                }
            }
        }
    }
)
async def process_task(request: TaskRequest):
    """
    Process a task description and determine the first action to take.
    
    This endpoint:
    1. Takes a task description (e.g., "How to download a youtube video and convert it to mp3")
    2. Converts it to a structured todo list using Gemini
    3. Takes a screenshot of the current screen
    4. Determines the first action to take based on the todo list
    5. Returns the bounding box and instructions for the first step
    
    **Example request:**
    ```json
    {
        "task": "How to download a youtube video and convert it to mp3"
    }
    ```
    
    **Example response:**
    ```json
    {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 50,
        "instructions": "Open Firefox browser to access YouTube"
    }
    ```
    """
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set"
        )
    
    # Import here to avoid circular imports
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    # Convert task to todo list using Gemini
    todo_prompt = f"""Convert the following task into a step-by-step todo list. 
    Be specific and actionable. Format as a numbered list.

    Task: {request.task}

    Return only the todo list, one step per line, numbered. For example:
    1. Open Firefox browser
    2. Navigate to YouTube
    3. Search for the video
    4. Copy the video URL
    5. Open a YouTube downloader website
    6. Paste the URL and download the video
    7. Convert the downloaded video to MP3 format
    """
    
    try:
        todo_response = model.generate_content(todo_prompt)
        todo_list = todo_response.text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating todo list: {str(e)}"
        )
    
    # Take screenshot
    screenshot = take_screenshot()
    
    # Query Gemini for the next action
    result = query_gemini_for_next_action(screenshot, todo_list, api_key)
    
    # Check for errors
    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )
    
    # Validate that we have all required fields
    required_fields = ["x", "y", "width", "height", "instructions"]
    for field in required_fields:
        if field not in result:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Gemini: missing field '{field}'"
            )
    
    # Return next action with bounding box and instructions
    return NextActionResponse(
        x=int(result["x"]),
        y=int(result["y"]),
        width=int(result["width"]),
        height=int(result["height"]),
        instructions=str(result["instructions"])
    )


@app.post(
    "/show_overlay",
    summary="Display overlay with coordinates and instructions",
    description="Triggers the overlay window to display at the specified coordinates with instructions",
    tags=["Overlay"],
    responses={
        200: {
            "description": "Overlay displayed successfully",
            "content": {
                "application/json": {
                    "example": {"status": "success", "message": "Overlay displayed"}
                }
            }
        },
        500: {
            "description": "Error displaying overlay",
            "content": {
                "application/json": {
                    "example": {"detail": "Error running overlay"}
                }
            }
        }
    }
)
async def show_overlay(request: OverlayRequest):
    """
    Display the overlay window at the specified coordinates with instructions.
    
    This endpoint triggers the overlay.py module to display a visual guide
    on the screen at the specified location.
    
    **Example request:**
    ```json
    {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 50,
        "text": "Click this button to proceed"
    }
    ```
    """
    try:
        # Get the path to the overlay module
        overlay_module = Path(__file__).parent / "overlay.py"
        
        # Run the overlay as a subprocess
        # Use the Python interpreter that's running this server
        python_exe = sys.executable
        
        subprocess.Popen(
            [
                python_exe,
                "-m",
                "src.drippy.overlay",
                str(request.x),
                str(request.y),
                str(request.width),
                str(request.height),
                "--text",
                request.text
            ],
            cwd=Path(__file__).parent.parent.parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return {"status": "success", "message": "Overlay displayed"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error displaying overlay: {str(e)}"
        )

