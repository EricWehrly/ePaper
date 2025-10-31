#!/usr/bin/env python3
"""Test GPIO 24 specifically to see if it has edge detection issues"""

print("Testing GPIO 24 (BUSY_PIN) edge detection...")

try:
    import gpiozero
    print("Creating Button on GPIO 24...")
    button = gpiozero.Button(24, pull_up=False)
    print("✅ GPIO 24 Button created successfully!")
    button.close()
except Exception as e:
    print(f"❌ GPIO 24 Button failed: {e}")
    
    # Try alternative approach without edge detection
    print("\nTrying alternative approach (LED instead of Button)...")
    try:
        import gpiozero
        # Use LED for input reading instead of Button
        led = gpiozero.LED(24)
        print("✅ GPIO 24 as LED works (can be used for digital read)")
        led.close()
    except Exception as e2:
        print(f"❌ GPIO 24 as LED also failed: {e2}")

print("\nTest complete!")