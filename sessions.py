from secrets import token_urlsafe
from typing import Optional


_sessions: dict[str, dict[str, int | str]] = {}


def create_session(user: dict) -> str:
    token = token_urlsafe(32)
    _sessions[token] = {"user_id": user["user_id"], "role": user["role"]}
    return token


def get_session(token: str) -> Optional[dict[str, int | str]]:
    return _sessions.get(token)


def revoke_session(token: str) -> None:
    _sessions.pop(token, None)
