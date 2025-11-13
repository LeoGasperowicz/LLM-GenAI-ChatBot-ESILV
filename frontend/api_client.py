import requests
from typing import Optional, Dict, Any, List
from config import BACKEND_BASE_URL


class APIClientError(Exception):
    pass


def _handle_response(resp: requests.Response) -> Any:
    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise APIClientError(f"Erreur API ({resp.status_code}): {detail}")
    try:
        return resp.json()
    except Exception:
        return resp.text


def chat(user_id: Optional[str], message: str) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/chat/"
    payload = {"user_id": user_id, "message": message}
    resp = requests.post(url, json=payload, timeout=30)
    return _handle_response(resp)


def get_conversation(user_id: str) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/chat/conversation/{user_id}"
    resp = requests.get(url, timeout=10)
    return _handle_response(resp)


def get_admin_stats() -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/admin/stats"
    resp = requests.get(url, timeout=10)
    return _handle_response(resp)


def get_contacts() -> List[Dict[str, Any]]:
    url = f"{BACKEND_BASE_URL}/admin/contacts"
    resp = requests.get(url, timeout=10)
    return _handle_response(resp)