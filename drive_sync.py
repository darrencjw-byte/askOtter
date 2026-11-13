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


def _list_files_in_folder(service, folder_id: str) -> list[dict]:
    """Lists all supported files inside a single folder (non-recursive)."""
    mime_filter = " or ".join(f"mimeType='{m}'" for m in SUPPORTED_MIME_TYPES)
    query = f"({mime_filter}) and trashed=false and '{folder_id}' in parents"

    files = []
    page_token = None
    while True:
        results = (
            service.files()
            .list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    return files


def _list_subfolders(service, folder_id: str) -> list[str]:
    """Returns IDs of immediate subfolders inside a folder."""
    query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and '{folder_id}' in parents"
    folder_ids = []
    page_token = None
    while True:
        results = (
            service.files()
            .list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
            )
            .execute()
        )
        folder_ids.extend(f["id"] for f in results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break
    return folder_ids


def list_files(credentials, folder_url: str | None = None) -> list[dict]:
    """Lists supported files, recursing into subfolders when a folder URL is given."""
    service = _build_service("drive", "v3", credentials)

    folder_id = _extract_folder_id(folder_url) if folder_url else None

    if not folder_id:
        mime_filter = " or ".join(f"mimeType='{m}'" for m in SUPPORTED_MIME_TYPES)
        query = f"({mime_filter}) and trashed=false"
        all_files = []
        page_token = None
        while True:
            results = (
                service.files()
                .list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    corpora="allDrives",
                    pageToken=page_token,
                )
                .execute()
            )
            all_files.extend(results.get("files", []))
            page_token = results.get("nextPageToken")
            if not page_token:
                break
        return all_files

    # Recurse into subfolders
    all_files = []
    folders_to_scan = [folder_id]
    while folders_to_scan:
        current = folders_to_scan.pop()
        all_files.extend(_list_files_in_folder(service, current))
        folders_to_scan.extend(_list_subfolders(service, current))
    return all_files


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
