# ePaper Display Project

## Overview
A minimal Python project to display images on a Waveshare 4-inch e-Paper HAT+ (E) using Raspberry Pi.

## Hardware Specifications
- **Device**: Waveshare 4-inch e-Paper HAT+ (E)
- **Resolution**: 400 x 600 pixels
- **Colors**: 6-color palette (BLACK, WHITE, YELLOW, RED, BLUE, GREEN)
- **Platform**: Raspberry Pi

## Project Structure
```
/home/eric/Projects/ePaper/
├── lib/waveshare_epd/     # Waveshare library
│   └── epd4in0e.py       # Device driver
├── pic/                  # BMP images for display
├── pic-raw/              # Source images (PNG, JPEG)
└── src/                  # Python scripts
    └── epd_4in0e_test.py # Reference example
```

## Core Requirements
1. **Image Loading**: Load PNG/JPEG images from `pic-raw/` folder
2. **Image Processing**: 
   - Convert to 400x600 resolution
   - Apply 6-color palette (BLACK, WHITE, YELLOW, RED, BLUE, GREEN)
   - Save as BMP in `pic/` folder
3. **Display Cycling**: Automatically cycle through BMP images and display on e-paper

## Key Implementation Notes
- Use existing `waveshare_epd.epd4in0e` library
- Color constants: `epd.BLACK`, `epd.WHITE`, `epd.YELLOW`, `epd.RED`, `epd.BLUE`, `epd.GREEN`
- Device resolution: `epd.width` (400) x `epd.height` (600)
- Always call `epd.sleep()` when finished to preserve display

## Code Style
- Keep functions simple and focused
- Use clear variable names
- **Minimal logging**: Only log errors, warnings, and major workflow steps
- Handle exceptions gracefully
- Avoid cluttering code with debug/info logs for routine operations

## Logging Guidelines
- **ERROR**: For failures that prevent operation
- **WARNING**: For recoverable issues or missing resources
- **INFO**: Only for major workflow milestones (startup, conversion batches, shutdown)
- **DEBUG**: Avoid unless specifically debugging
- **No logging for**: Successful routine operations, file I/O, basic function entry/exit
