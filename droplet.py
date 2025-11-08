from PIL import Image, ImageDraw
import math

def draw_cap(draw, x, y, w, h):
    """Draws a cartoonish backwards baseball cap that sits on top of the droplet."""
    cap_main_color = (30, 70, 180, 255)
    cap_shade_color = (20, 50, 130, 255)
    cap_highlight_color = (80, 120, 220, 255)

    dome_height = h // 4
    brim_height = h // 10

    # Dome of cap (rounded top)
    dome_box = (x - w//2, y - h//2 - dome_height, x + w//2, y - h//2 + dome_height//2)
    draw.pieslice(dome_box, start=0, end=180, fill=cap_main_color)

    # Shading at base of dome
    shade_box = (x - w//2, y - h//2 - dome_height//4, x + w//2, y - h//2 + dome_height)
    draw.pieslice(shade_box, start=0, end=180, fill=cap_shade_color)

    # Backwards brim (arched, visible behind head)
    brim_box = (x - w//1.6, y - h//2 - brim_height, x + w//1.6, y - h//2 + brim_height)
    draw.arc(brim_box, start=10, end=170, fill=cap_highlight_color, width=5)

    # Button on top
    draw.ellipse((x - 4, y - h//2 - dome_height - 2, x + 4, y - h//2 - dome_height + 6), fill=cap_highlight_color)

    # Stitch line (simple central line)
    draw.line((x, y - h//2 - dome_height + 5, x, y - h//2 + 5), fill=(200, 220, 255, 120), width=1)


def draw_droplet(draw, center, size):
    """Draws a cute water droplet with a refined hat and gold necklace."""
    x, y = center
    w, h = size

    # Body (rounded teardrop)
    draw.ellipse((x - w//2, y - h//2, x + w//2, y + h//2), fill=(100, 180, 255, 255))

    # Highlight
    highlight_box = (x - w//4, y - h//3, x - w//10, y - h//6)
    draw.ellipse(highlight_box, fill=(180, 230, 255, 180))

    # Face
    eye_offset_x = w // 6
    eye_y = y - h // 12
    eye_r = w // 15
    draw.ellipse((x - eye_offset_x - eye_r, eye_y - eye_r, x - eye_offset_x + eye_r, eye_y + eye_r), fill=(0, 0, 0, 255))
    draw.ellipse((x + eye_offset_x - eye_r, eye_y - eye_r, x + eye_offset_x + eye_r, eye_y + eye_r), fill=(0, 0, 0, 255))

    # Smile
    mouth_y = y + h // 8
    mouth_w = w // 4
    mouth_h = h // 10
    draw.arc(
        (x - mouth_w//2, mouth_y - mouth_h//2, x + mouth_w//2, mouth_y + mouth_h//2),
        start=20,
        end=160,
        fill=(0, 0, 0, 255),
        width=2
    )

    # Necklace (gold chain arc)
    chain_y = y + h // 3
    chain_r = w // 2
    for i in range(12):
        angle = math.pi * (i / 11)
        cx = x + math.cos(angle) * chain_r * 0.6
        cy = chain_y + math.sin(angle) * 5
        draw.ellipse(
            (cx - 3, cy - 3, cx + 3, cy + 3),
            fill=(255, 215, 0, 255),
            outline=(200, 160, 0, 255)
        )

    # Dollar sign pendant
    pendant_y = chain_y + 8
    draw.text((x - 4, pendant_y), "$", fill=(255, 215, 0, 255))

    # Add the cap last so it sits on top
    draw_cap(draw, x, y, w, h)


def make_bounce_gif(filename="bouncing_droplet_refined_hat.gif", frame_count=30, size=(200, 200), duration=40):
    frames = []
    width, height = size

    for i in range(frame_count):
        frame = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        bounce = int(math.sin(i / frame_count * math.pi * 2) * 20)
        droplet_center = (width // 2, height // 2 + bounce)

        draw_droplet(draw, droplet_center, (60, 80))
        frames.append(frame)

    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        transparency=0,
        disposal=2
    )
    print(f"✅ Saved '{filename}' with refined backwards cap and bling.")

if __name__ == "__main__":
    make_bounce_gif()
