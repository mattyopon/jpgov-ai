# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""JWT Authentication for JPGovAI API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import Header, HTTPException
from pydantic import BaseModel

SECRET_KEY = os.environ.get("JPGOV_JWT_SECRET", "change-me-in-production")
TOKEN_EXPIRY = 3600 * 24  # 24 hours

_USER_DB_PATH = os.environ.get("JPGOV_USER_DB", "jpgov_users.db")


# ── Models ───────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """ユーザー登録リクエスト."""

    email: str
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    """ログインリクエスト."""

    email: str
    password: str


class AuthResponse(BaseModel):
    """認証レスポンス."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


@dataclass
class TokenPayload:
    """Decoded JWT payload."""

    user_id: str
    email: str
    exp: float


# ── JWT helpers (stdlib only) ────────────────────────────────────


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: str, email: str) -> str:
    """Create a HS256 JWT token."""
    header = _b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64encode(
        json.dumps(
            {
                "user_id": user_id,
                "email": email,
                "exp": time.time() + TOKEN_EXPIRY,
            }
        ).encode()
    )
    signature = hmac.new(
        SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256
    ).digest()
    sig_b64 = _b64encode(signature)
    return f"{header}.{payload}.{sig_b64}"


def verify_token(token: str) -> TokenPayload | None:
    """Verify a JWT token and return its payload, or None if invalid."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected_sig = _b64encode(
            hmac.new(
                SECRET_KEY.encode(),
                f"{header}.{payload}".encode(),
                hashlib.sha256,
            ).digest()
        )
        if not hmac.compare_digest(sig, expected_sig):
            return None
        data = json.loads(_b64decode(payload))
        if data.get("exp", 0) < time.time():
            return None
        return TokenPayload(
            user_id=data["user_id"], email=data["email"], exp=data["exp"]
        )
    except Exception:
        return None


# ── FastAPI dependency ───────────────────────────────────────────


async def get_current_user(
    authorization: str | None = Header(None),
) -> TokenPayload:
    """Extract and verify JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# ── File-based user storage (SQLite) ─────────────────────────────


def _hash_password(password: str, salt: str) -> str:
    """Hash a password with salt using SHA-256."""
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def _get_user_db() -> sqlite3.Connection:
    """Get or create the user database."""
    db_path = Path(_USER_DB_PATH)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def register_user(email: str, password: str, display_name: str = "") -> dict:
    """Register a new user. Returns user dict or raises HTTPException."""
    conn = _get_user_db()
    try:
        # Check if email already exists
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row:
            raise HTTPException(status_code=409, detail="Email already registered")

        user_id = str(uuid.uuid4())
        salt = uuid.uuid4().hex
        password_hash = _hash_password(password, salt)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        conn.execute(
            "INSERT INTO users (id, email, password_hash, salt, display_name, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email, password_hash, salt, display_name, now),
        )
        conn.commit()
        return {"user_id": user_id, "email": email, "display_name": display_name}
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict | None:
    """Authenticate a user. Returns user dict or None."""
    conn = _get_user_db()
    try:
        row = conn.execute(
            "SELECT id, email, password_hash, salt, display_name FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if not row:
            return None
        expected_hash = _hash_password(password, row["salt"])
        if not hmac.compare_digest(row["password_hash"], expected_hash):
            return None
        return {
            "user_id": row["id"],
            "email": row["email"],
            "display_name": row["display_name"],
        }
    finally:
        conn.close()
