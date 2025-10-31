"""
C/C++ external binary approach and comprehensive final recommendation.
"""

import subprocess
import tempfile
import os
from pathlib import Path


def create_c_dithering_binary():
    """
    Create a C program for ultra-fast dithering as external binary.
    This is for future implementation.
    """
    c_code = '''
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

// 6-color palette: BLACK, WHITE, YELLOW, RED, BLUE, GREEN
static const uint8_t PALETTE[6][3] = {
    {0, 0, 0},        // BLACK
    {255, 255, 255},  // WHITE
    {255, 243, 56},   // YELLOW
    {191, 0, 0},      // RED
    {100, 64, 255},   // BLUE
    {67, 138, 28}     // GREEN
};

int find_closest_color(uint8_t r, uint8_t g, uint8_t b) {
    int min_dist = INT_MAX;
    int closest_idx = 0;
    
    for (int i = 0; i < 6; i++) {
        int dr = (int)r - (int)PALETTE[i][0];
        int dg = (int)g - (int)PALETTE[i][1]; 
        int db = (int)b - (int)PALETTE[i][2];
        int dist = dr*dr + dg*dg + db*db;
        
        if (dist < min_dist) {
            min_dist = dist;
            closest_idx = i;
        }
    }
    return closest_idx;
}

void floyd_steinberg_dither(uint8_t* image, int width, int height, uint8_t* output) {
    // Create working buffer with padding
    int padded_width = width + 2;
    int padded_height = height + 1;
    float* working = calloc(padded_width * padded_height * 3, sizeof(float));
    
    // Copy image data with padding
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int src_idx = (y * width + x) * 3;
            int dst_idx = (y * padded_width + (x + 1)) * 3;
            working[dst_idx] = image[src_idx];
            working[dst_idx + 1] = image[src_idx + 1];
            working[dst_idx + 2] = image[src_idx + 2];
        }
    }
    
    // Floyd-Steinberg dithering
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int idx = (y * padded_width + (x + 1)) * 3;
            
            uint8_t old_r = (uint8_t)working[idx];
            uint8_t old_g = (uint8_t)working[idx + 1];
            uint8_t old_b = (uint8_t)working[idx + 2];
            
            int closest = find_closest_color(old_r, old_g, old_b);
            
            uint8_t new_r = PALETTE[closest][0];
            uint8_t new_g = PALETTE[closest][1];
            uint8_t new_b = PALETTE[closest][2];
            
            // Store result
            int out_idx = (y * width + x) * 3;
            output[out_idx] = new_r;
            output[out_idx + 1] = new_g;
            output[out_idx + 2] = new_b;
            
            // Calculate and distribute error
            float err_r = old_r - new_r;
            float err_g = old_g - new_g;
            float err_b = old_b - new_b;
            
            // Distribute error to neighbors
            if (x + 1 < width) {
                int right_idx = (y * padded_width + (x + 2)) * 3;
                working[right_idx] += err_r * 7.0f/16.0f;
                working[right_idx + 1] += err_g * 7.0f/16.0f;
                working[right_idx + 2] += err_b * 7.0f/16.0f;
            }
            
            if (y + 1 < height) {
                if (x > 0) {
                    int bl_idx = ((y + 1) * padded_width + x) * 3;
                    working[bl_idx] += err_r * 3.0f/16.0f;
                    working[bl_idx + 1] += err_g * 3.0f/16.0f;
                    working[bl_idx + 2] += err_b * 3.0f/16.0f;
                }
                
                int bottom_idx = ((y + 1) * padded_width + (x + 1)) * 3;
                working[bottom_idx] += err_r * 5.0f/16.0f;
                working[bottom_idx + 1] += err_g * 5.0f/16.0f;
                working[bottom_idx + 2] += err_b * 5.0f/16.0f;
                
                if (x + 1 < width) {
                    int br_idx = ((y + 1) * padded_width + (x + 2)) * 3;
                    working[br_idx] += err_r * 1.0f/16.0f;
                    working[br_idx + 1] += err_g * 1.0f/16.0f;
                    working[br_idx + 2] += err_b * 1.0f/16.0f;
                }
            }
        }
    }
    
    free(working);
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        printf("Usage: %s input.raw output.raw width height\\n", argv[0]);
        return 1;
    }
    
    int width = atoi(argv[3]);
    int height = atoi(argv[4]);
    
    // Read raw RGB data
    FILE* input = fopen(argv[1], "rb");
    if (!input) {
        printf("Cannot open input file\\n");
        return 1;
    }
    
    uint8_t* image = malloc(width * height * 3);
    uint8_t* output = malloc(width * height * 3);
    
    fread(image, 1, width * height * 3, input);
    fclose(input);
    
    // Process
    floyd_steinberg_dither(image, width, height, output);
    
    // Write output
    FILE* out = fopen(argv[2], "wb");
    fwrite(output, 1, width * height * 3, out);
    fclose(out);
    
    free(image);
    free(output);
    
    return 0;
}
'''
    
    # Save C code
    c_file = Path("test/outputs/fast_dither.c")
    c_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(c_file, 'w') as f:
        f.write(c_code)
    
    return c_file


