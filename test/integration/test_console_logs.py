"""
Test to capture browser console logs for debugging
"""
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_capture_console():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Capture all console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        
        # Navigate to page
        page.goto("http://epaper-display:5000")
        page.wait_for_timeout(3000)  # Wait for JS to execute
        
        # Print all console messages
        logger.info("\n" + "="*50)
        logger.info("BROWSER CONSOLE OUTPUT:")
        logger.info("="*50)
        for msg in console_messages:
            logger.info(msg)
        logger.info("="*50)
        
        # Check if thumbList has content
        thumb_list = page.locator("#thumbList")
        thumb_count = thumb_list.locator(".thumb").count()
        logger.info(f"\n✓ Thumb count: {thumb_count}")
        
        # Check if playlistList has content  
        playlist_list = page.locator("#playlistList")
        playlist_count = playlist_list.locator(".playlist-item").count()
        logger.info(f"✓ Playlist count: {playlist_count}")
        
        # Check active tab
        active_pane = page.locator(".tab-pane.active")
        logger.info(f"✓ Active pane: {active_pane.get_attribute('data-pane')}")
        
        # Get innerHTML of thumbList to see if it's empty
        thumb_html = thumb_list.inner_html()
        logger.info(f"\n✓ ThumbList innerHTML length: {len(thumb_html)}")
        if len(thumb_html) < 100:
            logger.info(f"  Content: {thumb_html}")
        
        browser.close()

if __name__ == "__main__":
    test_capture_console()
