"""
JWT authentication for SupportPilot.
"""
import os
import time
from functools import wraps
from typing import Optional

import jwt
from flask import request, jsonify, session, redirect, url_for, g

# Load optional .env from project root (no extra dependency)
def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


_load_dotenv()

JWT_SECRET = os.environ.get("JWT_SECRET", "supportpilot-jwt-secret-change-me-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "24"))


def create_access_token(
    username: str,
    full_name: str = "",
    role: str = "employee",
    email: str = "",
    auth_provider: str = "password",
) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "name": full_name or username,
        "role": role,
        "email": email,
        "provider": auth_provider,
        "iat": now,
        "exp": now + JWT_EXPIRE_HOURS * 3600,
        "iss": "supportpilot",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT <2 returns bytes; always return str for cookies/headers
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_access_token(token: str) -> Optional[dict]:
    if not token:
        return None
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer="supportpilot",
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_bearer_token() -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get("sp_token")



def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "username" in session:
            g.current_user = {
                "username": session.get("username"),
                "full_name": session.get("full_name"),
                "role": session.get("role", "employee"),
                "email": session.get("email", ""),
                "provider": session.get("auth_provider", "password"),
            }
            return f(*args, **kwargs)

        token = extract_bearer_token()
        payload = decode_access_token(token) if token else None
        if payload:
            g.current_user = {
                "username": payload.get("sub"),
                "full_name": payload.get("name"),
                "role": payload.get("role", "employee"),
                "email": payload.get("email", ""),
                "provider": payload.get("provider", "jwt"),
            }
            session["username"] = g.current_user["username"]
            session["full_name"] = g.current_user["full_name"]
            session["role"] = g.current_user["role"]
            session["email"] = g.current_user["email"]
            session["auth_provider"] = g.current_user["provider"]
            return f(*args, **kwargs)

        if request.path.startswith("/api/"):
            return jsonify({"error": "unauthorized", "message": "Valid JWT required"}), 401
        return redirect(url_for("login"))

    return wrapped
