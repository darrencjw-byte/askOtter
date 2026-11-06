"""Lists and downloads files from the signed-in user's Google Drive (delegated, per-user scoped)."""
import io

import httplib2
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# The Google API client has no default network timeout — a stalled request can hang
# forever instead of raising. Build every service over an AuthorizedHttp with an
# explicit timeout so a slow/unreachable API fails fast with a catchable error.
REQUEST_TIMEOUT_SECONDS = 20


def _build_service(name: str, version: str, credentials):
    authed_http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=REQUEST_TIMEOUT_SECONDS))
    return build(name, version, http=authed_http)

EXPORT_MIME_MAP = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
}

SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.spreadsheet",
]


def list_files(credentials, folder_url: str | None = None, page_size: int = 50) -> list[dict]:
    """Lists files visible to the signed-in user — restricted to supported document types.

    If folder_url is given, lists only that folder's contents (folder ID parsed from the URL).
    Otherwise lists files across the user's Drive (My Drive + Shared Drives they belong to).
    """
    service = _build_service("drive", "v3", credentials)

    mime_filter = " or ".join(f"mimeType='{m}'" for m in SUPPORTED_MIME_TYPES)
    query_parts = [f"({mime_filter})", "trashed=false"]

    folder_id = _extract_folder_id(folder_url) if folder_url else None
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")

    query = " and ".join(query_parts)

    results = (
        service.files()
        .list(
            q=query,
            pageSize=page_size,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora="allDrives" if not folder_id else "user",
        )
        .execute()
    )
    return results.get("files", [])


def _extract_folder_id(folder_url: str) -> str | None:
    if "/folders/" in folder_url:
        return folder_url.split("/folders/")[1].split("?")[0].split("/")[0]
    return None


def download_file(credentials, file_id: str, mime_type: str, file_name: str, service=None) -> tuple[bytes, str]:
    """Downloads (or exports, for Google Docs/Sheets) a file. Returns (content_bytes, final_name)."""
    if service is None:
        service = _build_service("drive", "v3", credentials)

    if mime_type in EXPORT_MIME_MAP:
        export_mime, suffix = EXPORT_MIME_MAP[mime_type]
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        final_name = file_name + suffix
    else:
        request = service.files().get_media(fileId=file_id)
        final_name = file_name

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buffer.getvalue(), final_name
