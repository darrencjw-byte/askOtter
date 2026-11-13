"""Google Drive access using owner's stored refresh token (server-side, not per-user)."""
import os

from google.oauth2.credentials import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_credentials() -> Credentials:
    """Builds credentials from env vars (stored in Streamlit secrets)."""
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not all([refresh_token, client_id, client_secret]):
        raise ValueError(
            "Google Drive is not configured. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in secrets."
        )

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
