from PIL import Image, ImageDraw, ImageFont
import os

def create_highres_favicon():
    # 512x512 High-DPI Favicon
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rectangle
    bg_color = (15, 76, 103, 255) # Deep HIPG Teal/Navy
    draw.rounded_rectangle([0, 0, size, size], radius=90, fill=bg_color)

    # White shield outline
    cx, cy = 256, 195
    shield_pts = [
        (cx, cy - 85),
        (cx + 65, cy - 75),
        (cx + 70, cy - 25),
        (cx + 60, cy + 45),
        (cx, cy + 95),
        (cx - 60, cy + 45),
        (cx - 70, cy - 25),
        (cx - 65, cy - 75)
    ]
    draw.polygon(shield_pts, fill=(15, 76, 103, 255), outline=(255, 255, 255, 255), width=10)

    # Ship silhouette (Vessel bow) inside shield
    ship_pts = [(cx, cy - 50), (cx + 38, cy + 15), (cx - 38, cy + 15)]
    draw.polygon(ship_pts, fill=(255, 255, 255, 255))
    ship_right = [(cx, cy - 50), (cx + 38, cy + 15), (cx, cy + 50)]
    draw.polygon(ship_right, fill=(224, 242, 254, 255))

    # Water wave arcs
    draw.arc([cx - 45, cy + 20, cx + 45, cy + 50], start=0, end=180, fill=(255, 255, 255, 255), width=8)
    draw.arc([cx - 35, cy + 42, cx + 35, cy + 68], start=0, end=180, fill=(56, 189, 248, 255), width=6)

    # Text "HIPG" bold high resolution
    try:
        font = ImageFont.truetype("arialbd.ttf", 110)
    except Exception:
        font = ImageFont.load_default()

    draw.text((256, 410), "HIPG", fill=(255, 255, 255, 255), font=font, anchor="mm")

    # Gold CM Emblem
    draw.ellipse([395, 45, 465, 115], fill=(197, 160, 89, 255), outline=(255, 255, 255, 255), width=4)
    try:
        font_cm = ImageFont.truetype("arialbd.ttf", 26)
    except Exception:
        font_cm = ImageFont.load_default()
    draw.text((430, 80), "CM", fill=(255, 255, 255, 255), font=font_cm, anchor="mm")

    return img

def create_highres_logo_horizontal():
    # 1200x360 Ultra High-Res Transparent Logo
    width, height = 1200, 360
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    brand_color = (15, 76, 103, 255)

    # H - Left Pillar
    draw.rounded_rectangle([60, 50, 130, 290], radius=16, fill=brand_color)
    # H - Right Pillar
    draw.rounded_rectangle([210, 50, 280, 290], radius=16, fill=brand_color)
    # H - Crossbar
    draw.rectangle([110, 155, 230, 205], fill=brand_color)

    # Vessel emblem atop H crossbar
    cx, cy = 170, 115
    shield_pts = [
        (cx, cy - 45), (cx + 35, cy - 40), (cx + 38, cy - 10),
        (cx + 30, cy + 25), (cx, cy + 50), (cx - 30, cy + 25),
        (cx - 38, cy - 10), (cx - 35, cy - 40)
    ]
    draw.polygon(shield_pts, fill=brand_color, outline=(224, 242, 254, 255), width=5)
    draw.polygon([(cx, cy - 25), (cx + 20, cy + 10), (cx - 20, cy + 10)], fill=(224, 242, 254, 255))
    draw.polygon([(cx, cy - 25), (cx + 20, cy + 10), (cx, cy + 30)], fill=(255, 255, 255, 255))

    # I Pillar
    draw.rounded_rectangle([320, 50, 390, 290], radius=16, fill=brand_color)

    # P Letter
    draw.rounded_rectangle([430, 50, 500, 290], radius=16, fill=brand_color)
    draw.rounded_rectangle([480, 50, 610, 180], radius=40, fill=brand_color)
    draw.rounded_rectangle([530, 95, 570, 135], radius=15, fill=(0, 0, 0, 0)) # Inner cutout

    # G Letter
    draw.ellipse([640, 50, 880, 290], fill=brand_color)
    draw.ellipse([700, 110, 820, 230], fill=(0, 0, 0, 0)) # Inner cutout
    draw.rectangle([760, 160, 890, 210], fill=brand_color) # Bar

    # Gold CM Emblem Accent
    draw.ellipse([920, 50, 990, 120], fill=None, outline=(197, 160, 89, 255), width=6)
    try:
        font_cm = ImageFont.truetype("arialbd.ttf", 28)
    except Exception:
        font_cm = ImageFont.load_default()
    draw.text((955, 85), "CM", fill=(197, 160, 89, 255), font=font_cm, anchor="mm")

    return img

if __name__ == "__main__":
    fav = create_highres_favicon()
    fav.save("favicon.png", "PNG")
    fav.save("static/favicon.png", "PNG")
    print("Saved 512x512 crisp favicon.png")

    logo = create_highres_logo_horizontal()
    logo.save("hipg_logo.png", "PNG")
    logo.save("static/hipg_logo.png", "PNG")
    print("Saved 1200x360 crisp hipg_logo.png")
