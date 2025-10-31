"""
Performance tests for image conversion optimization.

Tests conversion speed and verifies output quality remains identical.
"""

import time
import numpy as np
from PIL import Image
from pathlib import Path
import hashlib
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.convert.core import convert_image_to_6color_dithered


class ConversionPerformanceTester:
    """Test harness for conversion performance optimization."""
    
    def __init__(self, test_images_dir="test/resources"):
        self.test_images_dir = Path(test_images_dir)
        self.baseline_outputs = {}
        self.baseline_times = {}
        
    def create_test_images(self):
        """Create test images of various sizes for performance testing."""
        test_dir = Path("test/resources")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test images of different sizes
        test_sizes = [
            (400, 600, "epaper_size"),      # Target ePaper resolution
            (800, 1200, "2x_size"),         # 2x resolution
            (1200, 1800, "3x_size"),        # 3x resolution
            (200, 300, "small_size"),       # Smaller than target
        ]
        
        for width, height, name in test_sizes:
            # Create a complex test image with gradients and patterns
            img = Image.new('RGB', (width, height))
            pixels = []
            
            for y in range(height):
                for x in range(width):
                    # Create a complex pattern for realistic testing
                    r = int(255 * (x / width))
                    g = int(255 * (y / height))
                    b = int(255 * ((x + y) / (width + height)))
                    
                    # Add some noise/variation
                    r = min(255, max(0, r + (x * y) % 50 - 25))
                    g = min(255, max(0, g + (x * 3) % 40 - 20))
                    b = min(255, max(0, b + (y * 2) % 30 - 15))
                    
                    pixels.append((r, g, b))
            
            img.putdata(pixels)
            img.save(test_dir / f"test_{name}.png")
            print(f"Created test image: {name} ({width}x{height})")
    
    def calculate_image_hash(self, image_path):
        """Calculate hash of image file for comparison."""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def time_conversion(self, input_path, output_path, iterations=3):
        """Time a conversion function multiple times and return average."""
        times = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            success = convert_image_to_6color_dithered(input_path, output_path)
            end_time = time.perf_counter()
            
            if not success:
                raise Exception(f"Conversion failed for {input_path}")
                
            times.append(end_time - start_time)
        
        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'times': times
        }
    
    def establish_baseline(self):
        """Run baseline tests and store results."""
        print("🏃 Establishing baseline performance...")
        
        test_images = list(self.test_images_dir.glob("test_*.png"))
        if not test_images:
            print("No test images found. Creating them...")
            self.create_test_images()
            test_images = list(self.test_images_dir.glob("test_*.png"))
        
        baseline_dir = Path("test/outputs/baseline")
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        for test_img in test_images:
            print(f"\n📊 Testing {test_img.name}...")
            output_path = baseline_dir / f"{test_img.stem}_baseline.bmp"
            
            # Time the conversion
            timing_results = self.time_conversion(test_img, output_path)
            
            # Store results
            image_hash = self.calculate_image_hash(output_path)
            
            self.baseline_times[test_img.name] = timing_results
            self.baseline_outputs[test_img.name] = {
                'hash': image_hash,
                'output_path': output_path,
                'size': output_path.stat().st_size
            }
            
            print(f"   ⏱️  Average time: {timing_results['avg_time']:.3f}s")
            print(f"   📏 Output size: {output_path.stat().st_size:,} bytes")
            print(f"   🔒 Hash: {image_hash[:8]}...")
    
    def test_optimized_version(self, optimized_function):
        """Test an optimized version against baseline."""
        print("\n🚀 Testing optimized version...")
        
        optimized_dir = Path("test/outputs/optimized")
        optimized_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for test_img_name, baseline_timing in self.baseline_times.items():
            test_img = self.test_images_dir / test_img_name
            output_path = optimized_dir / f"{test_img.stem}_optimized.bmp"
            
            print(f"\n📊 Testing optimized {test_img_name}...")
            
            # Time the optimized conversion
            start_time = time.perf_counter()
            success = optimized_function(test_img, output_path)
            end_time = time.perf_counter()
            
            if not success:
                print(f"❌ Optimized conversion failed for {test_img_name}")
                continue
            
            optimized_time = end_time - start_time
            baseline_time = baseline_timing['avg_time']
            
            # Check output quality
            optimized_hash = self.calculate_image_hash(output_path)
            baseline_hash = self.baseline_outputs[test_img_name]['hash']
            
            quality_match = optimized_hash == baseline_hash
            
            # Calculate performance improvement
            speedup = baseline_time / optimized_time if optimized_time > 0 else float('inf')
            
            results[test_img_name] = {
                'baseline_time': baseline_time,
                'optimized_time': optimized_time,
                'speedup': speedup,
                'quality_match': quality_match,
                'baseline_hash': baseline_hash[:8],
                'optimized_hash': optimized_hash[:8]
            }
            
            print(f"   ⏱️  Baseline: {baseline_time:.3f}s")
            print(f"   ⏱️  Optimized: {optimized_time:.3f}s")
            print(f"   🚀 Speedup: {speedup:.2f}x")
            print(f"   {'✅' if quality_match else '❌'} Quality match: {quality_match}")
        
        return results
    
    def print_summary(self, results):
        """Print performance summary."""
        print("\n" + "="*60)
        print("📈 PERFORMANCE SUMMARY")
        print("="*60)
        
        if not results:
            print("❌ No results to display")
            return
        
        total_baseline_time = sum(r['baseline_time'] for r in results.values())
        total_optimized_time = sum(r['optimized_time'] for r in results.values())
        overall_speedup = total_baseline_time / total_optimized_time
        
        quality_matches = sum(1 for r in results.values() if r['quality_match'])
        
        print(f"Overall speedup: {overall_speedup:.2f}x")
        print(f"Quality matches: {quality_matches}/{len(results)}")
        print(f"Total baseline time: {total_baseline_time:.3f}s")
        print(f"Total optimized time: {total_optimized_time:.3f}s")
        
        print("\nPer-image results:")
        for img_name, result in results.items():
            status = "✅" if result['quality_match'] else "❌"
            print(f"  {status} {img_name}: {result['speedup']:.2f}x speedup")


def main():
    """Run performance tests."""
    tester = ConversionPerformanceTester()
    
    # Create test images if they don't exist
    if not Path("test/resources").exists() or not list(Path("test/resources").glob("test_*.png")):
        tester.create_test_images()
    
    # Establish baseline
    tester.establish_baseline()
    
    print("\n✅ Baseline established. Now optimize the conversion function and run:")
    print("   python -c \"from test.test_conversion_performance import main; main()\"")


if __name__ == "__main__":
    main()