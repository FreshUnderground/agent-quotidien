"""Génération automatique des visuels sociaux (Pollinations ou OpenAI DALL-E)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "assets" / "logos"
BRANDS_FILE = ROOT / "assets" / "brands.json"

# Fallback si brands.json absent
BRAND_COLORS = {
    "KAWA_KANZURURU": "black, light blue #5BA3D9, green #4CAF50, cherry red #E53935, brown, white",
    "UZAAPP": "orange-red #E85D2C, teal #1A8A8A, white smiley motif, black accents",
    "INVESTEE_GROUP": "teal cyan #268FA5, black background, growth chart briefcase",
    "IM_SYSTEM": "bright blue #2196F3, dark navy #1A237E, white map pin icon",
}

BRAND_SITES = {
    "KAWA_KANZURURU": "kawakanzururu.com",
    "UZAAPP": "uzaapp.com",
    "INVESTEE_GROUP": "investee-group.com",
    "IM_SYSTEM": "imsystem.investee-group.com",
}

LOGO_KEY_MAP = {
    "KAWA_KANZURURU": "kawa",
    "UZAAPP": "uzaapp",
    "INVESTEE_GROUP": "investee",
    "IM_SYSTEM": "im-system",
}


def _load_brands() -> dict:
    if BRANDS_FILE.exists():
        return json.loads(BRANDS_FILE.read_text(encoding="utf-8"))
    return {}


def _brand_entry(brand_key: str) -> dict:
    brands = _load_brands()
    return brands.get(brand_key, {})


def _brand_palette(brand_key: str) -> str:
    entry = _brand_entry(brand_key)
    if entry:
        return entry.get("palette_text") or entry.get("identity", "")
    return BRAND_COLORS.get(brand_key, "professional, clean")


def _brand_identity(brand_key: str) -> str:
    return _brand_entry(brand_key).get("identity", "")


def _brand_design_rules(brand_key: str) -> dict:
    return _brand_entry(brand_key).get("design_rules", {})


def _hex_palette_list(brand_key: str) -> str:
    """Liste hex officielle pour contraindre l'IA image."""
    entry = _brand_entry(brand_key)
    colors = entry.get("colors", {})
    if colors:
        return ", ".join(colors.values())
    rules = _brand_design_rules(brand_key)
    allowed = rules.get("allowed_colors", [])
    return ", ".join(allowed) if allowed else _brand_palette(brand_key)


