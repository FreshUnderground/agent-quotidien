"""Génération des visuels sociaux — templates professionnels (défaut) ou IA optionnelle."""

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
    prompt: str = ""  # utilisé seulement si IMAGE_PROVIDER=openai|pollinations


def _extract_field(content: str, label: str) -> str:
    pattern = rf"\*\*{re.escape(label)}:\*\*\s*(.+)"
    match = re.search(pattern, content, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_image_block(content: str) -> str:
    block = re.search(
        r"###\s*Image à réaliser aujourd'hui\s*(.*?)(?=\n###|\n## |\Z)",
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
    section = _extract_image_block(content)
    if section:
        for label in ("Texte sur l'image", "Texte sur visuel", "Texte accroche"):
            text = _extract_field(section, label)
            if text:
                return text
    return _extract_field(content, "Texte accroche")


def _extract_products(content: str) -> list[dict[str, str]]:
    """Extrait nom + prix exacts de chaque produit UZAAPP du briefing."""
    products: list[dict[str, str]] = []
    blocks = re.split(r"(?=###\s*Produit\s+\d+)", content, flags=re.IGNORECASE)
    for block in blocks:
        if not re.search(r"###\s*Produit\s+\d+", block, re.IGNORECASE):
            continue
        name = _extract_field(block, "Nom")
        if not name:
            continue
        price = _extract_field(block, "Prix indicatif")
        accroche = _extract_field(block, "Texte accroche")
        if not accroche and "Fiche créative" in content:
            fiche = re.search(
                rf"###\s*Fiche créative.*?(?=###|\Z)",
                content,
                re.DOTALL | re.IGNORECASE,
            )
            if fiche:
                accroche = _extract_field(fiche.group(0), "Texte accroche")
        products.append({"name": name, "price": price, "accroche": accroche})
        if len(products) >= 2:
            break

    if not products:
        for match in re.finditer(r"-\s*\*\*Nom\s*:\*\*\s*(.+)", content, re.IGNORECASE):
            name = match.group(1).strip()
            start = match.start()
            chunk = content[start : start + 500]
            price = _extract_field(chunk, "Prix indicatif")
            products.append({"name": name, "price": price, "accroche": ""})
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
            products = [{"name": "Produit UZAAPP", "price": "", "accroche": ""}]
        for i, prod in enumerate(products[:2], start=1):
            name = prod["name"]
            price = prod["price"]
            accroche = prod.get("accroche") or f"{name} — sur UZAAPP"
            briefs.append(
                ImageBrief(
                    key="UZAAPP",
                    filename=f"{date_slug}-uzaapp-produit{i}.png",
                    headline=accroche,
                    subtitle=name,
                    product_name=name,
                    price=price,
                    alt_text=f"UZAAPP — {name}",
                )
            )

    if "INVESTEE_GROUP" in section_map:
        content = section_map["INVESTEE_GROUP"]
        focus = investee_focus(day)
        subject = _extract_image_subject(content) or "Solutions NTIC pour entreprises"
        headline = _extract_overlay_text(content) or "INVESTEE-GROUP"
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


def _render_template(brief: ImageBrief, out_path: Path) -> None:
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
        render_uzaapp(
            out_path,
            brief.product_name or brief.subtitle,
            brief.price,
            brief.headline,
            logo,
        )
    elif brief.key == "IM_SYSTEM":
        render_im_system(out_path, brief.headline, brief.subtitle, logo)
    elif brief.key == "INVESTEE_GROUP":
        render_investee(out_path, brief.headline, brief.subtitle, logo)
    else:
        raise ValueError(f"Marque inconnue : {brief.key}")
    print(f"  Template OK : {out_path.name}")


def _generate_pollinations(prompt: str, out_path: Path, seed: int) -> None:
    encoded = urllib.parse.quote(prompt[:800])
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1080&height=1080&seed={seed}&nologo=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "agent-quotidien/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    if len(data) < 1000:
        raise RuntimeError("Image Pollinations invalide")
    out_path.write_bytes(data)


def generate_image(brief: ImageBrief, out_path: Path, seed: int = 42) -> None:
    provider = os.environ.get("IMAGE_PROVIDER", "template").strip().lower()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if provider == "template":
        _render_template(brief, out_path)
        return

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            if provider == "openai" and openai_key and brief.prompt:
                _generate_openai_legacy(brief.prompt, out_path, openai_key)
            elif brief.prompt:
                _generate_pollinations(brief.prompt, out_path, seed + attempt)
            else:
                _render_template(brief, out_path)
                return
            print(f"  Image IA OK : {out_path.name}")
            return
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, TimeoutError) as e:
            last_error = e
            print(f"  IA échouée ({attempt + 1}/3), fallback template…")
            try:
                _render_template(brief, out_path)
                return
            except Exception:
                time.sleep(3)

    raise RuntimeError(f"Échec {brief.filename} : {last_error}")


def _generate_openai_legacy(prompt: str, out_path: Path, api_key: str) -> None:
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

    provider = os.environ.get("IMAGE_PROVIDER", "template")
    print(f"Génération de {len(briefs)} visuel(s) pro via {provider}…")
    paths: list[Path] = []
    for i, brief in enumerate(briefs):
        out_path = out_dir / brief.filename
        try:
            generate_image(brief, out_path, seed=1000 + i)
            paths.append(out_path)
        except Exception as e:
            print(f"  AVERTISSEMENT : {brief.filename} — {e}")

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
                }
                for p, b in zip(paths, briefs[: len(paths)])
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return paths
