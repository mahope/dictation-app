"""Generate the app icon (icon.ico) with the equalizer design."""

from PIL import Image, ImageDraw


def generate_icon():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Dark rounded background
        pad = max(1, size // 32)
        radius = max(2, size // 5)
        draw.rounded_rectangle(
            [pad, pad, size - pad, size - pad],
            radius=radius, fill="#2d2d2d",
        )

        # Equalizer bars
        bar_count = 5
        bar_w = max(1, size // 10)
        gap = max(1, size // 12)
        heights_pct = [0.35, 0.55, 0.80, 0.55, 0.35]
        total_w = bar_count * bar_w + (bar_count - 1) * gap
        start_x = (size - total_w) // 2
        cy = size // 2

        for i in range(bar_count):
            x = start_x + i * (bar_w + gap)
            h = max(2, int(size * 0.6 * heights_pct[i]))
            bar_radius = max(1, bar_w // 3)
            draw.rounded_rectangle(
                [x, cy - h // 2, x + bar_w, cy + h // 2],
                radius=bar_radius, fill="#a3a3a3",
            )

        images.append(img)

    # Save as .ico with multiple sizes
    images[0].save(
        "icon.ico", format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Generated icon.ico ({len(sizes)} sizes)")


if __name__ == "__main__":
    generate_icon()
