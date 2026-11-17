import os
import time
from playwright.sync_api import sync_playwright

ASSETS_DIR = r"C:\Users\Admin\Downloads\vaani-ai\vaani-ai\reports\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Desktop 1440x900 - Dark Theme
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector("#controlsBar")
        time.sleep(0.5)
        
        # Send a rich message that triggers NER, Sentiment, Intent, Preprocessing
        query = "I am very happy today, my name is Yashvi and tomorrow I will visit Ahmedabad"
        page.fill("#text", query)
        page.click(".send")
        page.wait_for_selector(".msg.bot", timeout=12000)
        time.sleep(1)
        
        # Full app screenshot (Dark Theme)
        page.screenshot(path=os.path.join(ASSETS_DIR, "app_dark_theme_full.png"), full_page=True)
        print("Captured app_dark_theme_full.png")
        
        # Capture each of the 7 individual NLP cards
        page.locator("#cardLang").screenshot(path=os.path.join(ASSETS_DIR, "card1_lang_id.png"))
        page.locator("#cardPrep").screenshot(path=os.path.join(ASSETS_DIR, "card2_preprocessing.png"))
        page.locator("#cardSent").screenshot(path=os.path.join(ASSETS_DIR, "card3_sentiment.png"))
        page.locator("#cardIntent").screenshot(path=os.path.join(ASSETS_DIR, "card4_intent.png"))
        page.locator("#cardEntities").screenshot(path=os.path.join(ASSETS_DIR, "card5_ner.png"))
        page.locator("#cardLatency").screenshot(path=os.path.join(ASSETS_DIR, "card6_latency.png"))
        page.locator("#cardTrans").screenshot(path=os.path.join(ASSETS_DIR, "card7_translation.png"))
        print("Captured all 7 individual NLP pipeline cards!")
        
        # Switch to Light Theme
        page.click("#themeBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ASSETS_DIR, "app_light_theme_full.png"), full_page=True)
        print("Captured app_light_theme_full.png")
        
        page.close()
        
        # 2. Mobile Viewport (375x812)
        page = browser.new_page(viewport={"width": 375, "height": 812})
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector("#controlsBar")
        time.sleep(0.5)
        
        # Send a message on mobile
        page.fill("#text", "morning in Gujarati")
        page.click(".send")
        page.wait_for_selector(".msg.bot", timeout=10000)
        time.sleep(0.5)
        
        # Mobile Chat Dark
        page.screenshot(path=os.path.join(ASSETS_DIR, "mobile_chat_dark.png"))
        # Mobile Insights Dark
        page.click("#tabInsightsBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ASSETS_DIR, "mobile_insights_dark.png"))
        
        # Mobile Light
        page.click("#themeBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ASSETS_DIR, "mobile_insights_light.png"))
        page.click("#tabChatBtn")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ASSETS_DIR, "mobile_chat_light.png"))
        print("Captured mobile screenshots in Dark and Light themes!")
        
        page.close()
        browser.close()

if __name__ == "__main__":
    capture_all()
