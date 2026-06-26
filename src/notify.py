"""Envoi email et WhatsApp des briefings quotidiens."""

from __future__ import annotations

import os
import re
import smtplib
import urllib.parse
import urllib.request
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import NamedTuple


class BriefingSection(NamedTuple):
    key: str
    title: str
    content: str
    emoji: str


SECTION_META = {
    "KAWA_KANZURURU": ("Kawa Kanzururu", "☕"),
    "UZAAPP": ("UZAAPP", "📱"),
    "INVESTEE_GROUP": ("INVESTEE-GROUP", "💻"),
    "APPELS_OFFRES": ("Appels d'offres", "📋"),
}

MARKER_PATTERN = re.compile(
    r"===\s*(KAWA_KANZURURU|UZAAPP|INVESTEE_GROUP|APPELS_OFFRES)\s*===",
    re.IGNORECASE,
)


def parse_sections(full_text: str) -> list[BriefingSection]:
    """Découpe le texte agent en 4 sections via marqueurs."""
    parts = MARKER_PATTERN.split(full_text)
    sections: list[BriefingSection] = []

    # split alterne: [avant, KEY, contenu, KEY, contenu, ...]
    i = 1
    while i < len(parts) - 1:
        key = parts[i].strip().upper()
        body = parts[i + 1].strip()
        if key in SECTION_META:
            title, emoji = SECTION_META[key]
            sections.append(BriefingSection(key=key, title=title, content=body, emoji=emoji))
        i += 2

    if sections:
        return sections

    # Fallback : un seul message si marqueurs absents
    return [
        BriefingSection(
            key="BRIEFING",
            title="Briefing complet",
            content=full_text.strip(),
            emoji="📅",
        )
    ]


def _html_body(section: BriefingSection, date_str: str) -> str:
    escaped = (
        section.content.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>\n")
    )
    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:640px;margin:auto;padding:16px">
