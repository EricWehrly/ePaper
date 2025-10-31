"""
Conversion Configuration Presets

Defines different conversion configurations including legacy settings
for comparison testing and future user interface integration.
"""

from PIL import Image, ImageEnhance, ImageFilter
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ConversionConfig:
    """Configuration for image conversion parameters."""
    name: str
    description: str
    contrast_enhancement: float = 1.0
    color_enhancement: float = 1.0  
    sharpness_enhancement: float = 1.0
    dithering_method: Image.Dither = Image.Dither.FLOYDSTEINBERG
    preprocessing_filter: Optional[Callable] = None


def apply_blur_filter(image):
    """Apply slight blur to reduce noise."""
    return image.filter(ImageFilter.GaussianBlur(radius=0.5))


def apply_sharpen_filter(image):
    """Apply sharpening filter."""
    return image.filter(ImageFilter.SHARPEN)


# Conversion presets
CONVERSION_PRESETS = {
    'legacy': ConversionConfig(
        name="Legacy",
        description="Original conversion settings (resize only, manual dithering)",
        contrast_enhancement=1.0,
        color_enhancement=1.0,
        sharpness_enhancement=1.0,
        dithering_method=Image.Dither.FLOYDSTEINBERG
    ),
    
    'current': ConversionConfig(
        name="Current Default", 
        description="Optimized PIL quantization with enhanced contrast",
        contrast_enhancement=1.3,
        color_enhancement=1.3,
        sharpness_enhancement=1.1,
        dithering_method=Image.Dither.FLOYDSTEINBERG
    ),
    
    'high_contrast': ConversionConfig(
        name="High Contrast",
        description="For washed-out or low-contrast images",
        contrast_enhancement=1.5,
        color_enhancement=1.4,
        sharpness_enhancement=1.3,
        dithering_method=Image.Dither.FLOYDSTEINBERG
    ),
    
    'soft': ConversionConfig(
        name="Soft Enhancement", 
        description="Gentle enhancement for well-balanced images",
        contrast_enhancement=1.1,
        color_enhancement=1.1,
        sharpness_enhancement=1.0,
        dithering_method=Image.Dither.FLOYDSTEINBERG
    ),
    
    'no_dither': ConversionConfig(
        name="No Dithering",
        description="Fastest conversion, solid colors only",
        contrast_enhancement=1.3,
        color_enhancement=1.3, 
        sharpness_enhancement=1.1,
        dithering_method=Image.Dither.NONE
    ),
    
    'ordered_dither': ConversionConfig(
        name="Ordered Dithering",
        description="Pattern-based dithering (faster than Floyd-Steinberg)",
        contrast_enhancement=1.3,
        color_enhancement=1.3,
        sharpness_enhancement=1.1,
        dithering_method=Image.Dither.ORDERED
    ),
    
    'smooth': ConversionConfig(
        name="Smooth", 
        description="Blur first to reduce noise, then enhance",
        contrast_enhancement=1.3,
        color_enhancement=1.3,
        sharpness_enhancement=1.2,
        dithering_method=Image.Dither.FLOYDSTEINBERG,
        preprocessing_filter=apply_blur_filter
    )
}


def get_config(preset_name: str) -> ConversionConfig:
    """Get conversion configuration by preset name."""
    if preset_name not in CONVERSION_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(CONVERSION_PRESETS.keys())}")
    
    return CONVERSION_PRESETS[preset_name]


def list_presets():
    """List all available conversion presets."""
    print("📋 Available conversion presets:")
    print("=" * 50)
    
    for key, config in CONVERSION_PRESETS.items():
        print(f"  {key:15}: {config.description}")
        print(f"                   Contrast: {config.contrast_enhancement:.1f}x, "
              f"Color: {config.color_enhancement:.1f}x, "
              f"Sharp: {config.sharpness_enhancement:.1f}x")
        print(f"                   Dithering: {config.dithering_method.name}")
        if config.preprocessing_filter:
            print(f"                   Filter: {config.preprocessing_filter.__name__}")
        print()


def apply_config_preprocessing(image, config: ConversionConfig):
    """Apply preprocessing according to configuration."""
    from .preprocessing import resize_image_to_display
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to display resolution
    image = resize_image_to_display(image)
    
    # Apply preprocessing filter if specified
    if config.preprocessing_filter:
        image = config.preprocessing_filter(image)
    
    # Apply enhancements according to config
    if config.contrast_enhancement != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(config.contrast_enhancement)
    
    if config.color_enhancement != 1.0:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(config.color_enhancement)
        
    if config.sharpness_enhancement != 1.0:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(config.sharpness_enhancement)
    
    return image


# TODO: Future UI integration
# - Add preset selector to web interface
# - Allow custom config creation in UI
# - Save user preferences per image type
# - A/B testing interface for different presets
# - Real-time preview of preset effects