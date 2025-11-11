#!/bin/bash
# Run Playwright integration tests in the container

# Install dependencies
pip install -q -r /tests/requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the tests
cd /tests
pytest test_ui_e2e.py -v -s

echo "Integration tests completed. Check output above for specific failures."