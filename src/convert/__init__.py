"""
Convert Package - Enhanced Image Conversion with Floyd-Steinberg Dithering

Provides modular image conversion functionality for e-Paper displays with
6-color palette support and dithering algorithms. The package is organized
into separate modules for extensibility:

- core: Main conversion functions and image-to-BMP conversion
- dithering: Floyd-Steinberg dithering algorithm and color palette management
- preprocessing: Image preparation and resizing for e-Paper displays
- batch: Batch processing operations and comparison utilities

This module exposes the main public API for conversion operations.
"""

from .core import convert_image_to_6color_dithered
from .batch import convert_images_batch, convert_image_comparison
from .preprocessing import preprocess_image_for_epaper, resize_image_to_display
from .dithering import PALETTE_6COLOR, find_closest_palette_color, floyd_steinberg_dither

__all__ = [
    # Core conversion functions
    'convert_image_to_6color_dithered', 
    
    # Batch processing
    'convert_images_batch',
    'convert_image_comparison',
    
    # Preprocessing utilities
    'preprocess_image_for_epaper',
    'resize_image_to_display',
    
    # Dithering and palette
    'PALETTE_6COLOR',
    'find_closest_palette_color',
    'floyd_steinberg_dither'
]


if __name__ == "__main__":
    # Test conversion with comparison if run directly
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.convert <input_image> [output_dir]")
        print("  Creates both simple and dithered versions for comparison")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "comparison_output"
    
    print(f"Creating comparison conversions for: {input_file}")
    
    results = convert_image_comparison(input_file, output_dir)
    
    if results:
        print(f"✅ Conversion complete!")
        print(f"   Simple: {results['simple']}")
        print(f"   Dithered: {results['dithered']}")
        print(f"\\n💡 Compare the results:")
        print(f"   feh {results['simple']} {results['dithered']}")
    else:
        print("❌ Conversion failed")
        sys.exit(1)