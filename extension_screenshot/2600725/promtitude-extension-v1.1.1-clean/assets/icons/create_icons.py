#!/usr/bin/env python3
"""Create simple icon files for Chrome extension."""

from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
icons_dir = os.path.dirname(os.path.abspath(__file__))

# Define icon sizes
sizes = [16, 32, 48, 128]

# Create a simple icon with "P" for Promtitude
for size in sizes:
    # Create a new image with a blue background
    img = Image.new('RGB', (size, size), color='#2563eb')
    draw = ImageDraw.Draw(img)
    
    # Draw a white "P" in the center
    # Calculate font size (roughly 60% of icon size)
    font_size = int(size * 0.6)
    
    # Use a simple approach - draw a white rectangle and curves to form "P"
    padding = size // 8
    draw.rectangle([padding, padding, size-padding, size-padding], fill='#2563eb')
    
    # Draw white "P" shape
    white = '#ffffff'
    stroke_width = max(1, size // 16)
    
    # Vertical line of P
    x1 = size // 4
    draw.rectangle([x1, size//6, x1 + stroke_width*2, size - size//6], fill=white)
    
    # Top horizontal line of P
    draw.rectangle([x1, size//6, size - size//4, size//6 + stroke_width*2], fill=white)
    
    # Middle horizontal line of P
    draw.rectangle([x1, size//2 - stroke_width, size - size//4, size//2 + stroke_width], fill=white)
    
    # Right vertical line of P (partial)
    draw.rectangle([size - size//4 - stroke_width*2, size//6, size - size//4, size//2 + stroke_width], fill=white)
    
    # Save the icon
    img.save(os.path.join(icons_dir, f'icon-{size}.png'))
    print(f"Created icon-{size}.png")

print("All icons created successfully!")