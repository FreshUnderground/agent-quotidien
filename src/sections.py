"""Validation et complétion des 4 sections du briefing."""

from __future__ import annotations

from pathlib import Path

from notify import MARKER_PATTERN, SECTION_META, BriefingSection, parse_sections

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = {
    "KAWA_KANZURURU": ROOT / "prompts" / "section-kawa.md",
    "UZAAPP": ROOT / "prompts" / "section-uzaapp.md",
    "INVESTEE_GROUP": ROOT / "prompts" / "section-investee.md",
    "APPELS_OFFRES": ROOT / "prompts" / "section-ao.md",
}
REQUIRED_ORDER = ["KAWA_KANZURURU", "UZAAPP", "INVESTEE_GROUP", "APPELS_OFFRES"]


def merge_sections(sections: list[BriefingSection]) -> list[BriefingSection]:
    """Fusionne par clé, garde l'ordre standard des 4 marques."""
    by_key: dict[str, BriefingSection] = {}
    for s in sections:
        if s.key in SECTION_META and s.key not in by_key:
            by_key[s.key] = s
    return [by_key[k] for k in REQUIRED_ORDER if k in by_key]


def missing_keys(sections: list[BriefingSection]) -> list[str]:
    present = {s.key for s in sections}
    return [k for k in REQUIRED_ORDER if k not in present]


def load_section_prompt(key: str) -> str:
    path = PROMPTS[key]
    return path.read_text(encoding="utf-8")


def ensure_all_sections(
    full_text: str,
    api_key: str,
    run_cloud_fn,
) -> list[BriefingSection]:
    """
    Parse le briefing et génère les sections manquantes via l'API Cursor.
    run_cloud_fn(prompt, api_key) -> str
    """
    sections = merge_sections(parse_sections(full_text))
    missing = missing_keys(sections)

    if not missing:
        print(f"Toutes les sections présentes : {len(sections)}/4")
        return sections

    print(f"Sections manquantes : {', '.join(missing)} — génération complémentaire…")

    for key in missing:
        prompt = load_section_prompt(key)
        try:
            extra = run_cloud_fn(prompt, api_key)
            extra_sections = merge_sections(parse_sections(extra))
            for s in extra_sections:
                if s.key == key:
                    sections.append(s)
                    print(f"  + Section {key} générée")
                    break
            else:
                # Marqueur absent — encapsuler quand même
                title, emoji = SECTION_META[key]
                sections.append(
                    BriefingSection(key=key, title=title, content=extra.strip(), emoji=emoji)
                )
                print(f"  + Section {key} ajoutée (sans marqueur)")
        except Exception as e:
            print(f"  ! Échec section {key} : {e}")

    sections = merge_sections(sections)
    return sections


def assemble_full_text(sections: list[BriefingSection]) -> str:
    parts: list[str] = []
    for s in sections:
        parts.append(f"=== {s.key} ===")
        parts.append(s.content)
        parts.append("")
    return "\n".join(parts).strip()
