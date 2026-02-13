"""
Auth routes - Simple password authentication
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError

from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_at: str


class VerifyResponse(BaseModel):
    valid: bool
    expires_at: str | None = None


def create_token() -> tuple[str, datetime]:
    """Create a JWT token"""
    expires_at = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    payload = {
        "exp": expires_at,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def verify_token(token: str) -> dict | None:
    """Verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to verify authentication"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with password"""
    if request.password != settings.AUTH_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    token, expires_at = create_token()
    return LoginResponse(
        token=token,
        expires_at=expires_at.isoformat()
    )


@router.get("/verify", response_model=VerifyResponse)
async def verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token is valid"""
    if not credentials:
        return VerifyResponse(valid=False)

    payload = verify_token(credentials.credentials)
    if not payload:
        return VerifyResponse(valid=False)

    expires_at = datetime.fromtimestamp(payload["exp"])
    return VerifyResponse(
        valid=True,
        expires_at=expires_at.isoformat()
    )
