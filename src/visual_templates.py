"""Visuels sociaux professionnels — templates Pillow (texte FR lisible, charte stricte)."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
MARGIN = 56

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
]


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    preferred = FONT_CANDIDATES if bold else FONT_CANDIDATES[1::2] + FONT_CANDIDATES[::2]
    for path in preferred:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _font_fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int,
    bold: bool = True,
    min_size: int = 28,
) -> ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        font = _font(size, bold)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return _font(min_size, bold)


def _draw_text_crisp(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    outline_width: int = 2,
) -> None:
    """Texte net avec contour optionnel pour lisibilité maximale."""
    x, y = xy
    if outline and outline_width > 0:
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx or dy:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_multiline(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    lines: list[str],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    spacing: int = 12,
    outline: tuple[int, int, int] | None = None,
) -> int:
    cy = y
    for line in lines:
        _draw_text_crisp(draw, (x, cy), line, font, fill, outline=outline)
        cy += font.size + spacing
    return cy


def _paste_logo(
    canvas: Image.Image,
    logo_path: Path | None,
    position: str = "bottom-right",
    max_width_ratio: float = 0.24,
) -> None:
    if not logo_path or not logo_path.exists():
        return
    logo = Image.open(logo_path).convert("RGBA")
    target_w = int(canvas.width * max_width_ratio)
    ratio = target_w / logo.width
    target_h = int(logo.height * ratio)
    logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
    margin = MARGIN
    positions = {
        "bottom-right": (canvas.width - target_w - margin, canvas.height - target_h - margin),
        "top-left": (margin, margin),
        "top-right": (canvas.width - target_w - margin, margin),
    }
    x, y = positions.get(position, positions["bottom-right"])
    pad = 10
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(
        [x - pad, y - pad, x + target_w + pad, y + target_h + pad],
        radius=14,
        fill=(255, 255, 255, 210),
    )
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba = Image.alpha_composite(canvas_rgba, overlay)
    canvas_rgba.paste(logo, (x, y), logo)
    canvas.paste(canvas_rgba.convert("RGB"))


def _draw_kawa_decor(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """Montagnes stylisées + cerises — formes géométriques, pas de photo."""
    blue = _hex_to_rgb("#5BA3D9")
    green = _hex_to_rgb("#4CAF50")
    red = _hex_to_rgb("#E53935")
    brown = _hex_to_rgb("#5D4037")

    # Bande montagnes
    peaks = [(0, 520), (180, 380), (360, 450), (540, 320), (720, 400), (900, 350), (w, 420), (w, 520)]
    draw.polygon(peaks, fill=green)
    peaks2 = [(0, 520), (220, 420), (480, 480), (w, 400), (w, 520)]
    draw.polygon(peaks2, fill=blue)

    # Cerises stylisées (cercles)
    for cx, cy in [(140, 620), (200, 680), (880, 640), (820, 700), (760, 620)]:
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=red)
        draw.ellipse([cx - 6, cy - 28, cx + 6, cy - 16], fill=green)

    # Grains de café
    for cx, cy in [(950, 180), (100, 200)]:
        draw.ellipse([cx - 14, cy - 20, cx + 14, cy + 20], fill=brown, outline=(0, 0, 0))


def _draw_phone_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    """Silhouette téléphone simple — pas d'image produit aléatoire."""
    w, h = int(120 * scale), int(200 * scale)
    x0, y0 = cx - w // 2, cy - h // 2
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=18, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    draw.rounded_rectangle([x0 + 12, y0 + 24, x0 + w - 12, y0 + h - 48], radius=8, fill=(26, 138, 138))
    draw.ellipse([x0 + w // 2 - 10, y0 + h - 32, x0 + w // 2 + 10, y0 + h - 12], fill=(0, 0, 0))


def _draw_briefcase_icon(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int]) -> None:
    draw.rounded_rectangle([x, y + 30, x + 140, y + 130], radius=12, fill=color)
    draw.arc([x + 40, y, x + 100, y + 50], start=180, end=0, fill=color, width=8)
    # Courbe croissance
    pts = [(x + 20, y + 110), (x + 50, y + 85), (x + 80, y + 95), (x + 120, y + 55)]
    draw.line(pts, fill=(255, 255, 255), width=4, joint="curve")
    for px, py in pts:
        draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(255, 255, 255))