def _is_valid_image(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 500:
        return False
    header = path.read_bytes()[:4]
    return header[:2] == b"\xff\xd8" or header[:4] == b"\x89PNG" or header[:4] == b"RIFF"


def _resolve_logo_path(brand_key: str) -> Path | None:
    """Retourne le chemin du logo officiel si le fichier existe."""
    brands = _load_brands()
    base = LOGO_KEY_MAP.get(brand_key, brand_key.lower())
    candidates: list[str] = []
    if brand_key in brands:
        candidates.append(brands[brand_key].get("logo_file", ""))
    candidates.extend(
        [f"{base}.png", f"{base}.jpg", f"{base}.jpeg", f"{base}.webp"]
    )
    for name in candidates:
        if not name:
            continue
        path = LOGOS_DIR / name
        if _is_valid_image(path):
            return path
    return None


def apply_logo_overlay(brand_key: str, out_path: Path) -> bool:
    """Superpose le logo officiel en bas à droite (nécessite Pillow)."""
    logo_path = _resolve_logo_path(brand_key)
    if not logo_path or not out_path.exists():
        return False
    try:
        from PIL import Image
    except ImportError:
        print(f"  Logo non appliqué ({brand_key}) : Pillow absent — pip install Pillow")
        return False

    base = Image.open(out_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    target_w = int(base.width * 0.22)
    ratio = target_w / logo.width
    target_h = int(logo.height * ratio)
    logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

    margin = int(base.width * 0.04)
    x = base.width - target_w - margin
    y = base.height - target_h - margin

    # Fond semi-transparent derrière le logo — adapté à la marque
    pad = 8
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    from PIL import ImageDraw

    pad_colors = {
        "UZAAPP": (232, 93, 44, 220),
        "INVESTEE_GROUP": (255, 255, 255, 230),
        "IM_SYSTEM": (255, 255, 255, 230),
    }
    pad_fill = pad_colors.get(brand_key, (255, 255, 255, 200))

    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        [x - pad, y - pad, x + target_w + pad, y + target_h + pad],
        radius=12,
        fill=pad_fill,
    )
    base = Image.alpha_composite(base, overlay)
    base.paste(logo, (x, y), logo)
    base.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  Logo appliqué : {logo_path.name} → {out_path.name}")
    return True


@dataclass
class ImageBrief:
    key: str
    filename: str
    prompt: str
    alt_text: str


def _extract_field(content: str, label: str) -> str:
    pattern = rf"\*\*{re.escape(label)}:\*\*\s*(.+)"
    match = re.search(pattern, content, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_products(content: str) -> list[str]:
    names: list[str] = []
    for match in re.finditer(r"-\s*\*\*Nom\s*:\*\*\s*(.+)", content, re.IGNORECASE):
        name = match.group(1).strip()
        if name and name not in names:
            names.append(name)
    return names[:2]


def _extract_image_subject(content: str) -> str:
    block = re.search(
        r"###\s*Image à réaliser aujourd'hui\s*(.*?)(?=\n###|\n## |\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not block:
        return _extract_field(content, "Sujet")
    section = block.group(1)
    return _extract_field(section, "Sujet") or _extract_field(section, "Type visuel")


def _extract_overlay_text(content: str) -> str:
    block = re.search(
        r"###\s*Image à réaliser aujourd'hui\s*(.*?)(?=\n###|\n## |\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if block:
        text = _extract_field(block.group(1), "Texte sur l'image")
        if not text:
            text = _extract_field(block.group(1), "Texte sur visuel")
        if text:
            return text
    accroche = _extract_field(content, "Texte accroche")
    return accroche


def investee_focus(day: int | None = None) -> str:
    """Alterne entreprise (jour impair) et IM-SYSTEM (jour pair)."""
    d = day if day is not None else datetime.now().day
    return "im-system" if d % 2 == 0 else "entreprise"


def _build_prompt(
    brand_key: str,
    subject: str,
    overlay: str,
    extra: str = "",
) -> str:
    """Brief créatif niveau directeur artistique — charte graphique stricte."""
    rules = _brand_design_rules(brand_key)
    identity = _brand_identity(brand_key)
    site = BRAND_SITES.get(brand_key, "")
    hex_colors = _hex_palette_list(brand_key)
    max_colors = rules.get("max_colors", 4)
    style = rules.get("style", "clean professional brand design")
    background = rules.get("background", "clean minimal background")
    typography = rules.get("typography", "bold sans-serif, legible hierarchy")
    composition = rules.get("composition", "balanced layout with whitespace")
    mood = rules.get("mood", "professional branded")
    forbidden = rules.get("forbidden", ["rainbow", "random multicolor", "neon", "clipart"])
    forbidden_str = ", ".join(forbidden[:8])

    overlay_part = (
        f'Text overlay in French, short and bold: "{overlay[:80]}". '
        if overlay
        else ""
    )
    site_part = f"Small discreet URL: {site}. " if site else ""
    identity_part = f"Brand: {identity}. " if identity else ""

    return (
        f"Expert graphic design, social media post 1080x1080, {brand_key.replace('_', ' ')}. "
        f"Subject: {subject}. {extra}{identity_part}"
        f"DESIGN DIRECTOR BRIEF — follow brand guidelines EXACTLY. "
        f"Style: {style}. Mood: {mood}. "
        f"COLOR DISCIPLINE: use ONLY {max_colors} colors maximum from this official palette: {hex_colors}. "
        f"Background: {background}. Typography: {typography}. Layout: {composition}. "
        f"{overlay_part}{site_part}"
        f"STRICTLY FORBIDDEN: {forbidden_str}, any color outside the palette, "
        f"stock photo look, watermark, logo in image (logo added separately). "
        f"Flat or subtle gradient within same hue family only. "
        f"High-end corporate/agency quality, cohesive single-brand look. "
        f"Leave bottom-right corner empty and light for logo placement."
    )


def build_briefs_from_sections(sections: list, date_str: str | None = None) -> list[ImageBrief]:
    """Construit les briefs image à partir des sections du briefing."""
    date_slug = date_str or datetime.now().strftime("%Y-%m-%d")
    day = datetime.strptime(date_slug, "%Y-%m-%d").day if date_str else datetime.now().day
    briefs: list[ImageBrief] = []

    section_map = {s.key: s.content for s in sections}

    # Kawa — 1 visuel
    if "KAWA_KANZURURU" in section_map:
        content = section_map["KAWA_KANZURURU"]
        subject = _extract_image_subject(content) or (
            "Coffee harvest season, red cherries in farmer hands, Rwenzori mountains"
        )
        overlay = _extract_overlay_text(content) or "Kawa Kanzururu — Café blanc comme la neige"
        briefs.append(
            ImageBrief(
                key="KAWA_KANZURURU",
                filename=f"{date_slug}-kawa.png",
                prompt=_build_prompt("KAWA_KANZURURU", subject, overlay),
                alt_text=f"Visuel Kawa Kanzururu — {overlay}",
            )
        )

    # UZAAPP — 2 visuels (produits)
    if "UZAAPP" in section_map:
        content = section_map["UZAAPP"]
        products = _extract_products(content)
        if not products:
            products = ["Accessoire tech tendance", "Produit e-commerce populaire RDC"]
        for i, product in enumerate(products[:2], start=1):
            overlay = f"{product} — Commandez sur uzaapp.com"
            briefs.append(
                ImageBrief(
                    key="UZAAPP",
                    filename=f"{date_slug}-uzaapp-produit{i}.png",
                    prompt=_build_prompt(
                        "UZAAPP",
                        f"E-commerce product hero shot: {product}",
                        overlay,
                        "Modern mobile marketplace Congo DRC. ",
                    ),
                    alt_text=f"Visuel UZAAPP — {product}",
                )
            )

    # INVESTEE — 1 visuel (alternance entreprise / IM-SYSTEM)
    if "INVESTEE_GROUP" in section_map:
        content = section_map["INVESTEE_GROUP"]
        focus = investee_focus(day)
        if focus == "im-system":
            subject = _extract_image_subject(content) or (
                "Software dashboard for business management: inventory, invoicing, accounting"
            )
            overlay = _extract_overlay_text(content) or "IM-SYSTEM — Gérez votre entreprise"
            briefs.append(
                ImageBrief(
                    key="IM_SYSTEM",
                    filename=f"{date_slug}-investee-im-system.png",
                    prompt=_build_prompt("IM_SYSTEM", subject, overlay, "B2B SaaS product. "),
                    alt_text="Visuel IM-SYSTEM par INVESTEE-GROUP",
                )
            )
        else:
            subject = _extract_image_subject(content) or (
                "IT company team in Butembo: cybersecurity, helpdesk, digital solutions"
            )
            overlay = _extract_overlay_text(content) or "INVESTEE-GROUP — Solutions NTIC"
            briefs.append(
                ImageBrief(
                    key="INVESTEE_GROUP",
                    filename=f"{date_slug}-investee-entreprise.png",
                    prompt=_build_prompt("INVESTEE_GROUP", subject, overlay),
                    alt_text="Visuel INVESTEE-GROUP entreprise",
                )
            )

    return briefs


def _generate_pollinations(prompt: str, out_path: Path, seed: int) -> None:
    encoded = urllib.parse.quote(prompt[:800])
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1080&height=1080&seed={seed}&nologo=true&enhance=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "agent-quotidien/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    if len(data) < 1000:
        raise RuntimeError("Image Pollinations trop petite ou invalide")
    out_path.write_bytes(data)


def _generate_openai(prompt: str, out_path: Path, api_key: str) -> None:
    payload = json.dumps(
        {
            "model": "dall-e-3",
            "prompt": prompt[:4000],
            "size": "1024x1024",
            "quality": "standard",
            "n": 1,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    image_url = data["data"][0]["url"]
    with urllib.request.urlopen(image_url, timeout=60) as img_resp:
        out_path.write_bytes(img_resp.read())


def generate_image(brief: ImageBrief, out_path: Path, seed: int = 42) -> None:
    provider = os.environ.get("IMAGE_PROVIDER", "pollinations").strip().lower()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            if provider == "openai" and openai_key:
                _generate_openai(brief.prompt, out_path, openai_key)
            else:
                _generate_pollinations(brief.prompt, out_path, seed + attempt)
            print(f"  Image OK : {out_path.name}")
            return
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, TimeoutError) as e:
            last_error = e
            print(f"  Tentative {attempt + 1}/3 échouée ({brief.filename}) : {e}")
            time.sleep(5 * (attempt + 1))

    raise RuntimeError(f"Échec génération {brief.filename} : {last_error}") from last_error


def generate_daily_images(
    sections: list,
    date_str: str | None = None,
) -> list[Path]:
    """Génère tous les visuels du jour. Retourne les chemins des PNG créés."""
    date_slug = date_str or datetime.now().strftime("%Y-%m-%d")
    out_dir = ROOT / "output" / "images" / date_slug
    briefs = build_briefs_from_sections(sections, date_slug)

    if not briefs:
        print("Aucun brief image à générer.")
        return []

    provider = os.environ.get("IMAGE_PROVIDER", "pollinations")
    generate_flag = os.environ.get("GENERATE_IMAGES", "true").lower() == "true"
    if not generate_flag:
        print("GENERATE_IMAGES=false — visuels ignorés.")
        return []

    print(f"Génération de {len(briefs)} visuel(s) via {provider}…")
    paths: list[Path] = []
    for i, brief in enumerate(briefs):
        out_path = out_dir / brief.filename
        try:
            generate_image(brief, out_path, seed=1000 + i)
            apply_logo_overlay(brief.key, out_path)
            paths.append(out_path)
        except Exception as e:
            print(f"  AVERTISSEMENT : {brief.filename} — {e}")

    # Sauvegarder le manifeste
    manifest = out_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {"file": p.name, "brief": b.alt_text, "key": b.key}
                for p, b in zip(paths, briefs[: len(paths)])
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return paths
