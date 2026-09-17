from PIL import Image, ImageEnhance, ImageFilter
import os

original_path = r"C:\Users\Lasith\.gemini\antigravity\brain\1660019e-99ca-4b0c-875f-3daf1ec04ef6\.user_uploaded\media_1789617619309.png"

img = Image.open(original_path).convert("RGBA")
w, h = img.size

# 8x High-DPI Upscale for Retina/4K clarity
scale = 8
new_w, new_h = w * scale, h * scale

# High quality Lanczos resampling
upscaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

# Enhance sharpness and contrast
enhancer = ImageEnhance.Sharpness(upscaled)
sharpened = enhancer.enhance(2.5)

contrast = ImageEnhance.Contrast(sharpened)
final_logo = contrast.enhance(1.15)

# Save high-DPI logo
final_logo.save("hipg_logo.png", "PNG")
final_logo.save("static/hipg_logo.png", "PNG")
print(f"Saved 8x High-DPI logo: {new_w}x{new_h}")

# Create square 512x512 crisp favicon from original logo
fav_bg = Image.new("RGBA", (512, 512), (255, 255, 255, 0))

# Scale logo to fit nicely in 512x512
target_w = 460
aspect = h / w
target_h = int(target_w * aspect)
logo_resized = final_logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

offset_x = (512 - target_w) // 2
offset_y = (512 - target_h) // 2
fav_bg.paste(logo_resized, (offset_x, offset_y), logo_resized)

fav_bg.save("favicon.png", "PNG")
fav_bg.save("static/favicon.png", "PNG")
print("Saved 512x512 crisp favicon.png from official logo")
