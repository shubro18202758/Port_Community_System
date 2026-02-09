"""
Action Executor for Browser Agent
Executes LLM-decided actions via the browser controller
Now with VISUAL FEEDBACK for user transparency
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
import time

from .action_schema import BrowserAction, ActionType, ActionResult
from .browser_controller import BrowserController
from .dom_extractor import DOMExtractor

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes browser actions decided by the LLM.
    Bridges the gap between LLM decisions and browser automation.
    Now includes VISUAL FEEDBACK to show actions on screen.
    """
    
    def __init__(
        self,
        browser: BrowserController,
        dom_extractor: DOMExtractor,
        on_action_start: Optional[Callable[[BrowserAction], Awaitable[None]]] = None,
        on_action_complete: Optional[Callable[[ActionResult], Awaitable[None]]] = None,
        enable_visual_feedback: bool = True  # NEW: Enable visual feedback
    ):
        """
        Initialize action executor.
        
        Args:
            browser: Browser controller instance
            dom_extractor: DOM extractor instance
            on_action_start: Callback when action starts
            on_action_complete: Callback when action completes
            enable_visual_feedback: Show visual overlay for actions (default: True)
        """
        self.browser = browser
        self.dom_extractor = dom_extractor
        self._on_action_start = on_action_start
        self._on_action_complete = on_action_complete
        self.enable_visual_feedback = enable_visual_feedback
        
        # Action handlers mapping
        self._action_handlers = {
            ActionType.NAVIGATE: self._execute_navigate,
            ActionType.BACK: self._execute_back,
            ActionType.FORWARD: self._execute_forward,
            ActionType.REFRESH: self._execute_refresh,
            ActionType.CLICK: self._execute_click,
            ActionType.DOUBLE_CLICK: self._execute_double_click,
            ActionType.RIGHT_CLICK: self._execute_right_click,
            ActionType.HOVER: self._execute_hover,
            ActionType.TYPE: self._execute_type,
            ActionType.CLEAR: self._execute_clear,
            ActionType.SELECT: self._execute_select,
            ActionType.SCROLL_UP: self._execute_scroll_up,
            ActionType.SCROLL_DOWN: self._execute_scroll_down,
            ActionType.SCROLL_TO: self._execute_scroll_to,
            ActionType.READ_PAGE: self._execute_read_page,
            ActionType.EXTRACT_DATA: self._execute_extract_data,
            ActionType.SCREENSHOT: self._execute_screenshot,
            ActionType.WAIT: self._execute_wait,
            ActionType.COMPLETE: self._execute_complete,
            ActionType.FAIL: self._execute_fail,
            ActionType.ASK_USER: self._execute_ask_user,
        }
        
        # Action display names for visual feedback
        self._action_display_names = {
            ActionType.NAVIGATE: "🌐 Navigating",
            ActionType.BACK: "◀️ Going Back",
            ActionType.FORWARD: "▶️ Going Forward",
            ActionType.REFRESH: "🔄 Refreshing",
            ActionType.CLICK: "🖱️ Clicking",
            ActionType.DOUBLE_CLICK: "🖱️🖱️ Double Clicking",
            ActionType.RIGHT_CLICK: "🖱️ Right Clicking",
            ActionType.HOVER: "👆 Hovering",
            ActionType.TYPE: "⌨️ Typing",
            ActionType.CLEAR: "🗑️ Clearing",
            ActionType.SELECT: "📋 Selecting",
            ActionType.SCROLL_UP: "⬆️ Scrolling Up",
            ActionType.SCROLL_DOWN: "⬇️ Scrolling Down",
            ActionType.SCROLL_TO: "🎯 Scrolling To",
            ActionType.READ_PAGE: "👁️ Reading Page",
            ActionType.EXTRACT_DATA: "📊 Extracting Data",
            ActionType.SCREENSHOT: "📸 Taking Screenshot",
            ActionType.WAIT: "⏳ Waiting",
            ActionType.COMPLETE: "✅ Task Complete",
            ActionType.FAIL: "❌ Task Failed",
            ActionType.ASK_USER: "❓ Asking User",
        }
    
    async def _show_visual_feedback(self, action: BrowserAction) -> None:
        """Show visual feedback overlay before executing action"""
        if not self.enable_visual_feedback:
            return
        
        try:
            action_name = self._action_display_names.get(action.action_type, "🤖 Acting")
            target_desc = action.target[:60] if action.target else ""
            if action.value:
                target_desc = f"{target_desc} → {action.value[:30]}"
            
            await self.browser.show_action_overlay(
                action_name,
                target_desc,
                duration=1.5
            )
            
            # Highlight the target element if it's a click/hover action
            if action.target and action.action_type in [
                ActionType.CLICK, ActionType.DOUBLE_CLICK, 
                ActionType.RIGHT_CLICK, ActionType.HOVER,
                ActionType.TYPE, ActionType.SELECT
            ]:
                await self.browser.highlight_element_visual(action.target, duration=1.0)
                
        except Exception as e:
            logger.debug(f"Visual feedback failed (non-critical): {e}")
    
    async def execute(self, action: BrowserAction) -> ActionResult:
        """
        Execute a browser action with visual feedback.
        
        Args:
            action: The action to execute
            
        Returns:
            ActionResult with success/failure and observation data
        """
        start_time = time.time()
        
        # Notify action start
        if self._on_action_start:
            try:
                await self._on_action_start(action)
            except Exception as e:
                logger.warning(f"on_action_start callback failed: {e}")
        
        # SHOW VISUAL FEEDBACK before executing action
        await self._show_visual_feedback(action)
        
        logger.info(f"Executing action: {action.action_type.value} -> {action.target or 'N/A'}")
        
        try:
            # Get the handler for this action type
            handler = self._action_handlers.get(action.action_type)
            
            if not handler:
                result = ActionResult(
                    success=False,
                    action=action,
                    error_message=f"Unknown action type: {action.action_type}"
                )
            else:
                result = await handler(action)
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            result = ActionResult(
                success=False,
                action=action,
                error_message=str(e)
            )
        
        # Calculate execution time
        result.execution_time_ms = int((time.time() - start_time) * 1000)
        result.timestamp = datetime.now()
        
        # Notify action complete
        if self._on_action_complete:
            try:
                await self._on_action_complete(result)
            except Exception as e:
                logger.warning(f"on_action_complete callback failed: {e}")
        
        return result
    
    # ==================== NAVIGATION HANDLERS ====================
    
    async def _execute_navigate(self, action: BrowserAction) -> ActionResult:
        """Execute navigation action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Navigate action requires a URL target"
            )
        
        success, error = await self.browser.navigate(action.target)
        
        # Get page observation if successful
        dom_snapshot = None
        if success:
            html = await self.browser.get_page_html()
            dom_data = self.dom_extractor.extract_from_html(html, action.target)
            dom_snapshot = self.dom_extractor.create_llm_context(dom_data, "observe page")
        
        return ActionResult(
            success=success,
            action=action,
            dom_snapshot=dom_snapshot,
            error_message=error if not success else None
        )
    
    async def _execute_back(self, action: BrowserAction) -> ActionResult:
        """Execute back navigation"""
        success, error = await self.browser.go_back()
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_forward(self, action: BrowserAction) -> ActionResult:
        """Execute forward navigation"""
        success, error = await self.browser.go_forward()
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_refresh(self, action: BrowserAction) -> ActionResult:
        """Execute page refresh"""
        success, error = await self.browser.refresh()
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    # ==================== INTERACTION HANDLERS ====================
    
    async def _execute_click(self, action: BrowserAction) -> ActionResult:
        """Execute click action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Click action requires a target selector"
            )
        
        # Try direct selector first
        success, error = await self.browser.click(action.target)
        
        # If failed, try text-based click
        if not success and action.value:
            success, error = await self.browser.click_text(action.value)
        
        # Wait for potential page update
        if success:
            await asyncio.sleep(0.5)
        
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_double_click(self, action: BrowserAction) -> ActionResult:
        """Execute double-click action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Double-click action requires a target selector"
            )
        
        success, error = await self.browser.double_click(action.target)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_right_click(self, action: BrowserAction) -> ActionResult:
        """Execute right-click action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Right-click action requires a target selector"
            )
        
        success, error = await self.browser.right_click(action.target)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_hover(self, action: BrowserAction) -> ActionResult:
        """Execute hover action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Hover action requires a target selector"
            )
        
        success, error = await self.browser.hover(action.target)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_type(self, action: BrowserAction) -> ActionResult:
        """Execute type action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Type action requires a target selector"
            )
        
        if not action.value:
            return ActionResult(
                success=False,
                action=action,
                error_message="Type action requires a value to type"
            )
        
        success, error = await self.browser.type_text(action.target, action.value)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_clear(self, action: BrowserAction) -> ActionResult:
        """Execute clear action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Clear action requires a target selector"
            )
        
        success, error = await self.browser.clear(action.target)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_select(self, action: BrowserAction) -> ActionResult:
        """Execute select option action"""
        if not action.target or not action.value:
            return ActionResult(
                success=False,
                action=action,
                error_message="Select action requires target and value"
            )
        
        success, error = await self.browser.select_option(action.target, action.value)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    # ==================== SCROLLING HANDLERS ====================
    
    async def _execute_scroll_up(self, action: BrowserAction) -> ActionResult:
        """Execute scroll up action"""
        pixels = int(action.value) if action.value and action.value.isdigit() else 500
        success, error = await self.browser.scroll_up(pixels)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_scroll_down(self, action: BrowserAction) -> ActionResult:
        """Execute scroll down action"""
        pixels = int(action.value) if action.value and action.value.isdigit() else 500
        success, error = await self.browser.scroll_down(pixels)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    async def _execute_scroll_to(self, action: BrowserAction) -> ActionResult:
        """Execute scroll to element action"""
        if not action.target:
            return ActionResult(
                success=False,
                action=action,
                error_message="Scroll-to action requires a target selector"
            )
        
        success, error = await self.browser.scroll_to_element(action.target)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    # ==================== OBSERVATION HANDLERS ====================
    
    async def _execute_read_page(self, action: BrowserAction) -> ActionResult:
        """Execute read page action - observe current page state"""
        url = await self.browser.get_page_url()
        html = await self.browser.get_page_html()
        
        if not html:
            return ActionResult(
                success=False,
                action=action,
                error_message="Failed to read page content"
            )
        
        # Extract DOM data
        dom_data = self.dom_extractor.extract_from_html(html, url)
        dom_snapshot = self.dom_extractor.create_llm_context(dom_data, "observe page")
        
        # Take screenshot
        screenshot_path, screenshot_base64 = await self.browser.take_screenshot()
        
        return ActionResult(
            success=True,
            action=action,
            dom_snapshot=dom_snapshot,
            screenshot_path=screenshot_path,
            screenshot_base64=screenshot_base64,
            extracted_data={"url": url, "element_count": dom_data.get("element_count", 0)}
        )
    
    async def _execute_extract_data(self, action: BrowserAction) -> ActionResult:
        """Execute data extraction action"""
        extracted = {}
        
        # Extract tables
        if action.target and "table" in action.target.lower():
            extracted["tables"] = await self.browser.extract_table_data(action.target)
        else:
            extracted["tables"] = await self.browser.extract_table_data()
        
        # Extract links
        if not action.target or "link" in action.target.lower():
            extracted["links"] = await self.browser.extract_links()
        
        # Extract specific element text
        if action.target:
            text = await self.browser.get_element_text(action.target)
            if text:
                extracted["target_text"] = text
        
        return ActionResult(
            success=True,
            action=action,
            extracted_data=extracted
        )
    
    async def _execute_screenshot(self, action: BrowserAction) -> ActionResult:
        """Execute screenshot action"""
        full_page = action.value == "full" if action.value else False
        screenshot_path, screenshot_base64 = await self.browser.take_screenshot(full_page=full_page)
        
        return ActionResult(
            success=screenshot_path is not None,
            action=action,
            screenshot_path=screenshot_path,
            screenshot_base64=screenshot_base64
        )
    
    async def _execute_wait(self, action: BrowserAction) -> ActionResult:
        """Execute wait action"""
        ms = int(action.value) if action.value and action.value.isdigit() else 1000
        success, error = await self.browser.wait(ms)
        return ActionResult(
            success=success,
            action=action,
            error_message=error if not success else None
        )
    
    # ==================== CONTROL HANDLERS ====================
    
    async def _execute_complete(self, action: BrowserAction) -> ActionResult:
        """Execute complete action - task finished"""
        return ActionResult(
            success=True,
            action=action,
            extracted_data={"status": "completed", "summary": action.reasoning}
        )
    
    async def _execute_fail(self, action: BrowserAction) -> ActionResult:
        """Execute fail action - task cannot be completed"""
        return ActionResult(
            success=False,
            action=action,
            error_message=action.reasoning or "Task cannot be completed"
        )
    
    async def _execute_ask_user(self, action: BrowserAction) -> ActionResult:
        """Execute ask user action - need clarification"""
        return ActionResult(
            success=True,
            action=action,
            extracted_data={
                "status": "needs_clarification",
                "question": action.reasoning or "I need more information to continue"
            }
        )
