import os
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\1073c6eb-ca8f-407b-a860-bdb36b691be4"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # 1. Desktop 1920px Viewport
        # -------------------------------------------------------------
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector("#controlsBar")
        time.sleep(0.5)

        # Capture After 1920px
        controls_el = page.locator("#controlsBar")
        controls_el.screenshot(path=os.path.join(ARTIFACT_DIR, "controls_after_1920.png"))
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "full_after_1920.png"))
        print("Captured 1920px controls_after_1920.png & full_after_1920.png")

        # Test Theme toggle
        page.click("#themeBtn")
        time.sleep(0.3)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "full_after_1920_light.png"))
        print("Tested Theme button (switched to Light theme)")
        page.click("#themeBtn") # switch back to dark
        time.sleep(0.3)

        # Test typing & Send
        page.fill("#text", "which date is tomorrow")
        page.click(".send")
        page.wait_for_selector(".msg.bot", timeout=10000)
        time.sleep(0.5)

        bot_msgs = page.locator(".msg.bot .bubble").all_text_contents()
        latest_reply = bot_msgs[-1] if bot_msgs else ""
        print(f"Sent 'which date is tomorrow' -> Received bot reply: '{latest_reply}'")
        assert "18 November 2026" in latest_reply
        assert "Wednesday" in latest_reply

        # Check NLP Insights panel updated
        assert page.locator("#cardIntent").is_visible()
        intent_text = page.locator("#cardIntent").inner_text()
        print(f"Card 4 Intent displayed: {intent_text.splitlines()[0] if intent_text else ''}")

        # Test New Chat button
        page.click("#resetChatBtn")
        time.sleep(0.5)
        remaining_bubbles = page.locator(".bubble").all_text_contents()
        print(f"Clicked New Chat -> Reset to {len(remaining_bubbles)} bubble(s)")

        # Test Checkbox toggles
        tts_cb = page.locator("#ttsOn")
        auto_cb = page.locator("#autoSendVoice")
        assert tts_cb.is_checked() is True
        tts_cb.uncheck()
        assert tts_cb.is_checked() is False
        tts_cb.check()
        assert tts_cb.is_checked() is True

        assert auto_cb.is_checked() is False
        auto_cb.check()
        assert auto_cb.is_checked() is True
        auto_cb.uncheck()
        assert auto_cb.is_checked() is False
        print("Checkboxes (Speak replies, Auto-send voice) clickable and state logic preserved.")

        page.close()

        # -------------------------------------------------------------
        # 2. Laptop 1024px Viewport
        # -------------------------------------------------------------
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector("#controlsBar")
        time.sleep(0.3)
        page.locator("#controlsBar").screenshot(path=os.path.join(ARTIFACT_DIR, "controls_after_1024.png"))
        print("Captured 1024px controls_after_1024.png")
        page.close()

        # -------------------------------------------------------------
        # 3. Tablet 768px Viewport
        # -------------------------------------------------------------
        page = browser.new_page(viewport={"width": 768, "height": 1024})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector("#controlsBar")
        time.sleep(0.3)
        page.locator("#controlsBar").screenshot(path=os.path.join(ARTIFACT_DIR, "controls_after_768.png"))
        print("Captured 768px controls_after_768.png")
        page.close()

        # -------------------------------------------------------------
        # 4. Mobile 375px Viewport
        # -------------------------------------------------------------
        page = browser.new_page(viewport={"width": 375, "height": 812})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector("#controlsBar")
        time.sleep(0.3)

        # Capture After 375px
        page.locator("#controlsBar").screenshot(path=os.path.join(ARTIFACT_DIR, "controls_after_375.png"))
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "full_after_375.png"))
        print("Captured 375px controls_after_375.png & full_after_375.png")

        # Test Mobile Tabs (Chat and NLP Insights)
        assert page.locator("#chatPanel").is_visible()
        page.click("#tabInsightsBtn")
        time.sleep(0.3)
        assert page.locator("#insights").is_visible()
        page.click("#tabChatBtn")
        time.sleep(0.3)
        assert page.locator("#chatPanel").is_visible()
        print("Mobile tabs (Chat & Insights) switching verified.")

        page.close()
        browser.close()
        print("All UI verifications and screenshots completed successfully!")

if __name__ == "__main__":
    verify()
