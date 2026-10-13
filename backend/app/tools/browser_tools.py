"""
AgentOS - Controlled Playwright Browser Automation Tools.
Supports secure browser navigation restricted to approved domains (localhost/127.0.0.1),
accessible element selection, form filling, clicking, screenshot capture, state verification,
and resilient recovery from stale-element DOM detachments.
"""

from __future__ import annotations
import os
import re
import time
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.tools.base import ControlledBaseTool, ToolResult

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "sandbox_data", "screenshots")

ALLOWED_DOMAINS = {"localhost", "127.0.0.1"}

# Global browser session controller for reusing page across sequential tool steps
class BrowserSessionManager:
    _instance = None
    _playwright = None
    _browser = None
    _page = None

    @classmethod
    def get_page(cls):
        from playwright.sync_api import sync_playwright

        if cls._page is None or cls._page.is_closed():
            if cls._playwright is None:
                cls._playwright = sync_playwright().start()

            # Try Chrome first, then Edge fallback
            for channel in ["chrome", "msedge"]:
                try:
                    cls._browser = cls._playwright.chromium.launch(headless=True, channel=channel)
                    cls._page = cls._browser.new_page()
                    break
                except Exception:
                    continue

            if cls._page is None:
                # Direct chromium launch if channels fail
                cls._browser = cls._playwright.chromium.launch(headless=True)
                cls._page = cls._browser.new_page()

        return cls._page

    @classmethod
    def close(cls):
        try:
            if cls._page:
                cls._page.close()
            if cls._browser:
                cls._browser.close()
            if cls._playwright:
                cls._playwright.stop()
        except Exception:
            pass
        finally:
            cls._page = None
            cls._browser = None
            cls._playwright = None


def _validate_allowed_url(url: str):
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname not in ALLOWED_DOMAINS:
        raise PermissionError(
            f"Security Violation: Navigation to domain '{hostname}' is blocked. "
            f"AgentOS browser automation is strictly restricted to approved internal domains: {list(ALLOWED_DOMAINS)}"
        )


from backend.app.security.sanitizer import ContentSanitizer

def _sanitize_untrusted_content(text: str) -> str:
    """Neutralize prompt injection attempts embedded in untrusted external web content."""
    clean_text, _, _ = ContentSanitizer.sanitize(text, source_identifier="browser_content")
    return clean_text


class BrowserOpenUrlTool(ControlledBaseTool):
    name = "browser_open_url"
    description = "Open an approved URL in the controlled browser environment (restricted to localhost and 127.0.0.1)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Full URL to open, e.g. 'http://127.0.0.1:8000/portal/invoices'"
            }
        },
        "required": ["url"]
    }

    def execute(self, db_session: Session, url: str) -> ToolResult:
        try:
            _validate_allowed_url(url)
        except PermissionError as pe:
            return ToolResult(success=False, error=str(pe), retryable=False)

        try:
            page = BrowserSessionManager.get_page()
            response = page.goto(url, wait_until="networkidle", timeout=10000)
            status_code = response.status if response else 200
            title = page.title()

            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "status_code": status_code,
                    "title": title,
                    "message": f"Successfully loaded '{title}' ({url})"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Browser navigation error: {str(e)}",
                retryable=True
            )


