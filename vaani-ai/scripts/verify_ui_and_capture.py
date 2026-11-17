import os
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\1073c6eb-ca8f-407b-a860-bdb36b691be4"

def run_verification():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Desktop Viewport (1440 x 900) - Dark Theme
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector(".composer")
        
        # Verify no file input / paperclip
        file_inputs = page.query_selector_all("input[type='file']")
        uploads = page.query_selector_all(".upload")
        print(f"File inputs found: {len(file_inputs)} (expected 0)")
        print(f".upload elements found: {len(uploads)} (expected 0)")
        assert len(file_inputs) == 0, "File input exists!"
        assert len(uploads) == 0, "Upload element exists!"
        
        # Dark desktop initial
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "desktop_1440_dark.png"), full_page=True)
        print("Captured desktop_1440_dark.png")
        
        # Send message "morning in Gujarati"
        page.fill("#text", "morning in Gujarati")
        page.click(".send")
        
        # Wait for bot response
        page.wait_for_selector(".msg.bot", timeout=15000)
        time.sleep(1) # wait for DOM render
        
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "desktop_1440_dark_replied.png"), full_page=True)
        print("Captured desktop_1440_dark_replied.png")
        
        # Toggle to Light Theme
        page.click("#themeBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "desktop_1440_light_replied.png"), full_page=True)
        print("Captured desktop_1440_light_replied.png")
        page.close()
        
        # 2. Laptop Viewport (1024 x 768) - Light & Dark
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector(".composer")
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "laptop_1024_dark.png"), full_page=True)
        print("Captured laptop_1024_dark.png")
        page.click("#themeBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "laptop_1024_light.png"), full_page=True)
        print("Captured laptop_1024_light.png")
        page.close()
        
        # 3. Mobile Viewport (375 x 812) - iPhone size
        page = browser.new_page(viewport={"width": 375, "height": 812})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector(".composer")
        
        # Verify touch targets
        mic_box = page.locator("#micBtn").bounding_box()
        send_box = page.locator(".send").bounding_box()
        print(f"Mobile micBtn height: {mic_box['height']}, width: {mic_box['width']} (min 44px)")
        print(f"Mobile send height: {send_box['height']}, width: {send_box['width']} (min 44px)")
        assert mic_box['height'] >= 43.5 and mic_box['width'] >= 43.5
        assert send_box['height'] >= 43.5 and send_box['width'] >= 43.5
        
        # Mobile chat tab
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_375_chat_dark.png"))
        print("Captured mobile_375_chat_dark.png")
        
        # Switch to Insights tab
        page.click("#tabInsightsBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_375_insights_dark.png"))
        print("Captured mobile_375_insights_dark.png")
        
        # Switch to Light theme on mobile
        page.click("#themeBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_375_insights_light.png"))
        print("Captured mobile_375_insights_light.png")
        
        page.close()
        browser.close()
        print("All UI verifications and screenshots captured successfully!")

if __name__ == "__main__":
    run_verification()
