#!/usr/bin/env python3
"""
Basic E2E test to identify specific UI issues in the ePaper web interface.
This test will help us document what's broken and verify fixes.
"""
import pytest
from playwright.sync_api import Page, expect
import time
import logging

# Configure logging to see test progress
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the ePaper web app"""
    return "http://epaper-epaper-display-1:5000"

def test_page_loads(page: Page, base_url: str):
    """Verify the basic page loads and contains expected structure"""
    logger.info("Testing page load...")
    page.goto(base_url)
    
    # Wait for page to load - just check body is visible
    expect(page.locator("body")).to_be_visible()
    
    # Get the actual title for logging
    title = page.title()
    logger.info(f"✓ Page loads successfully with title: '{title}'")
    
    # Basic sanity check - page has content
    assert title is not None, "Page should have a title"

def test_dead_simple_tabs_present(page: Page, base_url: str):
    """Verify the dead simple tabs are inserted by JavaScript"""
    logger.info("Testing tab structure...")
    page.goto(base_url)
    
    # Wait a moment for JS to execute
    page.wait_for_timeout(2000)
    
    # Check for tab navigation
    tabs_nav = page.locator(".tab-nav")
    if tabs_nav.count() > 0:
        expect(tabs_nav).to_be_visible()
        logger.info("✓ Tab navigation found")
        
        # Check for individual tabs
        library_tab = page.locator("[data-tab='library']")
        photos_tab = page.locator("[data-tab='photos']")
        controls_tab = page.locator("[data-tab='controls']")
        
        expect(library_tab).to_be_visible()
        expect(photos_tab).to_be_visible() 
        expect(controls_tab).to_be_visible()
        logger.info("✓ All three tabs present")
    else:
        logger.warning("✗ Tab navigation not found - dead_simple_tabs.js may not have executed")

def test_display_section_present(page: Page, base_url: str):
    """Check if display section exists and is properly positioned"""
    logger.info("Testing display section...")
    page.goto(base_url)
    page.wait_for_timeout(2000)
    
    display_section = page.locator(".display-section")
    if display_section.count() > 0:
        expect(display_section).to_be_visible()
        logger.info("✓ Display section found and visible")
        
        # Check for display image
        current_image = page.locator("#currentImage")
        if current_image.count() > 0:
            logger.info("✓ Current image element found")
            # Check if it has a src attribute
            src = current_image.get_attribute("src")
            if src and src != "":
                logger.info(f"✓ Display image has source: {src}")
            else:
                logger.warning("✗ Display image has no source")
        else:
            logger.warning("✗ #currentImage element not found")
    else:
        logger.warning("✗ Display section not found")

def test_tab_switching_behavior(page: Page, base_url: str):
    """Test if clicking tabs actually switches content"""
    logger.info("Testing tab switching...")
    page.goto(base_url)
    page.wait_for_timeout(2000)
    
    # Try clicking on Photos tab
    photos_tab = page.locator("[data-tab='photos']")
    if photos_tab.count() > 0:
        photos_tab.click()
        page.wait_for_timeout(500)
        
        # Check if Photos pane is now visible
        photos_pane = page.locator(".tab-pane[data-tab='photos']")
        if photos_pane.count() > 0 and photos_pane.is_visible():
            logger.info("✓ Photos tab click shows Photos pane")
        else:
            logger.warning("✗ Photos tab click did not show Photos pane")
            
        # Try clicking on Controls tab
        controls_tab = page.locator("[data-tab='controls']")
        if controls_tab.count() > 0:
            controls_tab.click()
            page.wait_for_timeout(500)
            
            controls_pane = page.locator(".tab-pane[data-tab='controls']")
            if controls_pane.count() > 0 and controls_pane.is_visible():
                logger.info("✓ Controls tab click shows Controls pane")
            else:
                logger.warning("✗ Controls tab click did not show Controls pane")
        
        # Click back to Library tab
        library_tab = page.locator("[data-tab='library']")
        if library_tab.count() > 0:
            library_tab.click()
            page.wait_for_timeout(500)
            
            library_pane = page.locator(".tab-pane[data-tab='library']")
            if library_pane.count() > 0 and library_pane.is_visible():
                logger.info("✓ Library tab click shows Library pane")
            else:
                logger.warning("✗ Library tab click did not show Library pane")
    else:
        logger.warning("✗ No tabs found for switching test")

def test_google_photos_in_photos_tab(page: Page, base_url: str):
    """Check if Google Photos content appears in Photos tab"""
    logger.info("Testing Google Photos placement...")
    page.goto(base_url)
    page.wait_for_timeout(2000)
    
    # Click Photos tab
    photos_tab = page.locator("[data-tab='photos']")
    if photos_tab.count() > 0:
        photos_tab.click()
        page.wait_for_timeout(500)
        
        # Look for Google Photos container in Photos pane
        photos_pane = page.locator(".tab-pane[data-tab='photos']")
        if photos_pane.count() > 0:
            google_photos = photos_pane.locator(".google-photos-container")
            if google_photos.count() > 0:
                logger.info("✓ Google Photos container found in Photos pane")
                
                # Check if it's collapsed/hidden
                if google_photos.is_visible():
                    logger.info("✓ Google Photos container is visible")
                else:
                    logger.warning("✗ Google Photos container is hidden/collapsed")
            else:
                logger.warning("✗ Google Photos container not found in Photos pane")
        else:
            logger.warning("✗ Photos pane not found")
    else:
        logger.warning("✗ Photos tab not found")

def test_library_thumbnails_load(page: Page, base_url: str):
    """Check if library thumbnails are loading (or at least attempting to)"""
    logger.info("Testing library thumbnails...")
    page.goto(base_url)
    page.wait_for_timeout(3000)  # Give more time for thumbnail loading
    
    # Should be on Library tab by default, but click to be sure
    library_tab = page.locator("[data-tab='library']")
    if library_tab.count() > 0:
        library_tab.click()
        page.wait_for_timeout(1000)
    
    # Look for thumbnail elements
    thumbnails = page.locator(".thumbnail, .library-item, .image-thumbnail")
    thumb_count = thumbnails.count()
    
    if thumb_count > 0:
        logger.info(f"✓ Found {thumb_count} thumbnail elements")
        
        # Check if any have actual images
        images_with_src = 0
        for i in range(min(5, thumb_count)):  # Check first 5
            thumb = thumbnails.nth(i)
            img = thumb.locator("img")
            if img.count() > 0:
                src = img.get_attribute("src")
                if src and src != "":
                    images_with_src += 1
        
        if images_with_src > 0:
            logger.info(f"✓ {images_with_src} thumbnails have image sources")
        else:
            logger.warning("✗ No thumbnails have image sources")
    else:
        logger.warning("✗ No thumbnail elements found")

def test_console_errors(page: Page, base_url: str):
    """Capture and report JavaScript console errors"""
    logger.info("Monitoring console errors...")
    
    console_messages = []
    
    def handle_console(msg):
        console_messages.append(f"{msg.type}: {msg.text}")
    
    page.on("console", handle_console)
    
    page.goto(base_url)
    page.wait_for_timeout(3000)
    
    # Click through tabs to trigger any errors
    for tab_name in ['photos', 'controls', 'library']:
        tab = page.locator(f"[data-tab='{tab_name}']")
        if tab.count() > 0:
            tab.click()
            page.wait_for_timeout(500)
    
    # Report console messages
    errors = [msg for msg in console_messages if 'error' in msg.lower()]
    warnings = [msg for msg in console_messages if 'warn' in msg.lower()]
    
    if errors:
        logger.warning(f"✗ Found {len(errors)} console errors:")
        for error in errors[:5]:  # Limit to first 5
            logger.warning(f"  {error}")
    else:
        logger.info("✓ No console errors detected")
        
    if warnings:
        logger.info(f"Found {len(warnings)} console warnings (non-critical)")

def test_no_raw_html_css_visible(page: Page, base_url: str):
    """Check that no raw HTML/CSS code is visible as text on the page"""
    logger.info("Testing for visible raw HTML/CSS code...")
    page.goto(base_url)
    page.wait_for_timeout(2000)
    
    # Get the visible text content of the entire page
    body_text = page.locator("body").inner_text()
    
    # Look for telltale signs of raw HTML/CSS being rendered as text
    html_indicators = [
        "background: white;",
        "border: 1px solid",
        "padding: 14px",
        "border-radius:",
        "data-tab=",
        "<button",
        "<div",
        'style="',
    ]
    
    found_issues = []
    for indicator in html_indicators:
        if indicator in body_text:
            found_issues.append(indicator)
            logger.warning(f"✗ Found raw HTML/CSS in visible text: '{indicator}'")
    
    if found_issues:
        # Get a snippet of the problematic text
        snippet_start = body_text.find(found_issues[0])
        snippet = body_text[max(0, snippet_start-50):min(len(body_text), snippet_start+200)]
        logger.error(f"Context around error: ...{snippet}...")
        assert False, f"Raw HTML/CSS visible on page! Found: {', '.join(found_issues[:3])}"
    else:
        logger.info("✓ No raw HTML/CSS visible as text")

def test_display_and_thumbs_have_content(page: Page, base_url: str):
    """Verify that Display section and Thumbs section actually have content"""
    logger.info("Testing for actual content in Display and Thumbs sections...")
    page.goto(base_url)
    page.wait_for_timeout(3000)  # Give time for content to load
    
    # Check Display section has an image element with src
    display_img = page.locator("#currentImage")
    if display_img.count() > 0:
        src = display_img.get_attribute("src")
        is_visible = display_img.is_visible()
        if src and src != "" and is_visible:
            logger.info(f"✓ Display image present with src: {src[:50]}...")
        else:
            logger.warning(f"✗ Display image exists but src='{src}' visible={is_visible}")
            assert False, "Display image element exists but has no source or is not visible"
    else:
        logger.error("✗ #currentImage element not found")
        assert False, "Display image element (#currentImage) not found in DOM"
    
    # Check Thumbs section has actual thumbnail elements
    thumb_list = page.locator("#thumbList, .thumb-list")
    if thumb_list.count() > 0:
        # Look for actual thumbnail/image elements inside
        thumbs = thumb_list.locator("img, .thumbnail, .library-item")
        thumb_count = thumbs.count()
        
        if thumb_count > 0:
            logger.info(f"✓ Found {thumb_count} thumbnail elements")
        else:
            logger.error("✗ Thumb list exists but has NO thumbnail elements inside")
            # Get the actual HTML to see what's there
            html = thumb_list.inner_html()
            logger.error(f"Thumb list HTML (first 200 chars): {html[:200]}")
            assert False, "Thumbs section exists but contains no actual thumbnails"
    else:
        logger.error("✗ Thumb list container not found")
        assert False, "Thumb list container (#thumbList or .thumb-list) not found"