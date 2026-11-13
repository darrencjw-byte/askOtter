"""One-time helper to obtain a Google refresh token for the owner's Drive.

Run this locally:
    python get_refresh_token.py

It will open a browser for Google sign-in. After authorising, the refresh
token is printed — copy it into your Streamlit secrets as GOOGLE_REFRESH_TOKEN.

Requires: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET as env vars (or in .env).
"""
import os
from dotenv import load_dotenv

load_dotenv()

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

client_config = {
    "installed": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

print("\n" + "=" * 60)
print("GOOGLE_REFRESH_TOKEN:")
print(creds.refresh_token)
print("=" * 60)
print("\nCopy the token above into your Streamlit Cloud secrets.")
