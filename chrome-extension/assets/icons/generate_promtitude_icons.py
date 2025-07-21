#!/usr/bin/env python3
"""
Generate Promtitude Chrome Extension icons in all required sizes
"""

from PIL import Image, ImageDraw
import os

def create_rounded_rectangle(size, radius, color):
    """Create a rounded rectangle image"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle
    draw.rounded_rectangle(
        [(0, 0), (size-1, size-1)],
        radius=radius,
        fill=color
    )
    
    return img, draw

def draw_p_logo(draw, size, color='white'):
    """Draw the Promtitude P logo"""
    # Calculate scaling
    padding = size * 0.25
    scale = (size - padding * 2) / 80
    
    # Adjust line width based on size
    if size <= 16:
        line_width = int(3 * scale)
    elif size <= 32:
        line_width = int(4 * scale)
    else:
        line_width = int(5 * scale)
    
    # P shape coordinates (scaled)
    x_start = int(padding + 10 * scale)
    y_start = int(padding + 10 * scale)
    x_end = int(padding + 50 * scale)
    y_end = int(padding + 70 * scale)
    y_middle = int(padding + 40 * scale)
    
    # Draw P shape
    # Vertical line
    draw.rectangle(
        [x_start, y_start, x_start + line_width, y_end],
        fill=color
    )
    
    # Top horizontal line
    draw.rectangle(
        [x_start, y_start, x_end, y_start + line_width],
        fill=color
    )
    
    # Right vertical line (top part)
    draw.rectangle(
        [x_end - line_width, y_start, x_end, y_middle],
        fill=color
    )
    
    # Middle horizontal line
    draw.rectangle(
        [x_start, y_middle - line_width, x_end, y_middle],
        fill=color
    )
    
    # Add circuit dots for larger sizes
    if size >= 48:
        dot_size = max(2, int(size / 32))
        # Top-left dot
        draw.ellipse(
            [x_start - dot_size, y_start - dot_size,
             x_start + dot_size, y_start + dot_size],
            fill=color
        )
        # Top-right dot
        draw.ellipse(
            [x_end - dot_size, y_start - dot_size,
             x_end + dot_size, y_start + dot_size],
            fill=color
        )
        # Middle-right dot
        draw.ellipse(
            [x_end - dot_size, y_middle - dot_size,
             x_end + dot_size, y_middle + dot_size],
            fill=color
        )
        # Bottom-left dot
        draw.ellipse(
            [x_start - dot_size, y_end - dot_size,
             x_start + dot_size, y_end + dot_size],
            fill=color
        )

def generate_icon(size):
    """Generate a single icon"""
    # Colors
    primary_color = (79, 70, 229)  # #4F46E5
    white = (255, 255, 255)
    
    # Create rounded rectangle background
    radius = int(size * 0.1875)  # 24/128 = 0.1875
    img, draw = create_rounded_rectangle(size, radius, primary_color)
    
    # Draw P logo
    draw_p_logo(draw, size, color=white)
    
    # Save the icon
    filename = f'icon-{size}.png'
    img.save(filename, 'PNG', quality=95)
    print(f"✅ Generated {filename}")

def main():
    """Generate all icon sizes"""
    print("🎨 Generating Promtitude Chrome Extension icons...")
    
    sizes = [16, 32, 48, 128]
    
    for size in sizes:
        generate_icon(size)
    
    print("\n✨ All icons generated successfully!")
    print("📦 Ready to include in your Chrome extension")

if __name__ == "__main__":
    # Check if PIL is installed
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("❌ Error: Pillow is not installed")
        print("📦 Install it with: pip install Pillow")
        exit(1)
    
    main()