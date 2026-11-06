"""Browser-side session persistence (no server storage).

Uses st.context.cookies (read-only) for loading and JavaScript injection
for setting cookies, replacing the extra_streamlit_components dependency
which has compatibility issues on newer Python versions.
"""
import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken

COOKIE_NAME = "askotter_session"
COOKIE_MAX_AGE_DAYS = 7


def _fernet() -> Fernet:
    secret_material = (os.getenv("GOOGLE_CLIENT_SECRET", "") + os.getenv("APP_PASSWORD", "CFS@2027")).encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret_material).digest())
    return Fernet(key)


def save_session(data: dict) -> None:
    """Encrypts and writes session data to a browser cookie via JavaScript."""
    token = _fernet().encrypt(json.dumps(data).encode()).decode()
    max_age = COOKIE_MAX_AGE_DAYS * 86400
    js = f"""
    <script>
    document.cookie = "{COOKIE_NAME}={token}; path=/; max-age={max_age}; SameSite=Lax; Secure";
    </script>
    """
    st.html(js)


def load_session() -> dict | None:
    """Reads and decrypts the session cookie. Returns None if absent/invalid."""
    try:
        cookies = st.context.cookies
        raw = cookies.get(COOKIE_NAME)
    except Exception:
        return None
    if not raw:
        return None
    try:
        return json.loads(_fernet().decrypt(raw.encode()).decode())
    except (InvalidToken, ValueError, TypeError):
        return None


def clear_session() -> None:
    js = f"""
    <script>
    document.cookie = "{COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax; Secure";
    </script>
    """
    st.html(js)