<h2>{section.emoji} {section.title} — {date_str}</h2>
<div style="line-height:1.5">{escaped}</div>
<hr>
<p style="color:#666;font-size:12px">Agent quotidien Dieu-Merci — Butembo, RDC</p>
</body></html>"""


def send_email(
    to_addr: str,
    subject: str,
    plain: str,
    html: str | None = None,
    image_paths: list[Path] | None = None,
) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("SMTP_FROM", user).strip()

    if not all([user, password, to_addr]):
        raise ValueError("SMTP_USER, SMTP_PASSWORD et destinataire requis pour l'email")

    images = image_paths or []
    if images:
        msg = MIMEMultipart("related")
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(plain, "plain", "utf-8"))
        if html:
            alt.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(alt)
        for i, img_path in enumerate(images):
            if not img_path.exists():
                continue
            cid = f"img{i}"
            mime_img = MIMEImage(img_path.read_bytes(), _subtype="png")
            mime_img.add_header("Content-ID", f"<{cid}>")
            mime_img.add_header(
                "Content-Disposition",
                "attachment",
                filename=img_path.name,
            )
            msg.attach(mime_img)
    else:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        if html:
            msg.attach(MIMEText(html, "html", "utf-8"))

    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(host, port, timeout=120) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())


def send_telegram_user(username: str, text: str) -> None:
    """CallMeBot Telegram — message privé (@username, /start requis sur @CallMeBot_txtbot)."""
    if len(text) > 4000:
        text = text[:3997] + "…"
    user = username if username.startswith("@") else f"@{username}"
    params = urllib.parse.urlencode({"user": user, "text": text, "html": "no"})
    url = f"https://api.callmebot.com/text.php?{params}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        if "ERROR" in body.upper() or "NOT AUTHORIZED" in body.upper():
            raise RuntimeError(f"CallMeBot Telegram : {body}")


def send_telegram_group(apikey: str, text: str) -> None:
    """CallMeBot Telegram — message vers un groupe."""
    if len(text) > 4000:
        text = text[:3997] + "…"
    params = urllib.parse.urlencode(
        {"apikey": apikey, "text": text, "html": "no"}
    )
    url = f"https://api.callmebot.com/telegram/group.php?{params}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        if "ERROR" in body.upper():
            raise RuntimeError(f"CallMeBot Telegram groupe : {body}")


def telegram_combined_summary(
    sections: list[BriefingSection],
    date_str: str,
    image_count: int = 0,
) -> str:
    """Résumé Telegram — conseils du jour en tête, puis extraits par marque."""
    lines = [f"📅 Briefing du jour — {date_str}", ""]
    conseils = _conseils_du_jour_block(sections)
    if conseils:
        lines.append("💡 *CONSEILS DU JOUR*")
        lines.extend(conseils)
        lines.append("")
    if image_count > 0:
        lines.append(f"🖼️ {image_count} ébauches visuelles jointes à l'email")
        lines.append("📋 Guide créateur : briefs-createur.md")
        lines.append("")

    for s in sections:
        lines.append(f"{s.emoji} {s.title.upper()}")
        lines.append("-" * 28)
        for h in _extract_highlights(s.content, max_lines=5):
            lines.append(h)
        lines.append("")

    text = "\n".join(lines).strip()
    return text[:4000]


def send_whatsapp_callmebot(phone: str, text: str, apikey: str) -> None:
    """CallMeBot — gratuit, inscription sur callmebot.com."""
    if len(text) > 1200:
        text = text[:1197] + "…"
    params = urllib.parse.urlencode(
        {"phone": phone, "text": text, "apikey": apikey}
    )
    url = f"https://api.callmebot.com/whatsapp.php?{params}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        if "ERROR" in body.upper():
            raise RuntimeError(f"CallMeBot : {body}")


def send_whatsapp_twilio(
    account_sid: str,
    auth_token: str,
    from_whatsapp: str,
    to_whatsapp: str,
    text: str,
) -> None:
    """Twilio WhatsApp — compte payant, plus fiable en production."""
    if len(text) > 1500:
        text = text[:1497] + "…"
    data = urllib.parse.urlencode(
        {"From": from_whatsapp, "To": to_whatsapp, "Body": text}
    ).encode("utf-8")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    password_mgr = __import__("urllib.request", fromlist=["HTTPPasswordMgrWithDefaultRealm"])
    mgr = password_mgr.HTTPPasswordMgrWithDefaultRealm()
    mgr.add_password(None, url, account_sid, auth_token)
    opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(mgr))
    req = urllib.request.Request(url, data=data, method="POST")
    with opener.open(req, timeout=30) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"Twilio HTTP {resp.status}")


def whatsapp_plain_summary(section: BriefingSection, date_str: str) -> str:
    """Version courte pour WhatsApp (limite de caractères)."""
    lines = section.content.split("\n")
    # Garder titre + premières lignes utiles
    kept: list[str] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("<!--"):
            continue
        if s.startswith("#"):
            kept.append(s.lstrip("#").strip())
            continue
        if s.startswith("##") or s.startswith("**") or s.startswith("-") or s.startswith("|"):
            kept.append(s.replace("**", ""))
        if len("\n".join(kept)) > 900:
            break
    body = "\n".join(kept[:25])
    return f"{section.emoji} *{section.title}* — {date_str}\n\n{body}\n\n_Ouvrez l'email pour le détail complet._"


def combine_sections_plain(sections: list[BriefingSection], date_str: str) -> str:
    """Un seul message texte regroupant toutes les sections."""
    parts = [f"📅 BRIEFING QUOTIDIEN — {date_str}", f"Dieu-Merci Kamina | Butembo, RDC", ""]
    conseils = _conseils_du_jour_block(sections)
    if conseils:
        parts.append("=" * 50)
        parts.append("💡 CONSEILS DU JOUR")
        parts.append("=" * 50)
        for c in conseils:
            parts.append(c.replace("*", ""))
        parts.append("")
    for s in sections:
        parts.append("=" * 50)
        parts.append(f"{s.emoji} {s.title.upper()}")
        parts.append("=" * 50)
        parts.append(s.content)
        parts.append("")
    parts.append("— Agent quotidien Kawa · UZAAPP · INVESTEE-GROUP")
    return "\n".join(parts)


def _images_html_block(image_paths: list[Path]) -> str:
    if not image_paths:
        return ""
    items: list[str] = []
    for i, p in enumerate(image_paths):
        if p.exists():
            items.append(
                f'<div style="margin:16px 0">'
                f'<p style="font-size:13px;color:#555">{p.stem.replace("-", " ")}</p>'
                f'<img src="cid:img{i}" alt="{p.name}" style="max-width:100%;border-radius:8px">'
                f"</div>"
            )
    if not items:
        return ""
    return (
        '<h2 style="color:#1a1a1a;margin-top:28px">🖼️ Visuels du jour (à publier)</h2>'
        + "\n".join(items)
    )


def combine_sections_html(
    sections: list[BriefingSection],
    date_str: str,
    image_paths: list[Path] | None = None,
) -> str:
    blocks: list[str] = []
    for s in sections:
        escaped = (
            s.content.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>\n")
        )
        blocks.append(
            f'<h2 style="color:#2c5530;margin-top:24px">{s.emoji} {s.title}</h2>'
            f'<div style="line-height:1.6">{escaped}</div>'
        )
    body = "\n".join(blocks)
    images_block = _images_html_block(image_paths or [])
    conseils_html = ""
    conseils = _conseils_du_jour_block(sections)
    if conseils:
        items = "".join(
            f'<li style="margin:8px 0">{c.replace("*", "")}</li>' for c in conseils
        )
        conseils_html = f"""
