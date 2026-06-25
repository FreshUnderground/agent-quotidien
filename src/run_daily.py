#!/usr/bin/env python3
"""
Agent quotidien — briefing 4 marques + envoi email & WhatsApp.

Usage:
  python src/run_daily.py
  python src/run_daily.py --no-notify    # sauvegarde fichier seulement
  python src/run_daily.py --notify-only  # renvoie le dernier briefing

Marques : Kawa Kanzururu | UZAAPP | INVESTEE-GROUP | Appels d'offres
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = ROOT / "prompts" / "briefing-quotidien.md"
OUTPUT_DIR = ROOT / "output"


def load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt introuvable : {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


def save_result(text: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = OUTPUT_DIR / f"briefing-{date_str}.md"
    header = f"<!-- Généré le {datetime.now().isoformat(timespec='seconds')} -->\n\n"
    out_path.write_text(header + text, encoding="utf-8")
    return out_path


def save_sections(sections, date_str: str) -> None:
    from notify import BriefingSection  # noqa: F401

    for s in sections:
        path = OUTPUT_DIR / f"{date_str}-{s.key.lower()}.md"
        path.write_text(s.content, encoding="utf-8")


def run_cloud(prompt: str, api_key: str) -> str:
    from cursor_sdk import Agent, AgentOptions, CloudAgentOptions

    result = Agent.prompt(
        prompt,
        AgentOptions(
            api_key=api_key,
            model="composer-2.5",
            cloud=CloudAgentOptions(),
        ),
    )
    if result.status == "error":
        raise RuntimeError(f"Run échoué : {getattr(result, 'id', 'unknown')}")
    return result.result or ""


def run_local(prompt: str, api_key: str) -> str:
    from cursor_sdk import Agent, AgentOptions, LocalAgentOptions

    result = Agent.prompt(
        prompt,
        AgentOptions(
            api_key=api_key,
            model="composer-2.5",
            local=LocalAgentOptions(cwd=str(ROOT)),
        ),
    )
    if result.status == "error":
        raise RuntimeError(f"Run échoué : {getattr(result, 'id', 'unknown')}")
    return result.result or ""


def notify_from_file(path: Path) -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from notify import dispatch_all_sections, parse_sections

    text = path.read_text(encoding="utf-8")
    date_str = datetime.now().strftime("%d/%m/%Y")
    sections = parse_sections(text)
    log = dispatch_all_sections(sections, date_str)
    for k, v in log.items():
        print(f"  {k}: {v}")
    return 0 if all(v == "ok" for v in log.values()) else 1


def main() -> int:
    load_dotenv()
    sys.path.insert(0, str(ROOT / "src"))

    parser = argparse.ArgumentParser(description="Briefing quotidien multi-marques")
    parser.add_argument("--mode", choices=("cloud", "local"), default="cloud")
    parser.add_argument("--no-notify", action="store_true", help="Ne pas envoyer email/WhatsApp")
    parser.add_argument(
        "--notify-only",
        action="store_true",
        help="Renvoyer les notifications du briefing du jour",
    )
    args = parser.parse_args()

    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = OUTPUT_DIR / f"briefing-{date_str}.md"

    if args.notify_only:
        if not out_path.exists():
            print(f"ERREUR : pas de briefing pour {date_str}", file=sys.stderr)
            return 1
        print("Renvoi des notifications…")
        return notify_from_file(out_path)

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        print(
            "ERREUR : CURSOR_API_KEY manquant (cursor.com/dashboard → API Keys)",
            file=sys.stderr,
        )
        return 1

    try:
        from notify import dispatch_all_sections, parse_sections

        prompt = load_prompt()
        print(f"Mode {args.mode} — génération des 4 briefings…")
        text = run_cloud(prompt, api_key) if args.mode == "cloud" else run_local(prompt, api_key)
        if not text.strip():
            print("AVERTISSEMENT : réponse vide.", file=sys.stderr)

        out_path = save_result(text)
        print(f"Fichier : {out_path}")

        sections = parse_sections(text)
        save_sections(sections, date_str)
        print(f"Sections : {len(sections)} ({', '.join(s.key for s in sections)})")

        if not args.no_notify:
            display_date = datetime.now().strftime("%d/%m/%Y")
            log = dispatch_all_sections(sections, display_date)
            print("\nNotifications :")
            for k, v in log.items():
                print(f"  {k}: {v}")
            if not log:
                print(
                    "  (aucun envoi — configurez NOTIFY_EMAIL et/ou WHATSAPP dans .env)",
                )

        return 0
    except ImportError as e:
        print(f"ERREUR import : {e}\n pip install cursor-sdk", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
