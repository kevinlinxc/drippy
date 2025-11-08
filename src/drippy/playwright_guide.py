"""
Playwright-based browser automation and DOM injection for step-by-step guidance.
"""

import asyncio
import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class PlaywrightGuide:
    """Manages browser automation and DOM injection for user guidance."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_step = 0
        self.step_completed = False
        
    async def start(self):
        """Start Playwright and open a browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Listen for navigation to detect step completion
        self.page.on("framenavigated", self._on_navigation)
        
    async def close(self):
        """Close the browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def _on_navigation(self, frame):
        """Called when page navigates - can be used to detect step completion."""
        if frame == self.page.main_frame:
            # Navigation occurred, might indicate step completion
            pass
    
    async def navigate(self, url: str):
        """Navigate to a URL."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        await self.page.goto(url, wait_until="networkidle")
    
    async def open_browser(self, browser_type: str = "chromium"):
        """Open a browser (already done in start(), but kept for API compatibility)."""
        # Browser is already open from start()
        pass
    
    async def inject_guidance(self, selector: str, instructions: str, gif_path: Optional[str] = None):
        """
        Inject guidance overlay into the DOM at the specified element.
        
        Args:
            selector: CSS selector for the element to highlight
            instructions: Text instructions to display
            gif_path: Path to the GIF avatar (optional)
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        # Load GIF as base64 if provided
        gif_data_url = ""
        if gif_path:
            gif_file = Path(gif_path)
            if gif_file.exists():
                gif_bytes = gif_file.read_bytes()
                gif_base64 = base64.b64encode(gif_bytes).decode('utf-8')
                gif_data_url = f"data:image/gif;base64,{gif_base64}"
        
        # Get element position
        try:
            element = await self.page.query_selector(selector)
            if not element:
                print(f"Warning: Element not found with selector: {selector}")
                return
            
            box = await element.bounding_box()
            if not box:
                print(f"Warning: Could not get bounding box for element: {selector}")
                return
        except Exception as e:
            print(f"Error getting element position: {e}")
            return
        
        # Inject the guidance overlay
        injection_script = f"""
        (function() {{
            // Remove existing guidance if any
            const existing = document.getElementById('drippy-guidance');
            if (existing) existing.remove();
            const existingHighlight = document.getElementById('drippy-highlight');
            if (existingHighlight) existingHighlight.remove();
            
            // Highlight the target element
            const targetElement = document.querySelector({json.dumps(selector)});
            if (targetElement) {{
                // Create highlight overlay
                const highlight = document.createElement('div');
                highlight.id = 'drippy-highlight';
                const rect = targetElement.getBoundingClientRect();
                highlight.style.cssText = `
                    position: fixed;
                    left: ${{rect.left + window.scrollX}}px;
                    top: ${{rect.top + window.scrollY}}px;
                    width: ${{rect.width}}px;
                    height: ${{rect.height}}px;
                    border: 3px solid #4CAF50;
                    box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.3), 0 0 20px rgba(76, 175, 80, 0.5);
                    border-radius: 4px;
                    z-index: 999998;
                    pointer-events: none;
                    animation: drippy-pulse 2s ease-in-out infinite;
                `;
                document.body.appendChild(highlight);
                
                // Add pulse animation
                if (!document.getElementById('drippy-styles')) {{
                    const style = document.createElement('style');
                    style.id = 'drippy-styles';
                    style.textContent = `
                        @keyframes drippy-pulse {{
                            0%, 100% {{ opacity: 1; transform: scale(1); }}
                            50% {{ opacity: 0.8; transform: scale(1.02); }}
                        }}
                    `;
                    document.head.appendChild(style);
                }}
            }}
            
            // Create guidance container
            const guidance = document.createElement('div');
            guidance.id = 'drippy-guidance';
            guidance.style.cssText = `
                position: fixed;
                z-index: 999999;
                pointer-events: none;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            `;
            
            // Position near the element
            const elementBox = {{
                x: {box['x']},
                y: {box['y']},
                width: {box['width']},
                height: {box['height']}
            }};
            
            // Calculate position (to the right of element, or below if not enough space)
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            let guidanceX = elementBox.x + elementBox.width + 20;
            let guidanceY = elementBox.y;
            
            // Adjust if would go off screen
            if (guidanceX + 300 > viewportWidth) {{
                // Put it to the left instead
                guidanceX = elementBox.x - 320;
            }}
            if (guidanceY + 200 > viewportHeight) {{
                // Put it above
                guidanceY = elementBox.y - 200;
            }}
            
            // Create speech bubble container
            const bubble = document.createElement('div');
            bubble.style.cssText = `
                position: absolute;
                left: ${{guidanceX}}px;
                top: ${{guidanceY}}px;
                background: rgba(20, 20, 20, 0.95);
                border-radius: 12px;
                padding: 16px 20px;
                color: white;
                font-size: 15px;
                font-weight: bold;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);
                max-width: 300px;
                pointer-events: auto;
            `;
            
            // Add avatar if provided
            {f'''
            const avatar = document.createElement('img');
            avatar.src = '{gif_data_url}';
            avatar.style.cssText = `
                width: 80px;
                height: 80px;
                position: absolute;
                left: -100px;
                top: 0;
            `;
            bubble.appendChild(avatar);
            ''' if gif_data_url else ''}
            
            // Add instructions text
            const text = document.createElement('div');
            text.textContent = {json.dumps(instructions)};
            text.style.cssText = `
                margin-top: ${'20px' if gif_data_url else '0'};
                line-height: 1.4;
            `;
            bubble.appendChild(text);
            
            // Add speech bubble tail pointing to element
            const tail = document.createElement('div');
            tail.style.cssText = `
                position: absolute;
                left: -15px;
                top: 20px;
                width: 0;
                height: 0;
                border-top: 12px solid transparent;
                border-bottom: 12px solid transparent;
                border-right: 15px solid rgba(20, 20, 20, 0.95);
            `;
            bubble.appendChild(tail);
            
            guidance.appendChild(bubble);
            document.body.appendChild(guidance);
        }})();
        """
        
        await self.page.evaluate(injection_script)
    
    async def wait_for_step_completion(self, expected_url: Optional[str] = None, 
                                      expected_selector: Optional[str] = None,
                                      timeout: int = 30000):
        """
        Wait for the user to complete the current step.
        
        Detects completion by:
        - URL change (if expected_url is provided)
        - Element appearance (if expected_selector is provided)
        - Page content change (fallback)
        
        Args:
            expected_url: URL pattern that indicates step completion (can be partial)
            expected_selector: Element selector that indicates step completion
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if step completed, False if timeout
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            if expected_url:
                # Wait for URL to change (supports partial matches)
                if expected_url.startswith("http"):
                    # Full URL match
                    await self.page.wait_for_url(expected_url, timeout=timeout)
                else:
                    # Partial URL match
                    await self.page.wait_for_function(
                        f"window.location.href.includes('{expected_url}')",
                        timeout=timeout
                    )
                return True
            elif expected_selector:
                # Wait for element to appear
                await self.page.wait_for_selector(expected_selector, timeout=timeout)
                return True
            else:
                # Fallback: monitor for URL or content changes
                initial_url = self.page.url
                initial_content = await self.page.content()
                
                # Poll for changes
                start_time = asyncio.get_event_loop().time()
                while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
                    current_url = self.page.url
                    current_content = await self.page.content()
                    
                    # Check if URL changed
                    if current_url != initial_url:
                        return True
                    
                    # Check if content changed significantly (more than just timestamps)
                    if current_content != initial_content:
                        # Might be a change, wait a bit more to confirm
                        await asyncio.sleep(0.5)
                        new_content = await self.page.content()
                        if new_content != current_content:
                            return True
                    
                    await asyncio.sleep(0.5)
                
                # Timeout - assume user is still working
                return False
        except Exception as e:
            print(f"Step completion detection: {e}")
            return False
    
    async def remove_guidance(self):
        """Remove the guidance overlay and highlight from the DOM."""
        if not self.page:
            return
        
        await self.page.evaluate("""
            const guidance = document.getElementById('drippy-guidance');
            if (guidance) guidance.remove();
            const highlight = document.getElementById('drippy-highlight');
            if (highlight) highlight.remove();
        """)
    
    async def take_screenshot(self, path: str):
        """Take a screenshot of the current page."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        await self.page.screenshot(path=path)

