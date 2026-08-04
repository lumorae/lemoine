#!/usr/bin/env python3
"""Upload a render straight into the Google Drive 'Cut' folder.

The claude.ai Drive connector can't carry video-sized uploads, so this talks
to the Drive API directly. It needs a service account key:

  1. console.cloud.google.com → create project → enable "Google Drive API"
  2. Create a service account, download its JSON key
  3. Share the Drive folder (e.g. "Cut") with the service account's email
     (Editor access)
  4. Put the key at tools/lemoine-cut/gdrive-sa.json  (or set GDRIVE_SA_JSON
     to its path). It's gitignored.

Usage:
  python3 drive_upload.py --file cut.mp4 --folder-id 1c1JtVATdmmVnzR_sMFxUl61suf01bzbu
"""
import argparse
import base64
import json
import mimetypes
import os
import time
import urllib.parse
import urllib.request

DEFAULT_KEY = os.path.join(os.path.dirname(__file__), "gdrive-sa.json")
CUT_FOLDER_ID = "1c1JtVATdmmVnzR_sMFxUl61suf01bzbu"  # johnny's "Cut" folder


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def get_token(key_path):
    """OAuth2 JWT bearer flow for a service account (no SDK needed).

    Signs with the openssl CLI to avoid depending on the cryptography wheel,
    which can fail to load its Rust binding in some sandboxes.
    """
    import subprocess
    import tempfile

    sa = json.load(open(key_path))
    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    # Service accounts have no storage of their own, so impersonate a real
    # Workspace user (domain-wide delegation) — uploaded files are owned by
    # them and use their Drive quota. Set GDRIVE_IMPERSONATE to override.
    claim = {
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/drive",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }
    sub = os.environ.get("GDRIVE_IMPERSONATE", "hello@johnnylemoine.com")
    if sub:
        claim["sub"] = sub
    claims = b64url(json.dumps(claim).encode())
    signing_input = f"{header}.{claims}".encode()

    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as kf:
        kf.write(sa["private_key"])
        key_file = kf.name
    try:
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_file],
            input=signing_input, capture_output=True, check=True)
        sig = proc.stdout
    finally:
        os.unlink(key_file)
    jwt = f"{header}.{claims}.{b64url(sig)}"

    body = ("grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer"
            f"&assertion={jwt}").encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["access_token"]


def ensure_folder(name, parent_id, token):
    """Find (or create) a subfolder by name under parent_id; return its id."""
    q = ("mimeType='application/vnd.google-apps.folder' and trashed=false "
         f"and name='{name}' and '{parent_id}' in parents")
    req = urllib.request.Request(
        "https://www.googleapis.com/drive/v3/files?q=" + urllib.parse.quote(q) +
        "&fields=files(id)&supportsAllDrives=true&includeItemsFromAllDrives=true",
        headers={"Authorization": f"Bearer {token}"})
    hits = json.load(urllib.request.urlopen(req)).get("files", [])
    if hits:
        return hits[0]["id"]
    meta = json.dumps({"name": name, "parents": [parent_id],
                       "mimeType": "application/vnd.google-apps.folder"}).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/drive/v3/files?supportsAllDrives=true",
        data=meta, method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json; charset=UTF-8"})
    return json.load(urllib.request.urlopen(req))["id"]



def trash_exact(name, parent_id, token):
    """Move files with an EXACT name (in one folder) to trash.

    Never use loose `name contains` queries with permanent delete: Drive's
    contains matching is token-based, so 'double-nova' also matches
    'double nova ... .MOV' and files.delete bypasses the trash entirely.
    This helper matches the full name, scopes to one parent, and trashes
    (recoverable) instead of deleting.
    """
    q = f"name = '{name}' and '{parent_id}' in parents and trashed=false"
    req = urllib.request.Request(
        "https://www.googleapis.com/drive/v3/files?q=" + urllib.parse.quote(q) +
        "&fields=files(id,name)&supportsAllDrives=true",
        headers={"Authorization": f"Bearer {token}"})
    out = []
    for f in json.load(urllib.request.urlopen(req)).get("files", []):
        r = urllib.request.Request(
            f"https://www.googleapis.com/drive/v3/files/{f['id']}?supportsAllDrives=true",
            data=json.dumps({"trashed": True}).encode(), method="PATCH",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json; charset=UTF-8"})
        urllib.request.urlopen(r)
        out.append(f["name"])
    return out


def upload(path, folder_id, token):
    import urllib.parse  # noqa: F401 (used by ensure_folder callers)
    name = os.path.basename(path)
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    meta = json.dumps({"name": name, "parents": [folder_id]}).encode()

    # resumable session
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
        data=meta, method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": mime})
    with urllib.request.urlopen(req) as r:
        session = r.headers["Location"]

    size = os.path.getsize(path)
    with open(path, "rb") as f:
        req = urllib.request.Request(
            session, data=f, method="PUT",
            headers={"Content-Type": mime, "Content-Length": str(size)})
        with urllib.request.urlopen(req) as r:
            info = json.load(r)
    print(f"uploaded: {name} -> https://drive.google.com/file/d/{info['id']}/view")
    return info["id"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--folder-id", default=CUT_FOLDER_ID)
    ap.add_argument("--subfolder", default=os.environ.get("LEMOINE_DRIVE_SUBFOLDER", ""),
                    help="month folder etc. — found or created under the Cut folder")
    ap.add_argument("--key", default=os.environ.get("GDRIVE_SA_JSON", DEFAULT_KEY))
    args = ap.parse_args()
    if not os.path.exists(args.key):
        raise SystemExit(f"no service-account key at {args.key} — see header comment for setup")
    token = get_token(args.key)
    dest = args.folder_id
    if args.subfolder:
        dest = ensure_folder(args.subfolder, dest, token)
    upload(args.file, dest, token)
