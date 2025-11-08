import os
import subprocess
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .gemini_query import take_screenshot, query_gemini_for_section, query_gemini_for_next_action

app = FastAPI(
    title="Drippy API",
    description="Screen search API using Gemini AI to find elements on screen and return bounding boxes",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


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
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set"
        )
    
    # Take screenshot
    screenshot = take_screenshot()
    
    # Query Gemini for the next action
    result = query_gemini_for_next_action(screenshot, request.todo_list, api_key)
    
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

