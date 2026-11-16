"""Script to capture desktop and mobile screenshots of Vaani AI UI using Playwright."""

import os
import shutil
import sys
import time
import threading
from pathlib import Path
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE))

from app import app

SCREENSHOT_DIR = WORKSPACE / "reports" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path(r"C:\Users\Admin\.gemini\antigravity\brain\1073c6eb-ca8f-407b-a860-bdb36b691be4")


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=5099):
        super().__init__()
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def run_capture():
    port = 5099
    server = ServerThread(app, port=port)
    server.start()
    time.sleep(1.0)

    url = f"http://127.0.0.1:{port}"
    print(f"Connecting to {url} with Playwright...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # 1. Desktop View (1280x800)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url)
            page.wait_for_selector("#text")

            # Clean state
            desktop_clean_path = SCREENSHOT_DIR / "desktop_clean.png"
            page.screenshot(path=str(desktop_clean_path))
            print(f"Saved: {desktop_clean_path}")

            # Send a multilingual Hindi message
            page.fill("#text", "मेरा नाम राहुल है और मैं मुंबई में रहता हूँ")
            page.click("button.send")

            # Wait for bot message and cards to appear
            page.wait_for_selector("#cards:not([hidden])", timeout=30000)
            page.wait_for_timeout(1000)

            desktop_active_path = SCREENSHOT_DIR / "desktop_analyzed.png"
            page.screenshot(path=str(desktop_active_path))
            print(f"Saved: {desktop_active_path}")

            # 2. Mobile View (375x720)
            mobile_page = browser.new_page(viewport={"width": 375, "height": 720})
            mobile_page.goto(url)
            mobile_page.wait_for_selector("#text")
            mobile_page.fill("#text", "Tell me a joke please")
            mobile_page.click("button.send")
            mobile_page.wait_for_selector("#cards:not([hidden])", timeout=30000)
            mobile_page.wait_for_timeout(1000)

            mobile_chat_path = SCREENSHOT_DIR / "mobile_chat.png"
            mobile_page.screenshot(path=str(mobile_chat_path))
            print(f"Saved: {mobile_chat_path}")

            # Switch to NLP Insights tab on mobile
            mobile_page.click("#tabInsightsBtn")
            mobile_page.wait_for_timeout(500)
            mobile_insights_path = SCREENSHOT_DIR / "mobile_insights.png"
            mobile_page.screenshot(path=str(mobile_insights_path))
            print(f"Saved: {mobile_insights_path}")

            browser.close()

        # Copy captured screenshots to Artifact Directory for markdown embedding
        if ARTIFACT_DIR.exists():
            for shot in SCREENSHOT_DIR.glob("*.png"):
                dest = ARTIFACT_DIR / shot.name
                shutil.copy2(shot, dest)
                print(f"Copied to artifact dir: {dest}")

    finally:
        server.shutdown()
        server.join()
        print("Flask test server cleanly shut down.")


if __name__ == "__main__":
    run_capture()
