import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.config import settings

SECRET_KEY = os.environ.get("SECRET_KEY", "enterprise-governance-secret-key-change-in-prod-123456")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(User).filter(User.username == username).first()
        return user
    except jwt.PyJWTError:
        return None


def get_current_role(
    x_user_role: str = Header("Analyst", alias="X-User-Role"),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> str:
    """
    Extracts the user role. Checks the JWT first; if absent or invalid,
    falls back to the legacy X-User-Role header for backward compatibility.
    """
    if current_user and type(current_user).__name__ != "Depends":
        return current_user.role.title()
    return x_user_role.title() if x_user_role else "Analyst"


def get_current_tenant(
    x_tenant_id: str = Header("1", alias="X-Tenant-ID"),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> int:
    """
    Extracts the tenant ID. Checks the JWT first; if absent or invalid,
    falls back to the legacy X-Tenant-ID header.
    """
    if current_user and type(current_user).__name__ != "Depends" and current_user.tenant_id is not None:
        return current_user.tenant_id
    try:
        return int(x_tenant_id)
    except (ValueError, TypeError):
        return 1
