#!/usr/bin/env python3
"""Basic GPIO test without edge detection to check if GPIO access is working"""

import sys
import os

# Add lib directory to path for waveshare library
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

print("Testing GPIO access...")

# Test 1: Try RPi.GPIO directly
print("\n1. Testing RPi.GPIO...")
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)  # Use a safe pin for output test
    GPIO.output(18, GPIO.HIGH)
    GPIO.output(18, GPIO.LOW)
    GPIO.cleanup()
    print("✅ RPi.GPIO basic test passed")
except Exception as e:
    print(f"❌ RPi.GPIO failed: {e}")

# Test 2: Try gpiozero without edge detection
print("\n2. Testing gpiozero without edge detection...")
try:
    import gpiozero
    # Try a simple LED instead of Button (no edge detection needed)
    led = gpiozero.LED(18)
    led.on()
    led.off()
    led.close()
    print("✅ gpiozero basic test passed")
except Exception as e:
    print(f"❌ gpiozero failed: {e}")

# Test 3: Try SPI access
print("\n3. Testing SPI access...")
try:
    import spidev
    spi = spidev.SpiDev()
    spi.open(0, 0)  # Bus 0, Device 0
    spi.close()
    print("✅ SPI access test passed")
except Exception as e:
    print(f"❌ SPI access failed: {e}")

print("\nBasic GPIO tests complete!")