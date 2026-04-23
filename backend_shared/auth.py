from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend_shared.config import get_settings
from backend_shared.db import get_database
from backend_shared.utils import utcnow

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    settings = get_settings()
    expire_at = utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = data.copy()
    to_encode.update({"exp": expire_at})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm), expire_at


def issue_session(db, *, user: dict, service_name: str):
    session_id = uuid4().hex
    expires_at = utcnow() + timedelta(minutes=get_settings().access_token_expire_minutes)
    db.sessions.insert_one(
        {
            "session_id": session_id,
            "user_id": user["id"],
            "role": user["role"],
            "service": service_name,
            "created_at": utcnow(),
            "expires_at": expires_at,
            "revoked_at": None,
        }
    )

    token, token_expiry = create_access_token(
        {
            "sub": str(user["id"]),
            "role": user["role"],
            "sid": session_id,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "session_id": session_id,
        "expires_at": token_expiry,
    }


def get_token_payload(token: str = Depends(oauth2_scheme)):
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - handled at runtime
        raise HTTPException(status_code=401, detail="Invalid authentication") from exc


def revoke_session(session_id: str):
    db = get_database()
    db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {"revoked_at": utcnow()}},
    )


def get_current_user(required_roles: set[str] | None = None):
    def dependency(payload: dict = Depends(get_token_payload)):
        db = get_database()
        try:
            user_id = int(payload.get("sub"))
            session_id = payload["sid"]
        except (TypeError, ValueError, KeyError) as exc:
            raise HTTPException(status_code=401, detail="Invalid authentication") from exc

        session = db.sessions.find_one(
            {
                "session_id": session_id,
                "user_id": user_id,
                "revoked_at": None,
            }
        )
        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        if session.get("expires_at") and session["expires_at"] <= utcnow():
            raise HTTPException(status_code=401, detail="Session expired")

        user = db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if required_roles and user.get("role") not in required_roles:
            raise HTTPException(status_code=403, detail="Not authorized")

        return user

    return dependency
