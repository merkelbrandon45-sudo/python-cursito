from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    img = Image.new('RGBA', (size, size), (0, 123, 255, 255))  # Azul
    draw = ImageDraw.Draw(img)
    # Dibujar un círculo simple
    draw.ellipse([10, 10, size-10, size-10], fill=(255, 255, 255, 255))
    # Texto "B"
    try:
        font = ImageFont.truetype("arial.ttf", size//2)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "B", font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), "B", fill=(0, 0, 0, 255), font=font)
    img.save(filename)

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    create_icon(192, "static/icon-192.png")
    create_icon(512, "static/icon-512.png")
    print("Iconos creados!")