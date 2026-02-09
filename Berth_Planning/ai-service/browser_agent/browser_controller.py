"""
Browser Controller for Browser Agent
Uses Playwright for browser automation
Includes Windows screen control via pyautogui for full agentic operation
"""

import asyncio
import base64
import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime
import json
import time

logger = logging.getLogger(__name__)

# Import Playwright - will be installed separately
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")

# Import pyautogui for Windows screen control
try:
    import pyautogui
    from PIL import Image
    import io
    PYAUTOGUI_AVAILABLE = True
    # Safety settings
    pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
    pyautogui.PAUSE = 0.1  # Small pause between actions
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not installed. Run: pip install pyautogui pillow")


class WindowsScreenController:
    """
    Controls the entire Windows screen using pyautogui.
    Enables true agentic control visible to the user.
    """
    
    def __init__(self, screenshot_dir: Optional[str] = None):
        if not PYAUTOGUI_AVAILABLE:
            raise ImportError(
                "pyautogui is required for Windows screen control. "
                "Install with: pip install pyautogui pillow"
            )
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self._action_log: List[Dict[str, Any]] = []
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the Windows screen size"""
        return pyautogui.size()
    
    def take_full_screen_screenshot(self, filename: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Take a screenshot of the entire Windows screen.
        
        Returns:
            Tuple of (file_path, base64_data)
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screen_{timestamp}.png"
            
            filepath = self.screenshot_dir / filename
            
            # Take screenshot of entire screen
            screenshot = pyautogui.screenshot()
            screenshot.save(str(filepath))
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"Full screen screenshot saved: {filepath}")
            return str(filepath), base64_data
            
        except Exception as e:
            logger.error(f"Failed to take full screen screenshot: {e}")
            return None, None
    
    def move_mouse_visual(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Move mouse to position with visual animation"""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self._log_action("mouse_move", {"x": x, "y": y})
            return True
        except Exception as e:
            logger.error(f"Mouse move failed: {e}")
            return False
    
    def click_at(self, x: int, y: int, button: str = 'left', clicks: int = 1) -> bool:
        """Click at specific screen coordinates"""
        try:
            pyautogui.click(x, y, button=button, clicks=clicks)
            self._log_action("click", {"x": x, "y": y, "button": button, "clicks": clicks})
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    def type_text_system(self, text: str, interval: float = 0.05) -> bool:
        """Type text using system keyboard"""
        try:
            pyautogui.typewrite(text, interval=interval)
            self._log_action("type", {"text": text[:50]})
            return True
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """Press a keyboard key"""
        try:
            pyautogui.press(key)
            self._log_action("key_press", {"key": key})
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False
    
    def hotkey(self, *keys: str) -> bool:
        """Press a keyboard hotkey combination"""
        try:
            pyautogui.hotkey(*keys)
            self._log_action("hotkey", {"keys": keys})
            return True
        except Exception as e:
            logger.error(f"Hotkey failed: {e}")
            return False
    
    def scroll_screen(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Scroll the screen at current or specified position"""
        try:
            pyautogui.scroll(clicks, x=x, y=y)
            self._log_action("scroll", {"clicks": clicks, "x": x, "y": y})
            return True
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return False
    
    def drag_to(self, x: int, y: int, duration: float = 0.5, button: str = 'left') -> bool:
        """Drag from current position to target"""
        try:
            pyautogui.dragTo(x, y, duration=duration, button=button)
            self._log_action("drag", {"x": x, "y": y})
            return True
        except Exception as e:
            logger.error(f"Drag failed: {e}")
            return False
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        return pyautogui.position()
    
    def locate_on_screen(self, image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int, int, int]]:
        """Locate an image on screen (returns bounding box)"""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                return (location.left, location.top, location.width, location.height)
            return None
        except Exception as e:
            logger.error(f"Image locate failed: {e}")
            return None
    
    def highlight_area(self, x: int, y: int, width: int = 100, height: int = 50, duration: float = 1.0):
        """
        Visual highlight by moving mouse around area.
        This creates a visible feedback effect.
        """
        try:
            center_x, center_y = x + width // 2, y + height // 2
            # Move to corners to create visual highlight effect
            points = [
                (x, y), (x + width, y), 
                (x + width, y + height), (x, y + height), 
                (center_x, center_y)
            ]
            step_duration = duration / len(points)
            for px, py in points:
                pyautogui.moveTo(px, py, duration=step_duration)
            return True
        except Exception as e:
            logger.error(f"Highlight failed: {e}")
            return False
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """Get log of all actions performed"""
        return self._action_log.copy()
    
    def clear_action_log(self):
        """Clear the action log"""
        self._action_log.clear()
    
    def _log_action(self, action_type: str, details: Dict[str, Any]):
        """Log an action for tracking"""
        self._action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            "details": details,
            "screen_size": pyautogui.size()
        })


class BrowserController:
    """
    Controls browser automation using Playwright.
    Provides methods for navigation, interaction, and observation.
    
    Supports two modes:
    1. Launch mode (default): Opens a new browser window
    2. Connect mode: Connects to existing Chrome via CDP (Chrome DevTools Protocol)
       - User must start Chrome with: --remote-debugging-port=9222
       - Agent takes control of existing browser window visible to user
    """
    
    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        timeout_ms: int = 30000,
        screenshot_dir: Optional[str] = None,
        cdp_endpoint: Optional[str] = None
    ):
        """
        Initialize browser controller.
        
        Args:
            headless: Run browser in headless mode (ignored if connecting via CDP)
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            timeout_ms: Default timeout for operations
            screenshot_dir: Directory to save screenshots
            cdp_endpoint: Chrome DevTools Protocol endpoint (e.g., 'http://localhost:9222')
                          If provided, connects to existing Chrome instead of launching new one.
                          User must start Chrome with: --remote-debugging-port=9222
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for browser automation. "
                "Install with: pip install playwright && playwright install chromium"
            )
        
        self.headless = headless
        self.viewport = {"width": viewport_width, "height": viewport_height}
        self.timeout = timeout_ms
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.cdp_endpoint = cdp_endpoint
        
        # Playwright instances
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # State tracking
        self._is_initialized = False
        self._current_url = ""
        self._page_loaded = False
        self._connected_mode = False  # True if connected via CDP
    
    async def initialize(self) -> bool:
        """Initialize the browser (launch new or connect to existing)"""
        try:
            self._playwright = await async_playwright().start()
            
            if self.cdp_endpoint:
                # Connect to existing Chrome via CDP
                return await self._connect_to_existing_browser()
            else:
                # Launch new browser
                return await self._launch_new_browser()
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False
    
    async def _connect_to_existing_browser(self) -> bool:
        """Connect to an existing Chrome instance via Chrome DevTools Protocol"""
        try:
            logger.info(f"Connecting to existing Chrome at {self.cdp_endpoint}")
            
            # Connect over CDP
            self._browser = await self._playwright.chromium.connect_over_cdp(
                self.cdp_endpoint
            )
            
            # Get existing contexts and pages
            contexts = self._browser.contexts
            if contexts:
                self._context = contexts[0]
                pages = self._context.pages
                if pages:
                    # Use the first open page (or find the SmartBerth one)
                    self._page = pages[0]
                    # Try to find the SmartBerth page
                    for p in pages:
                        if 'localhost' in p.url or 'smartberth' in p.url.lower():
                            self._page = p
                            break
                    logger.info(f"Attached to existing page: {self._page.url}")
                else:
                    # No pages open, create one
                    self._page = await self._context.new_page()
            else:
                # No contexts, create new one
                self._context = await self._browser.new_context()
                self._page = await self._context.new_page()
            
            self._page.set_default_timeout(self.timeout)
            self._is_initialized = True
            self._connected_mode = True
            self._current_url = self._page.url
            
            logger.info("Connected to existing Chrome successfully - agent will control YOUR browser!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Chrome via CDP: {e}")
            logger.error("Make sure Chrome is started with: --remote-debugging-port=9222")
            return False
    
    async def _launch_new_browser(self) -> bool:
        """Launch a new browser instance"""
        try:
            # Launch Chromium
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--no-sandbox',
                ]
            )
            
            # Create context with viewport
            self._context = await self._browser.new_context(
                viewport=self.viewport,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Create page
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.timeout)
            
            self._is_initialized = True
            self._connected_mode = False
            logger.info("Browser launched successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            return False
    
    async def close(self):
        """Close the browser and cleanup resources"""
        try:
            if self._connected_mode:
                # In connected mode, DON'T close the user's browser
                # Just disconnect from it
                if self._browser:
                    await self._browser.close()  # This disconnects without closing Chrome
                logger.info("Disconnected from browser (keeping Chrome open)")
            else:
                # In launch mode, close everything
                if self._page:
                    await self._page.close()
                if self._context:
                    await self._context.close()
                if self._browser:
                    await self._browser.close()
                logger.info("Browser closed successfully")
            
            if self._playwright:
                await self._playwright.stop()
            
            self._is_initialized = False
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    @property
    def is_ready(self) -> bool:
        """Check if browser is ready for operations"""
        if not self._is_initialized or self._page is None:
            return False
        # Check if page is still open
        try:
            return not self._page.is_closed()
        except Exception:
            return False
    
    # ==================== NAVIGATION ====================
    
    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> Tuple[bool, str]:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: Wait condition (load, domcontentloaded, networkidle)
            
        Returns:
            Tuple of (success, error_message)
        """
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            # Use domcontentloaded instead of networkidle for React apps
            # as they have ongoing WebSocket connections for HMR
            await self._page.goto(url, wait_until=wait_until, timeout=15000)
            # Give React a moment to render
            await asyncio.sleep(1)
            self._current_url = url
            self._page_loaded = True
            logger.info(f"Navigated to: {url}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Navigation failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def go_back(self) -> Tuple[bool, str]:
        """Go back in browser history"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.go_back()
            self._current_url = self._page.url
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def go_forward(self) -> Tuple[bool, str]:
        """Go forward in browser history"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.go_forward()
            self._current_url = self._page.url
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def refresh(self) -> Tuple[bool, str]:
        """Refresh the current page"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.reload()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    # ==================== INTERACTION ====================
    
    async def click(self, selector: str, timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        Click an element.
        
        Args:
            selector: CSS selector or text-based selector
            timeout: Optional timeout override
            
        Returns:
            Tuple of (success, error_message)
        """
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            element = self._page.locator(selector).first
            await element.click(timeout=timeout or self.timeout)
            logger.info(f"Clicked: {selector}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Click failed for '{selector}': {str(e)}"
            logger.warning(error_msg)
            return False, error_msg
    
    async def click_text(self, text: str) -> Tuple[bool, str]:
        """Click an element containing specific text"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.get_by_text(text, exact=False).first.click()
            logger.info(f"Clicked text: '{text}'")
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def double_click(self, selector: str) -> Tuple[bool, str]:
        """Double-click an element"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.dblclick()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def right_click(self, selector: str) -> Tuple[bool, str]:
        """Right-click an element"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.click(button="right")
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def hover(self, selector: str) -> Tuple[bool, str]:
        """Hover over an element"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.hover()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def type_text(
        self, 
        selector: str, 
        text: str, 
        clear_first: bool = True,
        delay: int = 50
    ) -> Tuple[bool, str]:
        """
        Type text into an input element.
        
        Args:
            selector: CSS selector for the input
            text: Text to type
            clear_first: Clear existing content first
            delay: Delay between keystrokes in ms
        """
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            element = self._page.locator(selector).first
            
            if clear_first:
                await element.fill("")
            
            await element.type(text, delay=delay)
            logger.info(f"Typed into {selector}: '{text[:30]}...'")
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    async def fill(self, selector: str, value: str) -> Tuple[bool, str]:
        """Fill an input field (faster than type_text)"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.fill(value)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def select_option(self, selector: str, value: str) -> Tuple[bool, str]:
        """Select an option from a dropdown"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.select_option(value)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def clear(self, selector: str) -> Tuple[bool, str]:
        """Clear an input field"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.fill("")
            return True, ""
        except Exception as e:
            return False, str(e)
    
    # ==================== SCROLLING ====================
    
    async def scroll_down(self, pixels: int = 500) -> Tuple[bool, str]:
        """Scroll down by specified pixels"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.evaluate(f"window.scrollBy(0, {pixels})")
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def scroll_up(self, pixels: int = 500) -> Tuple[bool, str]:
        """Scroll up by specified pixels"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.evaluate(f"window.scrollBy(0, -{pixels})")
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def scroll_to_element(self, selector: str) -> Tuple[bool, str]:
        """Scroll to make an element visible"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.scroll_into_view_if_needed()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def scroll_to_top(self) -> Tuple[bool, str]:
        """Scroll to the top of the page"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.evaluate("window.scrollTo(0, 0)")
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def scroll_to_bottom(self) -> Tuple[bool, str]:
        """Scroll to the bottom of the page"""
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            return True, ""
        except Exception as e:
            return False, str(e)
    
    # ==================== OBSERVATION ====================
    
    async def get_page_html(self) -> str:
        """Get the current page HTML"""
        if not self.is_ready:
            return ""
        
        try:
            return await self._page.content()
        except Exception as e:
            logger.error(f"Failed to get page HTML: {e}")
            return ""
    
    async def get_page_url(self) -> str:
        """Get the current page URL"""
        if not self.is_ready:
            return ""
        
        return self._page.url
    
    async def get_page_title(self) -> str:
        """Get the current page title"""
        if not self.is_ready:
            return ""
        
        try:
            return await self._page.title()
        except Exception as e:
            return ""
    
    async def take_screenshot(
        self, 
        full_page: bool = False,
        filename: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[bytes]]:
        """
        Take a screenshot of the current page.
        
        Args:
            full_page: Capture full scrollable page
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Tuple of (file_path, base64_data)
        """
        if not self.is_ready:
            return None, None
        
        try:
            # Generate filename
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            filepath = self.screenshot_dir / filename
            
            # Take screenshot
            screenshot_bytes = await self._page.screenshot(
                full_page=full_page,
                type="png"
            )
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(screenshot_bytes)
            
            # Convert to base64
            base64_data = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath), base64_data
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None, None
    
    async def get_element_text(self, selector: str) -> Optional[str]:
        """Get text content of an element"""
        if not self.is_ready:
            return None
        
        try:
            return await self._page.locator(selector).first.text_content()
        except Exception as e:
            return None
    
    async def get_element_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get an attribute value from an element"""
        if not self.is_ready:
            return None
        
        try:
            return await self._page.locator(selector).first.get_attribute(attribute)
        except Exception as e:
            return None
    
    async def element_exists(self, selector: str) -> bool:
        """Check if an element exists on the page"""
        if not self.is_ready:
            return False
        
        try:
            count = await self._page.locator(selector).count()
            return count > 0
        except Exception as e:
            return False
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> Tuple[bool, str]:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector
            timeout: Timeout in ms
            state: State to wait for (attached, detached, visible, hidden)
        """
        if not self.is_ready:
            return False, "Browser not initialized"
        
        try:
            await self._page.locator(selector).first.wait_for(
                timeout=timeout or self.timeout,
                state=state
            )
            return True, ""
        except Exception as e:
            return False, str(e)
    
    async def wait(self, milliseconds: int) -> Tuple[bool, str]:
        """Wait for specified milliseconds"""
        try:
            await asyncio.sleep(milliseconds / 1000)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    # ==================== DATA EXTRACTION ====================
    
    async def extract_table_data(self, table_selector: str = "table") -> list:
        """Extract data from a table element"""
        if not self.is_ready:
            return []
        
        try:
            table = self._page.locator(table_selector).first
            rows = await table.locator("tr").all()
            
            data = []
            for row in rows:
                cells = await row.locator("td, th").all()
                row_data = []
                for cell in cells:
                    text = await cell.text_content()
                    row_data.append(text.strip() if text else "")
                if row_data:
                    data.append(row_data)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract table data: {e}")
            return []
    
    async def extract_links(self) -> list:
        """Extract all links from the page"""
        if not self.is_ready:
            return []
        
        try:
            links = await self._page.locator("a[href]").all()
            result = []
            for link in links:
                href = await link.get_attribute("href")
                text = await link.text_content()
                result.append({
                    "href": href,
                    "text": text.strip() if text else ""
                })
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract links: {e}")
            return []
    
    async def evaluate_js(self, script: str) -> Any:
        """Evaluate JavaScript on the page"""
        if not self.is_ready:
            return None
        
        try:
            return await self._page.evaluate(script)
        except Exception as e:
            logger.error(f"JS evaluation failed: {e}")
            return None

    # ==================== WINDOWS SCREEN CONTROL ====================
    
    def get_windows_controller(self) -> Optional['WindowsScreenController']:
        """Get a WindowsScreenController for system-level control"""
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("Windows control not available - pyautogui not installed")
            return None
        try:
            return WindowsScreenController(screenshot_dir=str(self.screenshot_dir))
        except Exception as e:
            logger.error(f"Failed to create Windows controller: {e}")
            return None
    
    async def take_full_screen_screenshot(
        self, 
        filename: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Take a screenshot of the entire Windows screen (not just browser).
        This shows exactly what the user sees.
        
        Returns:
            Tuple of (file_path, base64_data)
        """
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("Full screen screenshot not available - using browser screenshot")
            return await self.take_screenshot(full_page=False, filename=filename)
        
        try:
            controller = WindowsScreenController(screenshot_dir=str(self.screenshot_dir))
            return controller.take_full_screen_screenshot(filename)
        except Exception as e:
            logger.error(f"Failed to take full screen screenshot: {e}")
            return None, None
    
    async def highlight_element_visual(self, selector: str, duration: float = 1.5) -> bool:
        """
        Highlight an element with visual feedback visible on screen.
        Uses CSS injection to create a glowing border effect.
        """
        if not self.is_ready:
            return False
        
        try:
            # Inject CSS highlight animation
            await self._page.evaluate(f'''
                (function() {{
                    const el = document.querySelector("{selector}");
                    if (!el) return false;
                    
                    // Save original style
                    const originalOutline = el.style.outline;
                    const originalTransition = el.style.transition;
                    const originalBoxShadow = el.style.boxShadow;
                    
                    // Add highlight effect
                    el.style.transition = "all 0.2s ease-in-out";
                    el.style.outline = "3px solid #ff6b35";
                    el.style.boxShadow = "0 0 20px 5px rgba(255, 107, 53, 0.7)";
                    
                    // Pulse animation
                    let pulseCount = 0;
                    const maxPulses = 3;
                    const pulseInterval = setInterval(() => {{
                        if (pulseCount >= maxPulses) {{
                            clearInterval(pulseInterval);
                            // Restore original style
                            el.style.outline = originalOutline;
                            el.style.transition = originalTransition;
                            el.style.boxShadow = originalBoxShadow;
                            return;
                        }}
                        el.style.boxShadow = pulseCount % 2 === 0 
                            ? "0 0 30px 10px rgba(255, 107, 53, 0.9)"
                            : "0 0 20px 5px rgba(255, 107, 53, 0.7)";
                        pulseCount++;
                    }}, 200);
                    
                    return true;
                }})()
            ''')
            await asyncio.sleep(duration)
            return True
        except Exception as e:
            logger.error(f"Failed to highlight element: {e}")
            return False
    
    async def expand_all_panels(self) -> int:
        """
        Expand all collapsible panels/accordions on the page.
        Returns the number of panels expanded.
        """
        if not self.is_ready:
            return 0
        
        try:
            # Find and click all collapsed accordion/chevron buttons
            expanded = await self._page.evaluate('''
                (function() {
                    let expandedCount = 0;
                    
                    // Find common collapse toggle patterns
                    const toggleSelectors = [
                        '[data-state="closed"]',
                        '[aria-expanded="false"]',
                        '.collapsed',
                        '[class*="chevron-right"]',
                        '[class*="collapsed"]',
                        'button[class*="accordion"]',
                        'div[class*="expandable"]:not(.expanded)'
                    ];
                    
                    toggleSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            if (el.click) {
                                el.click();
                                expandedCount++;
                            }
                        });
                    });
                    
                    return expandedCount;
                })()
            ''')
            
            # Wait for animations
            await asyncio.sleep(0.5)
            
            logger.info(f"Expanded {expanded} panels")
            return expanded
            
        except Exception as e:
            logger.error(f"Failed to expand panels: {e}")
            return 0
    
    async def show_action_overlay(self, action: str, details: str = "", duration: float = 2.0) -> bool:
        """
        Display an on-screen overlay showing the current action.
        This provides visual feedback to the user.
        """
        if not self.is_ready:
            return False
        
        try:
            await self._page.evaluate(f'''
                (function() {{
                    // Remove existing overlay if any
                    const existing = document.getElementById('agent-action-overlay');
                    if (existing) existing.remove();
                    
                    // Create overlay
                    const overlay = document.createElement('div');
                    overlay.id = 'agent-action-overlay';
                    overlay.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        color: white;
                        padding: 16px 24px;
                        border-radius: 12px;
                        z-index: 999999;
                        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                        border: 1px solid rgba(255,255,255,0.1);
                        animation: slideIn 0.3s ease-out;
                        max-width: 350px;
                    `;
                    
                    // Add animation keyframes
                    if (!document.getElementById('agent-overlay-styles')) {{
                        const style = document.createElement('style');
                        style.id = 'agent-overlay-styles';
                        style.textContent = `
                            @keyframes slideIn {{
                                from {{ transform: translateX(100px); opacity: 0; }}
                                to {{ transform: translateX(0); opacity: 1; }}
                            }}
                            @keyframes fadeOut {{
                                from {{ opacity: 1; }}
                                to {{ opacity: 0; }}
                            }}
                        `;
                        document.head.appendChild(style);
                    }}
                    
                    overlay.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 10px; height: 10px; background: #4ade80; border-radius: 50%; animation: pulse 1s infinite;"></div>
                            <span style="font-weight: 600; font-size: 14px;">Browser Agent</span>
                        </div>
                        <div style="margin-top: 8px; font-size: 16px; font-weight: 700; color: #60a5fa;">
                            {action}
                        </div>
                        <div style="margin-top: 4px; font-size: 12px; color: rgba(255,255,255,0.7); line-height: 1.4;">
                            {details}
                        </div>
                    `;
                    
                    document.body.appendChild(overlay);
                    
                    // Auto-remove after duration
                    setTimeout(() => {{
                        overlay.style.animation = 'fadeOut 0.3s ease-out forwards';
                        setTimeout(() => overlay.remove(), 300);
                    }}, {int(duration * 1000)});
                    
                    return true;
                }})()
            ''')
            return True
        except Exception as e:
            logger.error(f"Failed to show action overlay: {e}")
            return False
    
    async def create_final_summary_view(self, summary_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a comprehensive final view with all relevant data expanded.
        Takes a full-screen screenshot after preparation.
        
        Args:
            summary_data: Data to summarize (will be merged with page data)
            
        Returns:
            Tuple of (screenshot_path, base64_data)
        """
        if not self.is_ready:
            return None, None
        
        try:
            # First expand all panels
            await self.expand_all_panels()
            
            # Show summary overlay
            summary_text = summary_data.get('summary', 'Task completed')
            await self.show_action_overlay(
                "Task Complete",
                summary_text[:200] + "..." if len(summary_text) > 200 else summary_text,
                duration=5.0
            )
            
            # Wait for animations
            await asyncio.sleep(1)
            
            # Take full screen screenshot
            return await self.take_full_screen_screenshot(filename="final_summary.png")
            
        except Exception as e:
            logger.error(f"Failed to create final summary view: {e}")
            return None, None
    
    async def focus_browser_window(self) -> bool:
        """Bring the browser window to the foreground"""
        if not self.is_ready:
            return False
        
        try:
            # Use JavaScript to focus
            await self._page.evaluate("window.focus()")
            
            # If we have pyautogui, also try system-level focus
            if PYAUTOGUI_AVAILABLE:
                # Press Alt+Tab would be risky, so just use page focus
                pass
            
            return True
        except Exception as e:
            logger.error(f"Failed to focus browser: {e}")
            return False