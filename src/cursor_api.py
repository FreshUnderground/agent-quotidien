"""Client REST Cursor Cloud Agents API v1 — sans dépendance cursor-sdk."""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from typing import Any

API_BASE = "https://api.cursor.com/v1/agents"
POLL_INTERVAL_SEC = 20
MAX_WAIT_SEC = 40 * 60  # 40 min (workflow timeout 45 min)


def _auth_header(api_key: str) -> dict[str, str]:
    token = base_key = api_key.strip()
    # Basic auth : clé comme username, mot de passe vide (doc Cursor)
    basic = base64.b64encode(f"{base_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _request(
    method: str,
    url: str,
    api_key: str,
    body: dict[str, Any] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=_auth_header(api_key))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cursor API HTTP {e.code} — {detail}") from e


def create_agent_run(prompt: str, api_key: str, model: str = "composer-2.5") -> tuple[str, str]:
    """Crée un agent cloud et retourne (agent_id, run_id)."""
    payload = {
        "prompt": {"text": prompt},
        "model": {"id": model},
    }
    data = _request("POST", API_BASE, api_key, payload)
    agent = data.get("agent") or {}
    run = data.get("run") or {}
    agent_id = agent.get("id") or data.get("id")
    run_id = run.get("id") or agent.get("latestRunId")
    if not agent_id or not run_id:
        raise RuntimeError(f"Réponse Cursor inattendue : {json.dumps(data)[:500]}")
    return agent_id, run_id


def get_run(agent_id: str, run_id: str, api_key: str) -> dict[str, Any]:
    url = f"{API_BASE}/{agent_id}/runs/{run_id}"
    return _request("GET", url, api_key)


def wait_for_run(agent_id: str, run_id: str, api_key: str) -> str:
    """Attend la fin du run et retourne le texte résultat."""
    terminal = {"FINISHED", "ERROR", "CANCELLED", "EXPIRED"}
    deadline = time.time() + MAX_WAIT_SEC
    last_status = ""

    while time.time() < deadline:
        run = get_run(agent_id, run_id, api_key)
        status = (run.get("status") or "").upper()
        last_status = status
        print(f"  Cursor run {run_id} — statut : {status}")

        if status in terminal:
            if status == "FINISHED":
                result = run.get("result") or ""
                if not result.strip():
                    raise RuntimeError("Run FINISHED mais résultat vide")
                return result
            raise RuntimeError(
                f"Run terminé avec statut {status} — {run.get('result', '')[:300]}"
            )

        time.sleep(POLL_INTERVAL_SEC)

    raise RuntimeError(f"Timeout après {MAX_WAIT_SEC}s (dernier statut : {last_status})")


def run_cloud_prompt(prompt: str, api_key: str) -> str:
    """Lance un agent cloud et retourne le texte du briefing."""
    print("Création agent Cursor Cloud…")
    agent_id, run_id = create_agent_run(prompt, api_key)
    print(f"Agent : {agent_id} | Run : {run_id}")
    print(f"Suivi : https://cursor.com/agents/{agent_id}")
    return wait_for_run(agent_id, run_id, api_key)
