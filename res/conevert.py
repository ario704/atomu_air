from PIL import Image
import sys
import os

def rgb888_to_rgb565(r, g, b):
    """Convert 8-bit R, G, B to 16-bit RGB565"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def convert_image(input_path):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    # Load image
    img = Image.open(input_path)

    # Handle transparency
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        print("Image has transparency. Flattening to opaque RGB.")
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (0, 0, 0, 255))  # fully opaque black
        img = Image.alpha_composite(bg, img)
        img = img.convert("RGB")
    else:
        img = img.convert("RGB")
    
    width, height = img.size
    print(f"Converting {input_path} ({width}x{height})...")

    base = os.path.splitext(input_path)[0]
    output_path = base + ".raw"

    with open(output_path, "wb") as f:
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                rgb565 = rgb888_to_rgb565(r, g, b)
                f.write(rgb565.to_bytes(2, 'big'))

    print(f"Done. Output saved as: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_to_rgb565.py <image_file>")
    else:
        convert_image(sys.argv[1])
