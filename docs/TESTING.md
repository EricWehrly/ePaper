# Testing Guide

Quick reference for running tests in the ePaper project.

## Integration Tests (Playwright)

End-to-end browser tests for the web interface.

```bash
# Run all integration tests
docker compose -f docker-compose.playwright.yml run --rm integration-tests
```

**What it tests**: Page loading, tab switching, display functionality, thumbnails, Google Photos integration, console errors.

**Details**: See [test/integration/README.md](../test/integration/README.md)

---

## Unit Tests (pytest)

Python unit tests for backend functionality.

```bash
# Using epaper-dev service (mounts full workspace including tests)
docker compose run --rm epaper-dev pytest -q

# Run specific test file
docker compose run --rm epaper-dev pytest test/test_settings.py -v

# Run with custom options
docker compose run --rm epaper-dev pytest -k "test_name" -v
```

**What it tests**: Settings management, conversion logic, display manager, path utilities.

**Note**: Tests that import hardware libraries (GPIO/SPI) will show import warnings but continue. Integration tests (Playwright) are excluded from this command as they need their own environment.

---

## Common Issues

### "No tests ran" / Exit code 5
- The `epaper-display` service doesn't mount the test directory
- Use `epaper-dev` service instead: `docker compose run --rm epaper-dev pytest -q`

### GPIO/Hardware Import Errors
- Expected when running without Raspberry Pi hardware
- Tests continue despite warnings
- Use `PIGPIO_ADDR` environment variable to mock hardware if needed

### Integration Tests Hanging
- Ensure main application is running: `docker compose up -d epaper-display`
- Integration tests connect to the app via Docker network
- Check logs: `docker compose logs epaper-display`

---

## Quick Commands Summary

```bash
# Integration tests (Playwright - E2E)
docker compose -f docker-compose.playwright.yml run --rm integration-tests

# Unit tests (pytest - backend)
docker compose run --rm epaper-dev pytest -q
```
