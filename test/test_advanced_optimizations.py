"""
Test advanced optimizations including Numba JIT.
"""

import time
import sys
import os
from pathlib import Path
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test.advanced_optimizations import (
    pil_quantize_with_dithering,
    numba_conversion,
    optimized_imagemagick_with_dithering,
    hybrid_approach
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
    
    try:
        with open(output_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        file_size = Path(output_path).stat().st_size
    except:
        file_hash = "error"
        file_size = 0
    
    print(f"   ⏱️  Time: {duration:.3f}s")
    print(f"   🔒 Hash: {file_hash}...")
    
    return {'time': duration, 'hash': file_hash, 'size': file_size}


def main():
    """Test advanced optimizations."""
    input_image = "test/resources/test_image.png"
    baseline_time = 29.7
    
    # Get baseline hash
    baseline_path = "test/outputs/baseline/test_image_baseline.bmp"
    baseline_hash = None
    if Path(baseline_path).exists():
        with open(baseline_path, 'rb') as f:
            baseline_hash = hashlib.md5(f.read()).hexdigest()[:8]
    
    strategies = [
        ("PIL Quantize + Dithering", pil_quantize_with_dithering, "pil_dither.bmp"),
        ("Numba JIT Floyd-Steinberg", numba_conversion, "numba.bmp"),
        ("ImageMagick + Dithering", optimized_imagemagick_with_dithering, "im_dither.bmp"),
        ("Hybrid Approach", hybrid_approach, "hybrid.bmp"),
    ]
    
    print("="*60)
    print("🚀 ADVANCED OPTIMIZATION TEST")
    print("="*60)
    
    results = {}
    
    for name, func, output_file in strategies:
        output_path = f"test/outputs/advanced_{output_file}"
        result = time_conversion(func, input_image, output_path, name)
        
        if result:
            results[name] = result
            speedup = baseline_time / result['time']
            quality = "✅" if result['hash'] == baseline_hash else "🔄"
            
            print(f"   🚀 Speedup: {speedup:.1f}x")
            print(f"   {quality} Quality match")
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 ADVANCED RESULTS SUMMARY")
    print('='*60)
    
    if results:
        sorted_results = sorted(results.items(), key=lambda x: x[1]['time'])
        
        print(f"{'Strategy':<25} {'Time':<8} {'Speedup':<8} {'Quality'}")
        print("-" * 50)
        
        for name, result in sorted_results:
            speedup = baseline_time / result['time']
            quality = "✅" if result['hash'] == baseline_hash else "🔄"
            print(f"{name:<25} {result['time']:<8.3f} {speedup:<8.1f}x {quality}")


if __name__ == "__main__":
    main()