<div style="background:#fff8e1;border-left:4px solid #f9a825;padding:16px 20px;margin:20px 0;border-radius:6px">
<h2 style="color:#e65100;margin:0 0 12px">💡 Conseils du jour</h2>
<ul style="margin:0;padding-left:20px;line-height:1.6">{items}</ul>
</div>"""
    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:720px;margin:auto;padding:20px">
<h1 style="color:#1a1a1a">📅 Briefing quotidien — {date_str}</h1>
<p style="color:#555">Kawa Kanzururu · UZAAPP · INVESTEE-GROUP · Appels d'offres</p>
<hr>
{conseils_html}
{body}
{images_block}
<hr>
<p style="color:#888;font-size:12px">Agent quotidien — dieumercikamina@gmail.com</p>
</body></html>"""


CONSEIL_PATTERN = re.compile(
    r"##\s*💡\s*Conseil[^\n]*\n+(.+?)(?=\n## |\n---|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def _extract_conseil(content: str) -> str:
    """Extrait le texte du bloc « Conseil … du jour »."""
    match = CONSEIL_PATTERN.search(content)
    if not match:
        return ""
    text = match.group(1).strip()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip() and not ln.strip().startswith("#")]
    return " ".join(lines)[:280]


def _conseils_du_jour_block(sections: list[BriefingSection]) -> list[str]:
    """Bloc prioritaire : tous les conseils du jour, une ligne par marque."""
    lines: list[str] = []
    for s in sections:
        conseil = _extract_conseil(s.content)
        if conseil:
            lines.append(f"{s.emoji} *{s.title}* : {conseil}")
    return lines


def _extract_highlights(content: str, max_lines: int = 5) -> list[str]:
    """Extrait les lignes les plus utiles d'une section."""
    highlights: list[str] = []
    for line in content.split("\n"):
        t = line.strip().replace("**", "")
        if not t or t.startswith("<!--") or t.startswith("|--"):
            continue
        if t.startswith("#"):
            continue
        if t.startswith("##"):
            highlights.append(f"▸ {t.lstrip('#').strip()}")
        elif t.startswith("- ") or (":" in t[:50] and not t.startswith("http")):
            highlights.append(t[:100])
        if len(highlights) >= max_lines:
            break
    return highlights


def whatsapp_combined_summary(
    sections: list[BriefingSection],
    date_str: str,
    image_count: int = 0,
) -> str:
    """Résumé WhatsApp — conseils du jour en premier, puis extraits par marque."""
    lines = [f"📅 *Briefing* — {date_str}", ""]
    conseils = _conseils_du_jour_block(sections)
    if conseils:
        lines.append("💡 *CONSEILS DU JOUR*")
        lines.extend(conseils)
        lines.append("")
    if image_count > 0:
        lines.append(f"🖼️ *{image_count} ébauches* + *briefs-createur.md*")
        lines.append("")

    for s in sections:
        lines.append(f"{s.emoji} *{s.title}*")
        for h in _extract_highlights(s.content, max_lines=3):
            lines.append(h)
        lines.append("")
        if len("\n".join(lines)) > 1100:
            lines.append("_Suite dans l'email_")
            break

    text = "\n".join(lines).strip()
    return text[:1197] + ("…" if len(text) > 1197 else "")


