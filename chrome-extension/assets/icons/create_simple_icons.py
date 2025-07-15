#!/usr/bin/env python3
"""Create simple PNG icons without external dependencies."""

import struct
import zlib

def create_png(width, height, rgb_color=(37, 99, 235)):
    """Create a simple solid color PNG."""
    
    # PNG header
    png_header = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    
    # IDAT chunk (image data)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter type
        for x in range(width):
            # Simple blue color with white "P" pattern
            if (width//4 <= x <= width//2) and (height//6 <= y <= height - height//6):
                # Vertical line of P
                raw_data += struct.pack('BBB', 255, 255, 255)
            elif (width//4 <= x <= 3*width//4) and (height//6 <= y <= height//6 + height//8):
                # Top horizontal of P
                raw_data += struct.pack('BBB', 255, 255, 255)
            elif (width//4 <= x <= 3*width//4) and (height//2 - height//16 <= y <= height//2 + height//16):
                # Middle horizontal of P
                raw_data += struct.pack('BBB', 255, 255, 255)
            elif (5*width//8 <= x <= 3*width//4) and (height//6 <= y <= height//2 + height//16):
                # Right curve of P
                raw_data += struct.pack('BBB', 255, 255, 255)
            else:
                # Background color
                raw_data += struct.pack('BBB', *rgb_color)
    
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b'IDAT' + compressed)
    idat_chunk = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    
    # IEND chunk
    iend_crc = zlib.crc32(b'IEND')
    iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    
    return png_header + ihdr_chunk + idat_chunk + iend_chunk

# Create icons
sizes = [16, 32, 48, 128]

for size in sizes:
    png_data = create_png(size, size)
    filename = f'icon-{size}.png'
    
    with open(filename, 'wb') as f:
        f.write(png_data)
    
    print(f"Created {filename}")

print("\nAll icons created successfully!")
print("You can now load the Chrome extension.")