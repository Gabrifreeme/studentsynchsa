"""Playwright browser automation helpers for ACEsi.

Exposed behind the dev-mode flag so it's never exposed publicly. Used by
chat() to drive a headless Chromium instance for URL inspection and
error-message troubleshooting (works on Chris's i7-3777 / Intel HD 4000).
"""
import os
import base64
import time
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

_DEV_MODE = os.environ.get("ACE_DEV", "0") == "1"

def _goto(page, url, timeout=25000):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    except Exception:
        pass

def _title(page):
    try:
        return page.evaluate("() => document.title")
    except Exception:
        try:
            return page.title()
        except Exception:
            return ""

def browser_eval(url, script=None, wait_ms=1500):
    """Navigate to url, return page title + optional JS eval result (string)."""
    if not _DEV_MODE:
        return {"error": "browser automation disabled (set ACE_DEV=1 to enable)"}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-gpu",
                                               "--disable-dev-shm-usage"])
            page = browser.new_page()
            page.set_default_timeout(25000)
            _goto(page, url)
            time.sleep(wait_ms / 1000.0)
            result = {"url": page.url, "title": _title(page)}
            if script:
                try:
                    result["script_result"] = str(page.evaluate(script))
                except Exception as e:
                    result["script_error"] = str(e)
            browser.close()
            return result
    except Exception as e:
        logger.warning("browser_eval failed: %r", e)
        return {"error": str(e)}

def browser_screenshot(url, wait_ms=1500, full_page=False):
    """Navigate to url, return PNG base64 string."""
    if not _DEV_MODE:
        return {"error": "browser automation disabled (set ACE_DEV=1 to enable)"}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-gpu",
                                               "--disable-dev-shm-usage"])
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.set_default_timeout(25000)
            _goto(page, url)
            time.sleep(wait_ms / 1000.0)
            png_bytes = page.screenshot(full_page=full_page)
            title = _title(page)
            browser.close()
            return {"png_base64": base64.b64encode(png_bytes).decode("ascii"),
                    "title": title}
    except Exception as e:
        logger.warning("browser_screenshot failed: %r", e)
        return {"error": str(e)}

def browser_errors(url, wait_ms=1500):
    """Navigate to url, capture JS console errors + network failures."""
    if not _DEV_MODE:
        return {"error": "browser automation disabled (set ACE_DEV=1 to enable)"}
    console_msgs = []
    failed_reqs = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-gpu",
                                               "--disable-dev-shm-usage"])
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.on("console", lambda msg: console_msgs.append(
                        f"[{msg.type}] {msg.text()}") if msg.type in ("error", "warning") else None)
            page.on("pageerror", lambda exc: console_msgs.append(f"[pageerror] {exc}"))
            page.on("requestfailed", lambda req: failed_reqs.append(
                        f"{req.method} {req.url} -> {req.failure()['errorText']}"))
            page.set_default_timeout(25000)
            _goto(page, url)
            time.sleep(wait_ms / 1000.0)
            title = _title(page)
            browser.close()
            return {
                "url": page.url,
                "title": title,
                "console_errors": console_msgs[:30],
                "failed_requests": failed_reqs[:30],
            }
    except Exception as e:
        logger.warning("browser_errors failed: %r", e)
        return {"error": str(e)}