def dispatch_all_sections(
    sections: list[BriefingSection],
    date_str: str,
    image_paths: list[Path] | None = None,
) -> dict[str, str]:
    """Envoie le briefing par email, WhatsApp et Telegram (1 message regroupé par défaut)."""
    log: dict[str, str] = {}
    email_to = os.environ.get("NOTIFY_EMAIL", "").strip()
    wa_phone = os.environ.get("WHATSAPP_PHONE", "").strip()
    wa_provider = os.environ.get("WHATSAPP_PROVIDER", "callmebot").strip().lower()
    mode = os.environ.get("NOTIFY_MODE", "combined").strip().lower()

    send_email_flag = os.environ.get("SEND_EMAIL", "true").lower() == "true"
    send_wa_flag = os.environ.get("SEND_WHATSAPP", "true").lower() == "true"
    send_tg_flag = os.environ.get("SEND_TELEGRAM", "false").lower() == "true"
    tg_mode = os.environ.get("TELEGRAM_MODE", "user").strip().lower()
    tg_user = os.environ.get("TELEGRAM_USER", "").strip()
    tg_group_key = os.environ.get("TELEGRAM_GROUP_APIKEY", "").strip()

    images = [p for p in (image_paths or []) if p.exists()]
    img_count = len(images)

    if mode == "combined":
        subject = f"📅 Briefing quotidien — {date_str}"
        plain = combine_sections_plain(sections, date_str)
        if img_count:
            plain += f"\n\n🖼️ {img_count} ébauches visuelles + guide briefs-createur.md (marketing réaliste)."
        html = combine_sections_html(sections, date_str, images)
        wa_text = whatsapp_combined_summary(sections, date_str, img_count)
        tg_text = telegram_combined_summary(sections, date_str, img_count)

        if send_email_flag and email_to:
            try:
                send_email(email_to, subject, plain, html, image_paths=images)
                log["email:combined"] = "ok"
            except Exception as e:
                log["email:combined"] = f"erreur: {e}"

        if send_wa_flag and wa_phone:
            try:
                if wa_provider == "twilio":
                    send_whatsapp_twilio(
                        os.environ["TWILIO_ACCOUNT_SID"],
                        os.environ["TWILIO_AUTH_TOKEN"],
                        os.environ["TWILIO_WHATSAPP_FROM"],
                        f"whatsapp:{wa_phone}" if not wa_phone.startswith("whatsapp:") else wa_phone,
                        wa_text,
                    )
                else:
                    apikey = os.environ.get("CALLMEBOT_APIKEY", "").strip()
                    if not apikey:
                        raise ValueError("CALLMEBOT_APIKEY manquant")
                    send_whatsapp_callmebot(
                        wa_phone.replace("+", ""),
                        wa_text,
                        apikey,
                    )
                log["whatsapp:combined"] = "ok"
            except Exception as e:
                log["whatsapp:combined"] = f"erreur: {e}"

        if send_tg_flag:
            try:
                if tg_mode == "group":
                    if not tg_group_key:
                        raise ValueError("TELEGRAM_GROUP_APIKEY manquant")
                    send_telegram_group(tg_group_key, tg_text)
                else:
                    if not tg_user:
                        raise ValueError("TELEGRAM_USER manquant (ex: @votre_pseudo)")
                    send_telegram_user(tg_user, tg_text)
                log["telegram:combined"] = "ok"
            except Exception as e:
                log["telegram:combined"] = f"erreur: {e}"

        return log

    # Mode séparé (4 messages) — legacy
    for section in sections:
        subject = f"{section.emoji} {section.title} — {date_str}"
        plain = f"{section.title} — {date_str}\n\n{section.content}"
        html = _html_body(section, date_str)
        wa_short = whatsapp_plain_summary(section, date_str)

        if send_email_flag and email_to:
            try:
                send_email(email_to, subject, plain, html)
                log[f"email:{section.key}"] = "ok"
            except Exception as e:
                log[f"email:{section.key}"] = f"erreur: {e}"

        if send_wa_flag and wa_phone:
            try:
                if wa_provider == "twilio":
                    send_whatsapp_twilio(
                        os.environ["TWILIO_ACCOUNT_SID"],
                        os.environ["TWILIO_AUTH_TOKEN"],
                        os.environ["TWILIO_WHATSAPP_FROM"],
                        f"whatsapp:{wa_phone}" if not wa_phone.startswith("whatsapp:") else wa_phone,
                        wa_short,
                    )
                else:
                    send_whatsapp_callmebot(
                        wa_phone.replace("+", ""),
                        wa_short,
                        os.environ.get("CALLMEBOT_APIKEY", ""),
                    )
                log[f"whatsapp:{section.key}"] = "ok"
            except Exception as e:
                log[f"whatsapp:{section.key}"] = f"erreur: {e}"

    return log