def _draw_dashboard_mock(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    blue = _hex_to_rgb("#2196F3")
    navy = _hex_to_rgb("#1A237E")
    draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=(255, 255, 255), outline=navy, width=2)
    draw.rectangle([x, y, x + w, y + 48], fill=navy)
    for i, col in enumerate([blue, navy, blue]):
        bx = x + 20 + i * ((w - 60) // 3 + 10)
        draw.rounded_rectangle([bx, y + 68, bx + (w - 60) // 3, y + 140], radius=8, fill=col if i != 1 else (227, 242, 253))
    draw.line([(x + 30, y + h - 60), (x + w - 30, y + h - 60)], fill=blue, width=3)
    draw.line([(x + 30, y + h - 60), (x + 80, y + h - 100), (x + 140, y + h - 85), (x + w - 40, y + h - 130)], fill=blue, width=3)


def render_kawa(
    out_path: Path,
    headline: str,
    subtitle: str,
    logo_path: Path | None,
) -> None:
    img = Image.new("RGB", (SIZE, SIZE), _hex_to_rgb("#FFFFFF"))
    draw = ImageDraw.Draw(img)
    _draw_kawa_decor(draw, SIZE, SIZE)

    # Bandeau texte bas
    draw.rectangle([0, SIZE - 340, SIZE, SIZE], fill=(255, 255, 255))
    draw.rectangle([0, SIZE - 344, SIZE, SIZE - 340], fill=_hex_to_rgb("#5BA3D9"))

    headline = _clean_fr(headline)
    subtitle = _clean_fr(subtitle)
    max_w = SIZE - 2 * MARGIN - 120

    # Titre adaptatif — texte complet du briefing, jamais tronqué arbitrairement
    title_font = _font_fit(draw, headline, max_w, 48, bold=True, min_size=32)
    lines = _wrap_text(draw, headline, title_font, max_w)
    y = SIZE - 310
    y = _draw_multiline(draw, MARGIN, y, lines[:3], title_font, (0, 0, 0), spacing=6)

    sub_font = _font(28, bold=False)
    sub_lines = _wrap_text(draw, subtitle, sub_font, max_w)
    _draw_multiline(draw, MARGIN, y + 8, sub_lines[:2], sub_font, _hex_to_rgb("#5D4037"))

    # Badge Fairtrade discret
    badge_font = _font(22)
    draw.rounded_rectangle([MARGIN, MARGIN, MARGIN + 200, MARGIN + 44], radius=10, fill=_hex_to_rgb("#E53935"))
    _draw_text_crisp(draw, (MARGIN + 16, MARGIN + 8), "FAIRTRADE", badge_font, (255, 255, 255))

    _paste_logo(img, logo_path, "top-right", 0.20)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def _paste_product_photo(
    canvas: Image.Image,
    photo_path: Path,
    box: tuple[int, int, int, int],
) -> None:
    """Photo produit réelle — centrée, fond blanc, style pub e-commerce."""
    x0, y0, x1, y1 = box
    card_w, card_h = x1 - x0, y1 - y0
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=(255, 255, 255, 255))
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba = Image.alpha_composite(canvas_rgba, overlay)
    canvas.paste(canvas_rgba.convert("RGB"))

    photo = Image.open(photo_path).convert("RGBA")
    pad = 28
    inner_w, inner_h = card_w - 2 * pad, card_h - 2 * pad
    ratio = min(inner_w / photo.width, inner_h / photo.height)
    tw, th = int(photo.width * ratio), int(photo.height * ratio)
    photo = photo.resize((tw, th), Image.Resampling.LANCZOS)
    px = x0 + (card_w - tw) // 2
    py = y0 + (card_h - th) // 2
    if photo.mode == "RGBA":
        canvas.paste(photo, (px, py), photo)
    else:
        canvas.paste(photo.convert("RGB"), (px, py))


def _draw_photo_placeholder(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=(255, 255, 255))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=24, outline=(0, 0, 0), width=2)
    hint_font = _font(26, bold=False)
    lines = ["Photo produit", "uzaapp.com", "→ briefs-createur.md"]
    cy = y0 + (y1 - y0) // 2 - 40
    for line in lines:
        tw = draw.textlength(line, font=hint_font)
        _draw_text_crisp(draw, (x0 + (x1 - x0 - tw) // 2, cy), line, hint_font, (80, 80, 80))
        cy += 34


def render_uzaapp(
    out_path: Path,
    product_name: str,
    price: str,
    headline: str,
    logo_path: Path | None,
    product_photo_path: Path | None = None,
) -> None:
    orange = _hex_to_rgb("#E85D2C")
    teal = _hex_to_rgb("#1A8A8A")
    img = Image.new("RGB", (SIZE, SIZE), orange)
    draw = ImageDraw.Draw(img)

    # Coin teal (comme l'icône app)
    draw.polygon([(SIZE, 0), (SIZE - 280, 0), (SIZE, 280)], fill=teal)
    draw.ellipse([(SIZE - 120, 40), (SIZE - 60, 100)], fill=(255, 255, 255))

    # Séparateur courbe discret
    draw.arc([MARGIN - 40, 120, SIZE - MARGIN + 40, 280], start=200, end=340, fill=(0, 0, 0), width=4)

    # Zone hero : photo produit réelle ou consigne créateur
    hero_box = (MARGIN, 100, SIZE - MARGIN, 500)
    if product_photo_path and product_photo_path.exists():
        _paste_product_photo(img, product_photo_path, hero_box)
        print(f"    Photo produit : {product_photo_path.name}")
    else:
        _draw_photo_placeholder(draw, hero_box)

    product_name = _clean_fr(product_name)
    price = _clean_fr(price) if price else ""
    headline = _clean_fr(headline)
    if price and "$" not in price and "€" not in price and "FC" not in price.upper():
        price_display = f"{price} $"
    else:
        price_display = price
    max_w = SIZE - 2 * MARGIN

    # Nom + prix sous la photo (style pub marketing)
    name_font = _font_fit(draw, product_name, max_w, 44, bold=True, min_size=28)
    lines = _wrap_text(draw, product_name, name_font, max_w)
    y = 520
    y = _draw_multiline(
        draw, MARGIN, y, lines[:2], name_font, (255, 255, 255),
        outline=(0, 0, 0), spacing=4,
    )

    if price_display:
        price_font = _font_fit(draw, price_display, max_w, 64, bold=True, min_size=40)
        _draw_text_crisp(
            draw, (MARGIN, y + 8), price_display, price_font, (255, 255, 255),
            outline=(0, 0, 0), outline_width=2,
        )

    # CTA : nom + prix + uzaapp.com
    if price_display and price_display in headline:
        cta = headline
    elif price_display:
        cta = f"{product_name} — {price_display}"
    else:
        cta = headline or f"Commandez sur uzaapp.com"

    cta_font = _font_fit(draw, cta, max_w - 40, 34, bold=True, min_size=24)
    draw.rounded_rectangle([MARGIN, SIZE - 130, SIZE - MARGIN, SIZE - 60], radius=20, fill=teal)
    cta_lines = _wrap_text(draw, cta, cta_font, max_w - 40)
    cta_text = cta_lines[0]
    tw = draw.textlength(cta_text, font=cta_font)
    _draw_text_crisp(
        draw, ((SIZE - tw) // 2, SIZE - 112), cta_text, cta_font, (255, 255, 255),
    )

    site_font = _font(26, bold=True)
    _draw_text_crisp(draw, (MARGIN, SIZE - 48), "uzaapp.com", site_font, (0, 0, 0))

    _paste_logo(img, logo_path, "bottom-right", 0.18)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def render_investee(
    out_path: Path,
    headline: str,
    subtitle: str,
    logo_path: Path | None,
) -> None:
    teal = _hex_to_rgb("#268FA5")
    img = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, 18, SIZE], fill=teal)
    draw.rectangle([0, 0, SIZE, 8], fill=teal)

    _draw_briefcase_icon(draw, MARGIN + 10, 120, teal)

    headline = _clean_fr(headline)
    subtitle = _clean_fr(subtitle)
    max_w = SIZE - 2 * MARGIN

    title_font = _font_fit(draw, headline, max_w, 48, bold=True, min_size=30)
    lines = _wrap_text(draw, headline, title_font, max_w)
    y = 300
    y = _draw_multiline(draw, MARGIN, y, lines[:3], title_font, teal)

    sub_font = _font(28, bold=False)
    sub_lines = _wrap_text(draw, subtitle, sub_font, max_w)
    _draw_multiline(draw, MARGIN, y + 16, sub_lines[:3], sub_font, (0, 0, 0))

    draw.rounded_rectangle([MARGIN, SIZE - 100, SIZE - MARGIN, SIZE - 40], radius=12, fill=teal)
    site_font = _font(26)
    site = "investee-group.com"
    tw = draw.textlength(site, font=site_font)
    _draw_text_crisp(draw, ((SIZE - tw) // 2, SIZE - 82), site, site_font, (255, 255, 255))

    _paste_logo(img, logo_path, "bottom-right", 0.22)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def render_im_system(
    out_path: Path,
    headline: str,
    subtitle: str,
    logo_path: Path | None,
) -> None:
    blue = _hex_to_rgb("#2196F3")
    navy = _hex_to_rgb("#1A237E")
    light = (227, 242, 253)
    img = Image.new("RGB", (SIZE, SIZE), light)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SIZE, 100], fill=navy)
    headline = _clean_fr(headline)
    subtitle = _clean_fr(subtitle)
    max_w = SIZE - 2 * MARGIN

    brand_font = _font(42)
    _draw_text_crisp(draw, (MARGIN, 28), "IM-SYSTEM", brand_font, (255, 255, 255))

    _draw_dashboard_mock(draw, MARGIN, 140, SIZE - 2 * MARGIN, 340)

    title_font = _font_fit(draw, headline, max_w, 44, bold=True, min_size=30)
    lines = _wrap_text(draw, headline, title_font, max_w)
    y = 510
    y = _draw_multiline(draw, MARGIN, y, lines[:2], title_font, navy)

    sub_font = _font(26, bold=False)
    sub_lines = _wrap_text(draw, subtitle, sub_font, max_w)
    _draw_multiline(draw, MARGIN, y + 8, sub_lines[:2], sub_font, blue)

    draw.rounded_rectangle([MARGIN, SIZE - 96, SIZE - MARGIN, SIZE - 36], radius=14, fill=blue)
    cta_font = _font(28)
    cta = headline if headline and "IM" not in headline.upper()[:10] else "Gérez votre entreprise"
    tw = draw.textlength(cta, font=cta_font)
    _draw_text_crisp(draw, ((SIZE - tw) // 2, SIZE - 78), cta, cta_font, (255, 255, 255))

    _paste_logo(img, logo_path, "bottom-right", 0.20)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def _clean_fr(text: str) -> str:
    """Nettoie le texte : français, sans guillemets parasites ni troncature."""
    text = text.strip().strip("«»\"'")
    text = re.sub(r"\s+", " ", text)
    return text
