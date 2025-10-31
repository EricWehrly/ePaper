"""
Test radical optimization strategies for massive performance gains.
"""

import time
import sys
import os
from pathlib import Path
import hashlib

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test.radical_optimizations import (
    simple_nearest_color_conversion,
    ordered_dither_conversion, 
    imagemagick_conversion,
    pil_quantize_conversion,
    lookup_table_conversion
)


def time_conversion(conversion_func, input_path, output_path, name):
    """Time a conversion and return results."""
    print(f"\n🚀 Testing {name}...")
    
    start_time = time.perf_counter()
    success = conversion_func(input_path, output_path)
    end_time = time.perf_counter()
    
    if not success:
        print(f"❌ {name} failed")
        return None
    
    duration = end_time - start_time
    
    # Calculate file hash for quality comparison
    try:
        with open(output_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
    except:
        file_hash = "error"
    
    # Get file size
    try:
        file_size = Path(output_path).stat().st_size
    except:
        file_size = 0
    
    print(f"   ⏱️  Time: {duration:.3f}s")
    print(f"   🔒 Hash: {file_hash}...")
    print(f"   📏 Size: {file_size:,} bytes")
    
    return {
        'time': duration,
        'hash': file_hash,
        'size': file_size,
        'success': success
    }


def main():
    """Test all radical optimizations."""
    input_image = "test/resources/test_image.png"
    
    if not Path(input_image).exists():
        print("❌ Test image not found. Run test_conversion_performance.py first.")
        return
    
    # Get baseline for comparison
    baseline_path = "test/outputs/baseline/test_image_baseline.bmp"
    baseline_hash = None
    if Path(baseline_path).exists():
        with open(baseline_path, 'rb') as f:
            baseline_hash = hashlib.md5(f.read()).hexdigest()[:8]
        print(f"📊 Baseline hash: {baseline_hash}...")
    
    strategies = [
        ("Simple Nearest Color", simple_nearest_color_conversion, "simple.bmp"),
        ("Ordered (Bayer) Dithering", ordered_dither_conversion, "ordered.bmp"),
        ("ImageMagick CLI", imagemagick_conversion, "imagemagick.bmp"),
        ("PIL Quantize", pil_quantize_conversion, "pil_quantize.bmp"),
        ("Lookup Table", lookup_table_conversion, "lookup.bmp"),
    ]
    
    results = {}
    baseline_time = 29.7  # From our previous testing
    
    print("="*60)
    print("🚀 RADICAL PERFORMANCE OPTIMIZATION TEST")
    print("="*60)
    print(f"Baseline time: {baseline_time:.3f}s")
    
    for name, func, output_file in strategies:
        output_path = f"test/outputs/radical_{output_file}"
        result = time_conversion(func, input_image, output_path, name)
        
        if result:
            results[name] = result
            speedup = baseline_time / result['time']
            quality_match = "✅" if result['hash'] == baseline_hash else "🔄" if baseline_hash else "❓"
            
            print(f"   🚀 Speedup: {speedup:.1f}x")
            print(f"   {quality_match} Quality vs baseline")
    
    # Summary
    print("\n" + "="*60)  
    print("📈 PERFORMANCE SUMMARY")
    print("="*60)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['time'])
    
    print(f"{'Strategy':<25} {'Time':<8} {'Speedup':<8} {'Quality'}")
    print("-" * 50)
    
    for name, result in sorted_results:
        speedup = baseline_time / result['time']
        quality = "✅" if result['hash'] == baseline_hash else "🔄"
        print(f"{name:<25} {result['time']:<8.3f} {speedup:<8.1f}x {quality}")
    
    # Find fastest
    if sorted_results:
        fastest_name, fastest_result = sorted_results[0]
        fastest_speedup = baseline_time / fastest_result['time']
        
        print(f"\n🏆 WINNER: {fastest_name}")
        print(f"   Time: {fastest_result['time']:.3f}s ({fastest_speedup:.1f}x faster)")
        print(f"   Quality: {'Same' if fastest_result['hash'] == baseline_hash else 'Different'}")


if __name__ == "__main__":
    main()