class BrowserInspectPageTool(ControlledBaseTool):
    name = "browser_inspect_page"
    description = "Inspect the current browser page, extracting interactive elements, form fields, and text content."
    parameters_schema = {
        "type": "object",
        "properties": {
            "max_length": {
                "type": "integer",
                "description": "Max text length to return",
                "default": 4000
            }
        }
    }

    def execute(self, db_session: Session, max_length: int = 4000) -> ToolResult:
        try:
            page = BrowserSessionManager.get_page()
            title = page.title()
            current_url = page.url

            # Extract interactive inputs
            inputs = page.locator("input, select, textarea, button").all()
            interactive_elements = []
            for el in inputs[:20]:
                try:
                    tag = el.evaluate("e => e.tagName.toLowerCase()")
                    el_id = el.get_attribute("id") or ""
                    el_name = el.get_attribute("name") or ""
                    el_type = el.get_attribute("type") or ""
                    el_placeholder = el.get_attribute("placeholder") or ""
                    el_text = el.inner_text() if tag == "button" else ""
                    interactive_elements.append({
                        "tag": tag,
                        "id": el_id,
                        "name": el_name,
                        "type": el_type,
                        "placeholder": el_placeholder,
                        "text": el_text
                    })
                except Exception:
                    continue

            # Extract body text and sanitize prompt injection
            raw_text = page.locator("body").inner_text()
            clean_text = _sanitize_untrusted_content(raw_text)[:max_length]

            return ToolResult(
                success=True,
                data={
                    "url": current_url,
                    "title": title,
                    "interactive_elements_count": len(interactive_elements),
                    "interactive_elements": interactive_elements,
                    "page_text": clean_text
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Browser inspection failed: {str(e)}",
                retryable=True
            )


class BrowserFillFieldTool(ControlledBaseTool):
    name = "browser_fill_field"
    description = "Fill a form input field in the browser using an accessible selector (ID, name, or label)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector or ID, e.g. '#vendor_name' or 'input[name=\"amount\"]'"
            },
            "value": {
                "type": "string",
                "description": "Text value to enter into the field"
            }
        },
        "required": ["selector", "value"]
    }

    def execute(self, db_session: Session, selector: str, value: Any) -> ToolResult:
        try:
            page = BrowserSessionManager.get_page()
            loc = page.locator(selector)
            if not loc.is_visible(timeout=3000):
                # Fallback: search by name or placeholder
                clean_name = selector.lstrip("#.")
                alt_loc = page.locator(f"input[name='{clean_name}'], input[placeholder*='{clean_name}']")
                if alt_loc.is_visible(timeout=2000):
                    loc = alt_loc

            loc.fill(str(value))
            return ToolResult(
                success=True,
                data={
                    "selector": selector,
                    "filled_value": str(value),
                    "message": f"Successfully filled '{selector}' with '{value}'"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to fill field '{selector}': {str(e)}",
                retryable=True
            )


class BrowserClickTool(ControlledBaseTool):
    name = "browser_click"
    description = "Click an accessible button or link in the browser, with automatic recovery from stale DOM locators."
    parameters_schema = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector or button text, e.g. '#submit-btn' or 'Submit Invoice'"
            }
        },
        "required": ["selector"]
    }

    def execute(self, db_session: Session, selector: str) -> ToolResult:
        page = BrowserSessionManager.get_page()

        # Retry loop for resilient recovery against stale DOM states
        for attempt in range(2):
            try:
                if selector.startswith("#") or selector.startswith("."):
                    loc = page.locator(selector)
                else:
                    loc = page.locator(f"button:has-text('{selector}'), a:has-text('{selector}')")

                loc.wait_for(state="visible", timeout=4000)
                loc.click()
                page.wait_for_load_state("domcontentloaded", timeout=4000)

                return ToolResult(
                    success=True,
                    data={
                        "selector": selector,
                        "current_url": page.url,
                        "message": f"Successfully clicked element '{selector}'"
                    }
                )
            except Exception as e:
                if attempt == 0:
                    time.sleep(0.5)  # Stale DOM recovery backoff
                    continue
                return ToolResult(
                    success=False,
                    error=f"Browser click error on '{selector}': {str(e)}",
                    retryable=True
                )


class BrowserTakeScreenshotTool(ControlledBaseTool):
    name = "browser_take_screenshot"
    description = "Capture a PNG screenshot of the current page for audit evidence."
    parameters_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Screenshot file name prefix, e.g. 'portal_submission'"
            }
        }
    }

    def execute(self, db_session: Session, name: str = "screenshot") -> ToolResult:
        try:
            page = BrowserSessionManager.get_page()
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            filename = f"{name}_{int(time.time())}.png"
            full_path = os.path.join(SCREENSHOTS_DIR, filename)

            page.screenshot(path=full_path, full_page=True)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/")

            return ToolResult(
                success=True,
                data={
                    "filename": filename,
                    "file_path": rel_path,
                    "size_bytes": os.path.getsize(full_path),
                    "message": f"Captured screenshot to '{rel_path}'"
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Screenshot capture failed: {str(e)}",
                retryable=False
            )


class BrowserVerifyPageStateTool(ControlledBaseTool):
    name = "browser_verify_page_state"
    description = "Independently verify that expected success text or elements exist on the current page."
    parameters_schema = {
        "type": "object",
        "properties": {
            "expected_text": {
                "type": "string",
                "description": "Text expected to appear on the page (e.g. 'Successfully Registered')"
            }
        },
        "required": ["expected_text"]
    }

    def execute(self, db_session: Session, expected_text: str) -> ToolResult:
        try:
            page = BrowserSessionManager.get_page()
            content = page.content()
            body_text = page.locator("body").inner_text()

            matched = expected_text.lower() in body_text.lower() or expected_text.lower() in content.lower()
            if not matched:
                return ToolResult(
                    success=False,
                    error=f"Browser verification failed: expected text '{expected_text}' not found on page.",
                    data={"verified": False, "expected_text": expected_text, "current_url": page.url}
                )

            return ToolResult(
                success=True,
                data={
                    "verified": True,
                    "expected_text": expected_text,
                    "current_url": page.url,
                    "message": f"Ground-truth verified: '{expected_text}' confirmed in browser DOM."
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Page state verification error: {str(e)}",
                retryable=False
            )
