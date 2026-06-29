import os
import httpx

BACKEND_URL = "http://localhost:8000"


def login(email: str, password: str) -> dict:
    try:
        r = httpx.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", "Login failed")}
    except Exception as e:
        return {"error": str(e)}


def register(email: str, password: str) -> dict:
    try:
        r = httpx.post(
            f"{BACKEND_URL}/auth/register",
            json={"email": email, "password": password},
            timeout=10,
        )
        return r.json() if r.status_code == 201 else {"error": r.json().get("detail", "Register failed")}
    except Exception as e:
        return {"error": str(e)}


def get_dashboard(token: str) -> dict:
    try:
        r = httpx.get(
            f"{BACKEND_URL}/commitments/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def get_commitments(token: str, status=None, owner=None, search=None) -> list:
    try:
        params = {}
        if status: params["status"] = status
        if owner: params["owner"] = owner
        if search: params["search"] = search
        r = httpx.get(
            f"{BACKEND_URL}/commitments/",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def get_commitment_detail(token: str, commitment_id: int) -> dict:
    try:
        r = httpx.get(
            f"{BACKEND_URL}/commitments/{commitment_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def update_commitment_status(token: str, commitment_id: int, status: str, note: str = "") -> dict:
    try:
        r = httpx.patch(
            f"{BACKEND_URL}/commitments/{commitment_id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": status, "note": note},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", "Failed")}
    except Exception as e:
        return {"error": str(e)}


def upload_transcript(token: str, file_path: str, filename: str) -> dict:
    try:
        with open(file_path, "rb") as f:
            r = httpx.post(
                f"{BACKEND_URL}/uploads/transcript",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (filename, f)},
                timeout=60,
            )
        return r.json() if r.status_code == 201 else {"error": r.json().get("detail", "Upload failed")}
    except Exception as e:
        return {"error": str(e)}


def upload_audio(token: str, file_path: str, filename: str) -> dict:
    try:
        with open(file_path, "rb") as f:
            r = httpx.post(
                f"{BACKEND_URL}/uploads/audio",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (filename, f)},
                timeout=120,
            )
        return r.json() if r.status_code == 201 else {"error": r.json().get("detail", "Upload failed")}
    except Exception as e:
        return {"error": str(e)}


def get_uploads(token: str) -> list:
    try:
        r = httpx.get(
            f"{BACKEND_URL}/uploads/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []
