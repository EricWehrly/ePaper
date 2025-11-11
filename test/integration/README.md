# Integration Tests

End-to-end browser tests for the ePaper web interface using Playwright.

## Setup

Tests run in an isolated Docker container using the official Playwright Python image.

```bash
## Running Tests

### Quick Start
```bash
# Run all integration tests (uses default entrypoint)
sudo docker compose -f docker-compose.playwright.yml run --rm integration-tests

# Or more explicitly
sudo docker compose -f docker-compose.playwright.yml run --rm integration-tests /scripts/run_playwright_tests.sh
```

### Alternative: Run with custom pytest options
```bash
sudo docker compose -f docker-compose.playwright.yml run --rm integration-tests \
  bash -c "pip install -r playwright/requirements.txt && \
           pytest playwright/test_ui_e2e.py -v --browser chromium"
```
```

## Test Philosophy

These tests verify **actual functionality and content**, not just DOM structure:
- ✅ Display image has a valid source AND is visible (not just exists)
- ✅ Thumbnails contain actual `<img>` elements with content (not just containers)
- ✅ No raw HTML/CSS rendered as text (catches template errors)
- ✅ Tab switching actually shows/hides correct content (not just structure)

**Key lesson**: Test what users see, not just what's in the DOM.
- Bad: "Does `#currentImage` exist?" 
- Good: "Does `#currentImage` have a valid src and is it visible?"

## Structure

## Architecture

- `docker-compose.playwright.yml` - Isolated test container configuration
- `test/playwright/test_ui_e2e.py` - E2E test suite
- `test/playwright/requirements.txt` - Python dependencies
- `scripts/run_playwright_tests.sh` - Test runner script

Tests connect to the main application via the `epaper_default` Docker network.