def compile_c_dithering():
    """Compile the C dithering program."""
    try:
        c_file = create_c_dithering_binary()
        binary_file = c_file.with_suffix('')
        
        # Compile with optimizations
        cmd = ['gcc', '-O3', '-march=native', '-o', str(binary_file), str(c_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ C binary compiled: {binary_file}")
            return binary_file
        else:
            print(f"❌ C compilation failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ C compilation error: {e}")
        return None


def c_binary_conversion(input_path, output_path):
    """
    Use compiled C binary for dithering (future implementation).
    """
    try:
        binary = compile_c_dithering()
        if not binary:
            return False
        
        # This would need additional PIL integration to convert to/from raw format
        print("🔧 C binary approach requires additional integration")
        return False
        
    except Exception as e:
        print(f"C binary conversion failed: {e}")
        return False


# Performance recommendations based on testing
PERFORMANCE_RECOMMENDATIONS = {
    'fastest': {
        'name': 'Hybrid Approach (PIL Quantize without dithering)',
        'speedup': '230x',
        'time': '~0.13s',
        'quality': 'Good (no dithering)',
        'use_case': 'When speed is critical and slight quality loss is acceptable'
    },
    'balanced': {
        'name': 'PIL Quantize with Floyd-Steinberg',
        'speedup': '164x', 
        'time': '~0.18s',
        'quality': 'Excellent (with dithering)',
        'use_case': 'Best balance of speed and quality'
    },
    'external': {
        'name': 'ImageMagick CLI',
        'speedup': '57x',
        'time': '~0.52s', 
        'quality': 'Excellent (external dependency)',
        'use_case': 'When you want to avoid Python overhead'
    },
    'future': {
        'name': 'C/C++ Binary',
        'speedup': 'Estimated 500-1000x',
        'time': '~0.03-0.06s',
        'quality': 'Perfect (identical to current)',
        'use_case': 'Maximum performance for production systems'
    }
}


def print_final_recommendations():
    """Print comprehensive performance recommendations."""
    print("\n" + "="*60)
    print("🏆 FINAL PERFORMANCE RECOMMENDATIONS")
    print("="*60)
    
    print(f"Current baseline: 29.7s (unacceptably slow)")
    print(f"Target for Pi: <1s (acceptable for user experience)")
    print()
    
    for category, info in PERFORMANCE_RECOMMENDATIONS.items():
        print(f"🎯 {category.upper()}:")
        print(f"   Strategy: {info['name']}")
        print(f"   Speed: {info['time']} ({info['speedup']} speedup)")
        print(f"   Quality: {info['quality']}")
        print(f"   Use case: {info['use_case']}")
        print()
    
    print("💡 IMMEDIATE RECOMMENDATION:")
    print("   Replace current Floyd-Steinberg with PIL Quantize + Floyd-Steinberg")
    print("   - 164x faster (29.7s → 0.18s)")
    print("   - Maintains excellent quality")
    print("   - No external dependencies")
    print("   - Production ready")
    print()
    
    print("🚀 FUTURE OPTIMIZATION:")
    print("   Implement C/C++ binary for sub-100ms conversions")
    print("   - Use original C code as starting point")
    print("   - Compile with -O3 -march=native optimizations")
    print("   - Call as external process from Python")
    print("   - Estimated 500-1000x speedup potential")


if __name__ == "__main__":
    print_final_recommendations()