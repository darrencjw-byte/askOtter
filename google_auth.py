"""Google Sign-In + delegated Drive access (OAuth 2.0, per-user scoped)."""
import os

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _client_config() -> dict:
    return {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _redirect_uri() -> str:
    return os.getenv("REDIRECT_URI", "").rstrip("/")


def is_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET") and _redirect_uri())


def get_authorization_url() -> str:
    # PKCE is skipped: this is a confidential client (holds a client_secret), and
    # PKCE's code_verifier would need to survive the round-trip to Google and back —
    # which st.session_state cannot guarantee across a redirect behind a proxy/multiple
    # instances. The client_secret itself already protects the token exchange.
    flow = Flow.from_client_config(
        _client_config(), scopes=SCOPES, redirect_uri=_redirect_uri(), autogenerate_code_verifier=False
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def handle_callback(code: str) -> dict:
    """Exchanges the auth code for tokens and returns the signed-in user's profile."""
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=_redirect_uri(),
        autogenerate_code_verifier=False,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    st.session_state["google_credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

    import httplib2
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build

    # No default network timeout on the Google API client — set one explicitly
    # so a stalled request fails fast instead of hanging the sign-in flow.
    authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=20))
    oauth2_service = build("oauth2", "v2", http=authed_http)
    profile = oauth2_service.userinfo().get().execute()
    return profile


def get_credentials() -> Credentials | None:
    data = st.session_state.get("google_credentials")
    if not data:
        return None
    return Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )


def is_signed_in() -> bool:
    return "google_credentials" in st.session_state


def sign_out():
    st.session_state.pop("google_credentials", None)
    st.session_state.pop("google_profile", None)
    st.session_state.pop("oauth_state", None)
