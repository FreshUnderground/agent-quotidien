"""Briefs créateur — orientations pour visuels marketing réalistes (Canva, terrain, uzaapp.com)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from images import (
    BRAND_SITES,
    _extract_image_subject,
    _extract_overlay_text,
    _extract_products,
    investee_focus,
)

ROOT = Path(__file__).resolve().parent.parent

UZAAPP_COLORS = "orange #E85D2C, teal #1A8A8A, blanc, noir"
KAWA_COLORS = "bleu #5BA3D9, vert #4CAF50, rouge #E53935, brun #5D4037"
INVESTEE_COLORS = "teal #268FA5, noir, blanc"
IM_COLORS = "bleu #2196F3, navy #1A237E, blanc"


def _section_map(sections: list) -> dict[str, str]:
    return {s.key: s.content for s in sections}


def _uzaapp_product_brief(prod: dict[str, str], num: int) -> str:
    name = prod.get("name", "Produit")
    price = prod.get("price", "")
    image_url = prod.get("image_url", "")
    accroche = prod.get("accroche") or (f"{name} — {price} $" if price else name)
    price_line = f"{price} $" if price and "$" not in price else price

    photo_block = (
        f"1. Ouvrir [uzaapp.com](https://uzaapp.com) → rechercher « {name} »\n"
        f"2. Clic droit sur la photo produit → « Copier l'adresse de l'image »\n"
        f"3. Coller l'URL dans le briefing (`**URL image produit :**`)"
    )
    if image_url:
        photo_block = f"**URL image (catalogue) :** {image_url}\n(Capture ou import directe dans Canva)"

    return f"""### UZAAPP — Produit {num} : {name}

**Format :** 1080×1080 (Instagram/Facebook) ou 1080×1920 (story)

**Objectif :** Pub e-commerce réaliste — le produit doit être **visible et net** (pas une icône).

**Photo produit :**
{photo_block}

**Texte sur le visuel :** {accroche}

**Mise en page recommandée (Canva / Photoshop) :**
- Zone haute (60 %) : **photo réelle du produit** sur fond blanc ou dégradé léger orange pâle
- Bandeau bas orange `{UZAAPP_COLORS.split(',')[0]}` : nom + **prix {price_line}** en gros blanc
- Coin haut droit : accent teal #1A8A8A (comme l'icône UZAAPP)
- Bas : « Commandez sur **uzaapp.com** » + logo UZAAPP
- **Ne pas** utiliser d'IA pour générer le produit — photo catalogue ou prise studio

**Réseaux :** Facebook (carré), TikTok (vertical avec prix en 3 premières secondes)
"""


def _kawa_brief(headline: str, subject: str) -> str:
    return f"""### Kawa Kanzururu

**Format :** 1080×1080 ou 1080×1920 (story)

**Objectif :** Marketing authentique café Fairtrade — **photo terrain de préférence**.

**Texte sur le visuel :** {headline}

**Sujet / angle :** {subject}

**À photographier sur place (réaliste) :**
- Mains triant des cerises rouges à la MSL (cadrage serré, lumière naturelle)
- Paysage Rwenzori + caféiers
- Sacs / étiquettes Fairtrade

**Si pas de photo dispo aujourd'hui :** graphique charte ({KAWA_COLORS}) + texte ci-dessus — **sans personnes IA**.

**Éviter :** images IA avec visages/mains flous, couleurs hors charte
"""


def _investee_brief(headline: str, subject: str, focus: str) -> str:
    if focus == "im-system":
        return f"""### IM-SYSTEM

**Format :** 1080×1080 ou 1200×627 (LinkedIn)

**Objectif :** Marketing SaaS B2B — **capture d'écran réelle** du tableau de bord IM-SYSTEM.

**Texte sur le visuel :** {headline}

**Visuel réaliste :**
- Screenshot app (factures, stock, tableau de bord) — flouer données sensibles
- Ou mockup téléphone avec vraie interface IM-SYSTEM

**Charte :** {IM_COLORS}

**Éviter :** UI multicolore inventée, photos IA d'équipes
"""
    return f"""### INVESTEE-GROUP

**Format :** 1200×627 (LinkedIn) ou 1080×1080

**Objectif :** Crédibilité B2B NTIC Butembo — photo réelle ou visuel corporate sobre.

**Texte sur le visuel :** {headline}

**Message :** {subject}

**Visuels réalistes possibles :**
- Équipe au bureau / formation (photo réelle)
- Serveurs, câblage, audit sécurité (sans données clients)
- Logo + chiffres clés (clients formés, années d'expérience)

**Charte :** {INVESTEE_COLORS} — monochrome strict
"""


def generate_creative_briefs(sections: list, date_str: str | None = None) -> Path:
    """Écrit le guide créateur pour concevoir les vrais visuels marketing."""
    date_slug = date_str or datetime.now().strftime("%Y-%m-%d")
    out_dir = ROOT / "output" / "images" / date_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "briefs-createur.md"

    section_map = _section_map(sections)
    day = datetime.strptime(date_slug, "%Y-%m-%d").day if date_str else datetime.now().day
    parts = [
        f"# Briefs créateur — visuels marketing réalistes\n",
        f"**Date :** {date_slug}\n",
        "## Comment utiliser ce document\n",
        "Les fichiers `.png` auto-générés sont des **ébauches** (texte + charte). "
        "Pour un rendu **marketing professionnel**, suivez ces briefs dans **Canva**, "
        "**Photoshop** ou avec une **photo terrain**.\n",
        "**UZAAPP :** toujours la **vraie photo produit** depuis [uzaapp.com](https://uzaapp.com).\n",
        "**Kawa :** privilégier photos terrain (MSL, cerises, Rwenzori).\n",
        "**INVESTEE :** screenshots réels ou photos bureau.\n",
        "---\n",
    ]

    if "UZAAPP" in section_map:
        products = _extract_products(section_map["UZAAPP"])
        parts.append("## UZAAPP\n")
        if products:
            for i, prod in enumerate(products[:2], start=1):
                parts.append(_uzaapp_product_brief(prod, i))
        else:
            parts.append("_Aucun produit extrait — compléter depuis uzaapp.com_\n")

    if "KAWA_KANZURURU" in section_map:
        content = section_map["KAWA_KANZURURU"]
        parts.append(_kawa_brief(
            _extract_overlay_text(content) or "Café des neiges éternelles",
            _extract_image_subject(content) or "Café Fairtrade Rwenzori",
        ))

    if "INVESTEE_GROUP" in section_map:
        content = section_map["INVESTEE_GROUP"]
        parts.append(_investee_brief(
            _extract_overlay_text(content) or "INVESTEE-GROUP",
            _extract_image_subject(content) or "Solutions NTIC",
            investee_focus(day),
        ))

    parts.append(f"""
---

## Checklist avant publication

- [ ] Photo produit **nette** (UZAAPP) ou photo terrain (Kawa)
- [ ] Prix et nom **exactement** comme sur uzaapp.com
- [ ] Texte lisible sur mobile (test à 15 cm)
- [ ] Logo marque visible
- [ ] Lien site en légende : {', '.join(BRAND_SITES.values())}

*Ébauches auto : `output/images/{date_slug}/*.png`*
""")

    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"  Briefs créateur : {out_path.name}")
    return out_path
