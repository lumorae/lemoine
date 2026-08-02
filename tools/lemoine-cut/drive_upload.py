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
import urllib.request

DEFAULT_KEY = os.path.join(os.path.dirname(__file__), "gdrive-sa.json")
CUT_FOLDER_ID = "1c1JtVATdmmVnzR_sMFxUl61suf01bzbu"  # johnny's "Cut" folder


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def get_token(key_path):
    """OAuth2 JWT bearer flow for a service account (no SDK needed)."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        raise SystemExit("pip install cryptography")

    sa = json.load(open(key_path))
    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = b64url(json.dumps({
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/drive.file",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }).encode())
    signing_input = f"{header}.{claims}".encode()
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    sig = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    jwt = f"{header}.{claims}.{b64url(sig)}"

    body = ("grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer"
            f"&assertion={jwt}").encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["access_token"]


def upload(path, folder_id, token):
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
    ap.add_argument("--key", default=os.environ.get("GDRIVE_SA_JSON", DEFAULT_KEY))
    args = ap.parse_args()
    if not os.path.exists(args.key):
        raise SystemExit(f"no service-account key at {args.key} — see header comment for setup")
    upload(args.file, args.folder_id, get_token(args.key))
