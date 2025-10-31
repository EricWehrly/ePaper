"""
Alternative Preprocessing Options

Collection of different preprocessing approaches for e-paper conversion.
These can be used for testing and future optimization.
"""

from PIL import Image, ImageEnhance, ImageFilter


def preprocess_original(image):
    """Original preprocessing: resize only (legacy behavior)."""
    from .preprocessing import resize_image_to_display
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    return resize_image_to_display(image)


def preprocess_enhanced_contrast_only(image):
    """Enhanced contrast only (no color/sharpness adjustments)."""
    from .preprocessing import resize_image_to_display
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image = resize_image_to_display(image)
    
    # Enhanced contrast for better e-paper visibility
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.3)
    
    return image


def preprocess_high_contrast(image):
    """High contrast version for very washed-out images."""
    from .preprocessing import resize_image_to_display
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image = resize_image_to_display(image)
    
    # High contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    # Enhanced saturation
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.4)
    
    # More aggressive sharpening
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.3)
    
    return image


def preprocess_soft_enhancement(image):
    """Gentle enhancement for already well-balanced images.""" 
    from .preprocessing import resize_image_to_display
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image = resize_image_to_display(image)
    
    # Mild contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.1)
    
    # Subtle color enhancement
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.1)
    
    return image


def preprocess_with_blur_reduction(image):
    """Preprocessing with slight blur to smooth noise before enhancement."""
    from .preprocessing import resize_image_to_display
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image = resize_image_to_display(image)
    
    # Slight blur to reduce noise
    image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Standard enhancements
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.3)
    
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.3)
    
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.2)
    
    return image


# Dictionary of available preprocessing options
PREPROCESSING_OPTIONS = {
    'default': 'Current production default (contrast 1.3x, color 1.3x, sharp 1.1x)',
    'original': 'Legacy behavior (resize only)',
    'contrast_only': 'Enhanced contrast only (1.3x)',
    'high_contrast': 'High contrast for washed-out images (1.5x)',
    'soft': 'Gentle enhancement for balanced images (1.1x)',
    'blur_smooth': 'Blur smoothing + enhancement'
}


def get_preprocessing_function(option_name):
    """Get preprocessing function by name."""
    functions = {
        'original': preprocess_original,
        'contrast_only': preprocess_enhanced_contrast_only, 
        'high_contrast': preprocess_high_contrast,
        'soft': preprocess_soft_enhancement,
        'blur_smooth': preprocess_with_blur_reduction
    }
    
    return functions.get(option_name)


def list_preprocessing_options():
    """List all available preprocessing options."""
    print("📋 Available preprocessing options:")
    print("=" * 50)
    
    for key, description in PREPROCESSING_OPTIONS.items():
        print(f"  {key:15}: {description}")
    
    print("\n💡 Usage: Use get_preprocessing_function(option_name) to get function")