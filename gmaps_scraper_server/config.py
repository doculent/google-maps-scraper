"""
Centralized secrets loader.

Priority order:
  1. Infisical (Universal Auth) — when INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET,
     and INFISICAL_PROJECT_ID are all set.
  2. .env file / os.environ — used as the baseline and as a fallback if Infisical
     credentials are missing or the fetch fails.

Infisical env vars:
  INFISICAL_CLIENT_ID      – machine identity client ID
  INFISICAL_CLIENT_SECRET  – machine identity client secret
  INFISICAL_PROJECT_ID     – Infisical project ID
  INFISICAL_ENVIRONMENT    – secret environment slug (default: "dev")
  INFISICAL_HOST           – self-hosted URL (default: https://app.infisical.com)
  INFISICAL_SECRET_PATH    – secret path (default: "/")
"""

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_INFISICAL_DEFAULT_HOST = "https://app.infisical.com"


def _login(host: str, client_id: str, client_secret: str) -> str:
    url = f"{host}/api/v1/auth/universal-auth/login"
    payload = json.dumps({"clientId": client_id, "clientSecret": client_secret}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["accessToken"]


def _fetch_secrets(
    host: str, token: str, project_id: str, environment: str, secret_path: str
) -> dict[str, str]:
    params = urllib.parse.urlencode(
        {"workspaceId": project_id, "environment": environment, "secretPath": secret_path}
    )
    req = urllib.request.Request(
        f"{host}/api/v3/secrets/raw?{params}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return {s["secretKey"]: s["secretValue"] for s in data["secrets"]}


def load_secrets() -> None:
    """Load secrets into os.environ from Infisical, falling back to .env."""
    load_dotenv()  # baseline — always load .env first

    client_id = os.environ.get("INFISICAL_CLIENT_ID")
    client_secret = os.environ.get("INFISICAL_CLIENT_SECRET")
    project_id = os.environ.get("INFISICAL_PROJECT_ID")

    if not (client_id and client_secret and project_id):
        logger.debug("Infisical credentials not configured — using .env / os.environ")
        return

    host = os.environ.get("INFISICAL_HOST", _INFISICAL_DEFAULT_HOST)
    environment = os.environ.get("INFISICAL_ENVIRONMENT", "dev")
    secret_path = os.environ.get("INFISICAL_SECRET_PATH", "/")

    try:
        token = _login(host, client_id, client_secret)
        secrets = _fetch_secrets(host, token, project_id, environment, secret_path)
        os.environ.update(secrets)
        logger.info("Loaded %d secrets from Infisical (env=%s)", len(secrets), environment)
    except Exception as exc:
        logger.warning("Infisical fetch failed, continuing with os.environ: %s", exc)
