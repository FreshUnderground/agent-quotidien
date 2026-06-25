"""Envoi email et WhatsApp des briefings quotidiens."""

from __future__ import annotations

import os
import re
import smtplib
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("SMTP_FROM", user).strip()

    if not all([user, password, to_addr]):
        raise ValueError("SMTP_USER, SMTP_PASSWORD et destinataire requis pour l'email")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(host, port, timeout=60) as server:
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


def telegram_combined_summary(sections: list[BriefingSection], date_str: str) -> str:
    """Résumé Telegram — plus long que WhatsApp (limite ~4000 car.)."""
    lines = [f"📅 Briefing du jour — {date_str}", ""]
    budget = 3800

    for s in sections:
        lines.append(f"{s.emoji} {s.title.upper()}")
        lines.append("-" * 30)
        for line in s.content.split("\n"):
            t = line.strip().replace("**", "")
            if not t or t.startswith("<!--"):
                continue
            if t.startswith("###"):
                continue
            lines.append(t[:200])
            if len("\n".join(lines)) > budget:
                lines.append("… (suite dans l'email)")
                break
        lines.append("")
        if len("\n".join(lines)) > budget:
            break

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
    for s in sections:
        parts.append("=" * 50)
        parts.append(f"{s.emoji} {s.title.upper()}")
        parts.append("=" * 50)
        parts.append(s.content)
        parts.append("")
    parts.append("— Agent quotidien Kawa · UZAAPP · INVESTEE-GROUP")
    return "\n".join(parts)


def combine_sections_html(sections: list[BriefingSection], date_str: str) -> str:
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
    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:720px;margin:auto;padding:20px">
<h1 style="color:#1a1a1a">📅 Briefing quotidien — {date_str}</h1>
<p style="color:#555">Kawa Kanzururu · UZAAPP · INVESTEE-GROUP · Appels d'offres</p>
<hr>
{body}
<hr>
<p style="color:#888;font-size:12px">Agent quotidien — dieumercikamina@gmail.com</p>
</body></html>"""


def whatsapp_combined_summary(sections: list[BriefingSection], date_str: str) -> str:
    """Résumé unique WhatsApp — toutes marques en un message."""
    lines = [f"📅 *Briefing du jour* — {date_str}", ""]
    budget = 1100  # limite CallMeBot ~1200

    for s in sections:
        header = f"{s.emoji} *{s.title}*"
        block_lines = [header]
        for line in s.content.split("\n"):
            t = line.strip().replace("**", "")
            if not t or t.startswith("<!--"):
                continue
            if t.startswith("#"):
                continue
            if t.startswith("##"):
                block_lines.append(f"▸ {t.lstrip('#').strip()}")
            elif t.startswith("- ") or t.startswith("|"):
                if not t.startswith("|--"):
                    block_lines.append(t[:120])
            elif t.startswith("**") or ":" in t[:40]:
                block_lines.append(t[:120])
            if len("\n".join(lines) + "\n" + "\n".join(block_lines)) > budget:
                block_lines.append("… (détail dans l'email)")
                break
        lines.extend(block_lines)
        lines.append("")
        if len("\n".join(lines)) > budget:
            lines.append("_Email complet : dieumercikamina@gmail.com_")
            break

    text = "\n".join(lines).strip()
    if len(text) > 1200:
        text = text[:1197] + "…"
    return text


def dispatch_all_sections(sections: list[BriefingSection], date_str: str) -> dict[str, str]:
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

    if mode == "combined":
        subject = f"📅 Briefing quotidien — {date_str}"
        plain = combine_sections_plain(sections, date_str)
        html = combine_sections_html(sections, date_str)
        wa_text = whatsapp_combined_summary(sections, date_str)
        tg_text = telegram_combined_summary(sections, date_str)

        if send_email_flag and email_to:
            try:
                send_email(email_to, subject, plain, html)
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
