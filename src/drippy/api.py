import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .screenshot_tool import take_screenshot, query_gemini_for_section

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

