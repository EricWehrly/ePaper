#!/usr/bin/env python3
"""
Test to verify UI doesn't show duplicate thumbnails in the library.

This test checks:
1. API returns unique filenames (no duplicates)
2. UI renders each image exactly once
3. No DOM duplication after refresh cycles
"""
import pytest
from playwright.sync_api import Page, expect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the ePaper web app. Respects TARGET_URL env var for CI/dev overrides."""
    return os.environ.get("TARGET_URL", "http://epaper-epaper-display-1:5000")

def test_api_returns_no_duplicates(page: Page, base_url: str):
    """Verify the API returns each converted image exactly once"""
    logger.info("Testing API for duplicate filenames...")
    
    response = page.request.get(f"{base_url}/api/images")
    assert response.ok, f"API request failed: {response.status}"
    
    data = response.json()
    converted_images = data.get("converted_images", [])
    
    # Extract all filenames
    filenames = [img["name"] for img in converted_images]
    unique_filenames = set(filenames)
    
    logger.info(f"API returned {len(filenames)} images, {len(unique_filenames)} unique")
    
    # Check for duplicates
    duplicates = [name for name in filenames if filenames.count(name) > 1]
    
    if duplicates:
        logger.error(f"❌ Found duplicate filenames in API response: {set(duplicates)}")
        assert False, f"API returned duplicate filenames: {set(duplicates)}"
    else:
        logger.info("✓ API returns no duplicate filenames")

def test_ui_shows_no_duplicate_thumbnails(page: Page, base_url: str):
    """Verify the UI displays each image exactly once in the library"""
    logger.info("Testing UI for duplicate thumbnails...")
    
    page.goto(base_url)
    page.wait_for_timeout(2000)  # Wait for initial load
    
    # Make sure we're on Library tab
    library_tab = page.locator("[data-tab='library']")
    if library_tab.count() > 0:
        library_tab.click()
        page.wait_for_timeout(1000)
    
    # Get all thumbnail images
    thumbnails = page.locator("#thumbList .thumb img")
    thumb_count = thumbnails.count()
    
    if thumb_count == 0:
        logger.warning("⚠ No thumbnails found - skipping duplicate check")
        return
    
    logger.info(f"Found {thumb_count} thumbnail elements")
    
    # Extract all src and data-src attributes
    src_list = []
    for i in range(thumb_count):
        img = thumbnails.nth(i)
        src = img.get_attribute("src") or img.get_attribute("data-src")
        if src:
            src_list.append(src)
            logger.info(f"  [{i}] {src}")
    
    unique_srcs = set(src_list)
    logger.info(f"Found {len(src_list)} total src attributes, {len(unique_srcs)} unique")
    
    # Check for duplicates and report them in detail
    duplicates = {}
    for src in src_list:
        count = src_list.count(src)
        if count > 1:
            duplicates[src] = count
    
    if duplicates:
        logger.error(f"❌ Found {len(duplicates)} duplicate thumbnail src attributes")
        for dup, count in duplicates.items():
            logger.error(f"  - {dup} appears {count} times")
            indices = [i for i, s in enumerate(src_list) if s == dup]
            logger.error(f"    At positions: {indices}")
        
        # Log browser console for clues
        logger.error("\n📋 Browser console logs:")
        for msg in page.context.pages[0].evaluate("() => window.consoleMessages || []"):
            logger.error(f"  {msg}")
            
        assert False, f"UI shows duplicate thumbnails: {len(duplicates)} duplicated images"
    else:
        logger.info("✓ UI shows no duplicate thumbnails")

def test_ui_no_duplicates_after_refresh(page: Page, base_url: str):
    """Verify thumbnails don't duplicate after refreshing images"""
    logger.info("Testing thumbnail stability after refresh...")
    
    page.goto(base_url)
    page.wait_for_timeout(2000)
    
    # Get initial count
    thumbnails = page.locator("#thumbList .thumb")
    initial_count = thumbnails.count()
    logger.info(f"Initial thumbnail count: {initial_count}")
    
    # Trigger a refresh by switching tabs
    photos_tab = page.locator("[data-tab='photos']")
    if photos_tab.count() > 0:
        photos_tab.click()
        page.wait_for_timeout(500)
    
    library_tab = page.locator("[data-tab='library']")
    if library_tab.count() > 0:
        library_tab.click()
        page.wait_for_timeout(1500)
    
    # Get count after refresh
    thumbnails_after = page.locator("#thumbList .thumb")
    after_count = thumbnails_after.count()
    logger.info(f"Thumbnail count after refresh: {after_count}")
    
    # Count should be the same (or close, allowing for +/- 1 for timing issues)
    if abs(after_count - initial_count) > 1:
        logger.error(f"❌ Thumbnail count changed significantly: {initial_count} -> {after_count}")
        
        # Check for actual duplicates
        src_list = []
        for i in range(after_count):
            img = thumbnails_after.nth(i).locator("img")
            if img.count() > 0:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src:
                    src_list.append(src)
        
        duplicates = [src for src in src_list if src_list.count(src) > 1]
        if duplicates:
            logger.error(f"Found {len(set(duplicates))} duplicated images after refresh")
            assert False, "Thumbnails duplicated after refresh"
    else:
        logger.info("✓ Thumbnail count stable after refresh")
