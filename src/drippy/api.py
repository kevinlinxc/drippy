import os
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

