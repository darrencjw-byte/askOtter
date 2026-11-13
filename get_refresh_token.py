"""One-time helper to obtain a Google refresh token.

Run locally:
    GOOGLE_CLIENT_ID="..." GOOGLE_CLIENT_SECRET="..." python3 get_refresh_token.py

Step 1: Prints a URL — open it in your browser and sign in.
Step 2: Google redirects to your redirect URI with ?code=... in the URL.
Step 3: Copy the full redirected URL and paste it here.
Step 4: The script exchanges the code for a refresh token and prints it.
"""
import os
from urllib.parse import urlencode, urlparse, parse_qs

import requests

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://askotter.streamlit.app"
SCOPES = "https://www.googleapis.com/auth/drive.readonly"

auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode({
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPES,
    "access_type": "offline",
    "prompt": "consent",
})

print("\n1. Open this URL in your browser:\n")
print(auth_url)
print("\n2. Sign in with your Google account.")
print("3. After authorising, you'll be redirected to a URL like:")
print("   https://askotter.streamlit.app/?code=4/0A...")
print("   (The page may show an error — that's OK, we just need the URL)\n")

redirect_url = input("4. Paste the full redirected URL here: ").strip()

parsed = urlparse(redirect_url)
code = parse_qs(parsed.query).get("code", [None])[0]

if not code:
    print("ERROR: Could not find 'code' in the URL. Make sure you pasted the full URL.")
    exit(1)

token_response = requests.post("https://oauth2.googleapis.com/token", data={
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
})

if token_response.status_code != 200:
    print(f"ERROR: Token exchange failed: {token_response.text}")
    exit(1)

tokens = token_response.json()
refresh_token = tokens.get("refresh_token")

if not refresh_token:
    print(f"ERROR: No refresh token in response. Full response: {tokens}")
    exit(1)

print("\n" + "=" * 60)
print("GOOGLE_REFRESH_TOKEN:")
print(refresh_token)
print("=" * 60)
print("\nCopy the token above into your Streamlit Cloud secrets.")
