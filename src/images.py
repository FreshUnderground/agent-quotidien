"""Génération des visuels sociaux — templates graphiques Pillow (texte FR net, sans IA photo)."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGOS_DIR = ROOT / "assets" / "logos"
BRANDS_FILE = ROOT / "assets" / "brands.json"

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


def _is_valid_image(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 500:
        return False
    header = path.read_bytes()[:4]
    return header[:2] == b"\xff\xd8" or header[:4] == b"\x89PNG" or header[:4] == b"RIFF"


def _resolve_logo_path(brand_key: str) -> Path | None:
    brands = _load_brands()
    base = LOGO_KEY_MAP.get(brand_key, brand_key.lower())
    candidates: list[str] = []
    if brand_key in brands:
        candidates.append(brands[brand_key].get("logo_file", ""))
    candidates.extend([f"{base}.png", f"{base}.jpg", f"{base}.jpeg", f"{base}.webp"])
    for name in candidates:
        if not name:
            continue
        path = LOGOS_DIR / name
        if _is_valid_image(path):
            return path
    return None


@dataclass
class ImageBrief:
    key: str
    filename: str
    headline: str
    subtitle: str
    product_name: str = ""
    price: str = ""
    alt_text: str = ""
    product_image_url: str = ""


def _extract_field(content: str, label: str) -> str:
    """Extrait une valeur après **Label :** (avec ou sans puce, parenthèses optionnelles)."""
    patterns = [
        rf"(?:^|\n)\s*[-*]?\s*\*\*{re.escape(label)}(?:\s*\([^)]*\))?\s*:\*\*\s*(.+)",
        rf"\*\*{re.escape(label)}(?:\s*\([^)]*\))?\s*:\*\*\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            val = match.group(1).strip().strip("«»\"'")
            return val.split("\n")[0].strip()
    return ""


def _extract_image_block(content: str) -> str:
    block = re.search(
        r"###\s*(?:Image à réaliser(?:\s+aujourd'hui)?|Visuel à créer|Fiche créative(?:\s+Produit\s+\d+)?)"
        r"\s*(.*?)(?=\n###|\n## |\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    return block.group(1) if block else ""


def _extract_image_subject(content: str) -> str:
    section = _extract_image_block(content)
    if section:
        return _extract_field(section, "Sujet") or _extract_field(section, "Type visuel")
    return _extract_field(content, "Sujet")


def _extract_overlay_text(content: str) -> str:
    for label in (
        "Texte sur l'image",
        "Texte sur visuel",
        "Texte accroche",
        "Message visuel",
    ):
        section = _extract_image_block(content)
        if section:
            text = _extract_field(section, label)
            if text:
                return text
        text = _extract_field(content, label)
        if text:
            return text
    return ""


def _product_block_core(block: str) -> str:
    """Limite le bloc au produit seul (sans fiches créatives suivantes)."""
    nested = re.search(r"\n###\s+(?!Produit\s+\d)", block, re.IGNORECASE)
    return block[: nested.start()] if nested else block


def _normalize_product_image_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        return ""
    if "storage.googleapis.com" in url and "uzaapp.com/api/proxy" not in url:
        return "https://uzaapp.com/api/proxy.php?url=" + urllib.parse.quote(url, safe="")
    return url


def _download_product_image(url: str, cache_path: Path) -> Path | None:
    url = _normalize_product_image_url(url)
    if not url:
        return None
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and cache_path.stat().st_size > 500:
        return cache_path
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; agent-quotidien/1.0)",
                "Accept": "image/*,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
        if len(data) < 500:
            return None
        cache_path.write_bytes(data)
        return cache_path if _is_valid_image(cache_path) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def _extract_uzaapp_accroche(content: str, product_num: int) -> str:
    fiche = re.search(
        rf"###\s*Fiche créative\s+Produit\s+{product_num}\s*(.*?)(?=\n###|\n## |\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if fiche:
        return _extract_field(fiche.group(0), "Texte accroche")
    return ""


def _extract_products(content: str) -> list[dict[str, str]]:
    """Extrait nom + prix exacts de chaque produit UZAAPP du briefing (source uzaapp.com)."""
    products: list[dict[str, str]] = []
    blocks = re.split(r"(?=###\s*Produit\s+\d+)", content, flags=re.IGNORECASE)
    for block in blocks:
        num_match = re.search(r"###\s*Produit\s+(\d+)", block, re.IGNORECASE)
        if not num_match:
            continue
        product_num = int(num_match.group(1))
        core = _product_block_core(block)
        name = _extract_field(core, "Nom")
        if not name:
            continue
        price = _extract_field(core, "Prix indicatif") or _extract_field(core, "Prix")
        image_url = (
            _extract_field(core, "URL image produit")
            or _extract_field(core, "Image produit")
            or _extract_field(core, "URL image")
        )
        accroche = (
            _extract_field(core, "Texte accroche")
            or _extract_uzaapp_accroche(content, product_num)
        )
        products.append({
            "name": name,
            "price": price,
            "accroche": accroche,
            "image_url": image_url,
        })
        if len(products) >= 2:
            break

    if not products:
        for match in re.finditer(r"-\s*\*\*Nom\s*:\*\*\s*(.+)", content, re.IGNORECASE):
            name = match.group(1).strip().strip("«»\"'")
            start = match.start()
            chunk = content[start : start + 600]
            price = _extract_field(chunk, "Prix indicatif") or _extract_field(chunk, "Prix")
            image_url = (
                _extract_field(chunk, "URL image produit")
                or _extract_field(chunk, "Image produit")
            )
            products.append({
                "name": name,
                "price": price,
                "accroche": "",
                "image_url": image_url,
            })
            if len(products) >= 2:
                break
    return products


def investee_focus(day: int | None = None) -> str:
    d = day if day is not None else datetime.now().day
    return "im-system" if d % 2 == 0 else "entreprise"


def build_briefs_from_sections(sections: list, date_str: str | None = None) -> list[ImageBrief]:
    date_slug = date_str or datetime.now().strftime("%Y-%m-%d")
    day = datetime.strptime(date_slug, "%Y-%m-%d").day if date_str else datetime.now().day
    briefs: list[ImageBrief] = []
    section_map = {s.key: s.content for s in sections}

    if "KAWA_KANZURURU" in section_map:
        content = section_map["KAWA_KANZURURU"]
        subject = _extract_image_subject(content) or "Récolte arabica Fairtrade au Rwenzori"
        headline = _extract_overlay_text(content) or "Café des neiges éternelles"
        briefs.append(
            ImageBrief(
                key="KAWA_KANZURURU",
                filename=f"{date_slug}-kawa.png",
                headline=headline,
                subtitle=subject,
                alt_text=f"Kawa Kanzururu — {headline}",
            )
        )

    if "UZAAPP" in section_map:
        content = section_map["UZAAPP"]
        products = _extract_products(content)
        if not products:
            products = [{"name": "Produit UZAAPP", "price": "", "accroche": "", "image_url": ""}]
        for i, prod in enumerate(products[:2], start=1):
            name = prod["name"]
            price = prod["price"]
            image_url = prod.get("image_url", "")
            accroche = prod.get("accroche") or ""
            if not accroche and price:
                accroche = f"{name} — {price} $"
            elif not accroche:
                accroche = name
            briefs.append(
                ImageBrief(
                    key="UZAAPP",
                    filename=f"{date_slug}-uzaapp-produit{i}.png",
                    headline=accroche,
                    subtitle=name,
                    product_name=name,
                    price=price,
                    product_image_url=image_url,
                    alt_text=f"UZAAPP — {name}",
                )
            )

    if "INVESTEE_GROUP" in section_map:
        content = section_map["INVESTEE_GROUP"]
        focus = investee_focus(day)
        subject = _extract_image_subject(content) or "Solutions NTIC pour entreprises"
        headline = _extract_overlay_text(content) or subject
        if focus == "im-system":
            briefs.append(
                ImageBrief(
                    key="IM_SYSTEM",
                    filename=f"{date_slug}-investee-im-system.png",
                    headline=headline if "IM" in headline.upper() else "IM-SYSTEM — Gérez votre entreprise",
                    subtitle=subject,
                    alt_text="IM-SYSTEM par INVESTEE-GROUP",
                )
            )
        else:
            briefs.append(
                ImageBrief(
                    key="INVESTEE_GROUP",
                    filename=f"{date_slug}-investee-entreprise.png",
                    headline=headline,
                    subtitle=subject,
                    alt_text="INVESTEE-GROUP",
                )
            )

    return briefs


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    return slug[:40] or "produit"


def _resolve_product_photo(brief: ImageBrief, date_slug: str) -> Path | None:
    if not brief.product_image_url:
        return None
    ext = ".jpg"
    if re.search(r"\.png", brief.product_image_url, re.I):
        ext = ".png"
    elif re.search(r"\.webp", brief.product_image_url, re.I):
        ext = ".webp"
    cache = ROOT / "output" / "images" / date_slug / "products" / f"{_slugify(brief.product_name)}{ext}"
    return _download_product_image(brief.product_image_url, cache)


def _render_template(brief: ImageBrief, out_path: Path, date_slug: str = "") -> None:
    from visual_templates import (
        render_im_system,
        render_investee,
        render_kawa,
        render_uzaapp,
    )

    logo = _resolve_logo_path(brief.key)
    if brief.key == "KAWA_KANZURURU":
        render_kawa(out_path, brief.headline, brief.subtitle, logo)
    elif brief.key == "UZAAPP":
        product_photo = _resolve_product_photo(brief, date_slug) if date_slug else None
        render_uzaapp(
            out_path,
            brief.product_name or brief.subtitle,
            brief.price,
            brief.headline,
            logo,
            product_photo,
        )
    elif brief.key == "IM_SYSTEM":
        render_im_system(out_path, brief.headline, brief.subtitle, logo)
    elif brief.key == "INVESTEE_GROUP":
        render_investee(out_path, brief.headline, brief.subtitle, logo)
    else:
        raise ValueError(f"Marque inconnue : {brief.key}")
    print(f"  Template OK : {out_path.name}")


def generate_image(brief: ImageBrief, out_path: Path, seed: int = 42) -> None:
    """Génère un visuel graphique (Pillow). Pas de photo IA — pas de corps humains."""
    provider = os.environ.get("IMAGE_PROVIDER", "template").strip().lower()
    if provider in ("pollinations", "openai"):
        print(
            f"  AVERTISSEMENT : IMAGE_PROVIDER={provider} ignoré "
            "(IA photo désactivée : mains/corps flous ou dupliqués). Template pro utilisé."
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    date_slug = out_path.parent.name
    _render_template(brief, out_path, date_slug)


def generate_daily_images(
    sections: list,
    date_str: str | None = None,
) -> list[Path]:
    date_slug = date_str or datetime.now().strftime("%Y-%m-%d")
    out_dir = ROOT / "output" / "images" / date_slug
    briefs = build_briefs_from_sections(sections, date_slug)

    if not briefs:
        print("Aucun brief image à générer.")
        return []

    if os.environ.get("GENERATE_IMAGES", "true").lower() != "true":
        print("GENERATE_IMAGES=false — visuels ignorés.")
        return []

    print(f"Génération de {len(briefs)} visuel(s) marketing…")
    paths: list[Path] = []
    for i, brief in enumerate(briefs):
        out_path = out_dir / brief.filename
        try:
            generate_image(brief, out_path, seed=1000 + i)
            paths.append(out_path)
            if brief.key == "UZAAPP" and not brief.product_image_url:
                print(f"  INFO {brief.filename} : ajoutez **URL image produit** (uzaapp.com) pour la photo réelle")
        except Exception as e:
            print(f"  AVERTISSEMENT : {brief.filename} — {e}")

    try:
        from creative_briefs import generate_creative_briefs

        generate_creative_briefs(sections, date_slug)
    except Exception as e:
        print(f"  AVERTISSEMENT briefs créateur : {e}")

    manifest = out_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "file": p.name,
                    "brief": b.alt_text,
                    "key": b.key,
                    "headline": b.headline,
                    "product": b.product_name,
                    "price": b.price,
                    "product_image_url": b.product_image_url,
                }
                for p, b in zip(paths, briefs[: len(paths)])
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return paths
