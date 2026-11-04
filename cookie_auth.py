"""Browser-side session persistence (no server storage).

Keeps the Google sign-in + password-gate state in an encrypted browser cookie
instead of only in `st.session_state`. `st.session_state` lives in one server
process's RAM — if that process restarts, or a later request lands on a
different replica, the in-memory state is gone and the user is bounced back
to the sign-in screen even though nothing actually went wrong on their end.

The cookie value is encrypted (Fernet) with a key derived from server-side
secrets that already exist (GOOGLE_CLIENT_SECRET + APP_PASSWORD) — nothing
new to configure, and nothing is written to disk or a database on the
server. The browser is the only place this state is stored.
"""
import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
import extra_streamlit_components as stx

COOKIE_NAME = "askotter_session"
COOKIE_MAX_AGE_DAYS = 7


def _fernet() -> Fernet:
    secret_material = (os.getenv("GOOGLE_CLIENT_SECRET", "") + os.getenv("APP_PASSWORD", "CFS@2027")).encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret_material).digest())
    return Fernet(key)


def _get_manager() -> stx.CookieManager:
    import streamlit as st

    if "_cookie_manager" not in st.session_state:
        st.session_state["_cookie_manager"] = stx.CookieManager(key="askotter_cookie_manager")
    return st.session_state["_cookie_manager"]


def save_session(data: dict) -> None:
    """Encrypts and writes session data to the browser cookie."""
    manager = _get_manager()
    token = _fernet().encrypt(json.dumps(data).encode()).decode()
    manager.set(
        COOKIE_NAME,
        token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=COOKIE_MAX_AGE_DAYS),
        key="askotter_session_set",
    )


def load_session() -> dict | None:
    """Reads and decrypts the browser cookie. Returns None if absent/invalid/corrupt."""
    manager = _get_manager()
    raw = manager.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        return json.loads(_fernet().decrypt(raw.encode()).decode())
    except (InvalidToken, ValueError, TypeError):
        return None


def clear_session() -> None:
    manager = _get_manager()
    try:
        manager.delete(COOKIE_NAME, key="askotter_session_delete")
    except KeyError:
        pass
