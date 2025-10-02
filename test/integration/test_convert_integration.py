#!/usr/bin/env python3
"""
Integration test for the image conversion module.

This test verifies end-to-end conversion functionality by:
1. Loading a test image from test resources
2. Converting it to 6-color BMP format
3. Saving the output for human verification

Run with: python -m pytest test/integration/test_convert_integration.py -v
Or directly: python test/integration/test_convert_integration.py
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

import convert
from PIL import Image


class TestConvertIntegration:
    """Integration tests for image conversion"""
    
    @classmethod
    def setup_class(cls):
        """Set up test resources"""
        cls.test_resources = project_root / 'test' / 'resources'
        cls.test_outputs = project_root / 'test' / 'outputs'
        cls.test_outputs.mkdir(exist_ok=True)
        
        cls.test_image_path = cls.test_resources / 'test_image.png'
        cls.output_bmp_path = cls.test_outputs / 'converted_test_image.bmp'
        
    def test_convert_image_to_6color_end_to_end(self):
        """
        Test complete image conversion pipeline.
        
        This test converts a real image and produces output for human verification.
        """
        # Ensure test image exists
        assert self.test_image_path.exists(), f"Test image not found: {self.test_image_path}"
        
        print(f"\\nConverting test image: {self.test_image_path}")
        print(f"Output will be saved to: {self.output_bmp_path}")
        
        # Perform conversion
        success = convert.convert_image_to_6color(
            str(self.test_image_path),
            str(self.output_bmp_path)
        )
        
        # Basic assertions
        assert success, "Conversion should return True on success"
        assert self.output_bmp_path.exists(), "Output BMP file should be created"
        
        # Verify output file properties
        with Image.open(self.output_bmp_path) as img:
            assert img.format == 'BMP', "Output should be BMP format"
            assert img.size == (400, 600), f"Output should be 400x600, got {img.size}"
            assert img.mode == 'RGB', f"Output should be RGB mode, got {img.mode}"
            
        # Get file sizes for information
        input_size = self.test_image_path.stat().st_size
        output_size = self.output_bmp_path.stat().st_size
        
        print(f"Input file size: {input_size:,} bytes")
        print(f"Output file size: {output_size:,} bytes")
        print(f"Output dimensions: {img.size}")
        print(f"\\n✅ Conversion successful! Check the output file:")
        print(f"   {self.output_bmp_path}")
        print(f"\\n💡 To view the converted image:")
        print(f"   feh {self.output_bmp_path}")
        print(f"   # or")
        print(f"   xdg-open {self.output_bmp_path}")
        
    def test_dithering_quality_check(self):
        """Verify that the converted image uses Floyd-Steinberg dithering effectively"""
        # Convert the test image
        success = convert.convert_image_to_6color(
            str(self.test_image_path),
            str(self.output_bmp_path)
        )
        
        assert success, "Conversion should succeed"
        
        # Load the converted image and check colors
        with Image.open(self.output_bmp_path) as img:
            # Get all unique colors in the image
            colors = set(img.getdata())
            
            # Convert palette colors to RGB tuples for comparison  
            palette_rgb = set()
            for color in convert.PALETTE_6COLOR:
                palette_rgb.add(tuple(color.astype('uint8')))
                
            print(f"\\nDithered image uses {len(colors)} of 6 available colors")
            print("Color usage:")
            color_names = ['BLACK', 'WHITE', 'YELLOW', 'RED', 'BLUE', 'GREEN']
            for i, (name, color) in enumerate(zip(color_names, convert.PALETTE_6COLOR)):
                rgb_tuple = tuple(color.astype('uint8'))
                used = "✓" if rgb_tuple in colors else " "
                print(f"  {used} {name}: {rgb_tuple}")
                
            # With Floyd-Steinberg dithering, we expect to use multiple colors
            assert len(colors) >= 3, f"Dithering should use multiple colors, only found {len(colors)}"
            
            print(f"\\n✅ Floyd-Steinberg dithering appears to be working - using {len(colors)} colors")


def main():
    """Run integration test directly"""
    import logging
    
    # Set up logging for the test
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    print("=" * 60)
    print("ePaper Convert Integration Test")
    print("=" * 60)
    
    # Create test instance and run
    test = TestConvertIntegration()
    test.setup_class()
    
    try:
        print("\\n🧪 Running end-to-end conversion test...")
        test.test_convert_image_to_6color_end_to_end()
        
        print("\\n🧪 Running Floyd-Steinberg dithering quality check...")
        test.test_dithering_quality_check()
        
        print("\\n" + "=" * 60)
        print("🎉 All integration tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
