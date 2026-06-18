"""Auth service — authentication routes."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from auth_service.services.user_store import user_store

router = APIRouter()

JWT_ALGORITHM = "HS256"
JWT_SECRET = "dev-secret-change-in-production"
ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=7)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(UTC) + ACCESS_TOKEN_TTL,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + REFRESH_TOKEN_TTL,
        "iat": datetime.now(UTC),
        "type": "refresh",
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, object]:
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(request: Request) -> dict[str, object]:
    auth_header = getattr(request.state, "user_id", None) if hasattr(request.state, "user_id") else None
    if not auth_header:
        auth_header = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if auth_header:
            decoded = decode_token(auth_header)
            return decoded
    raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest) -> TokenResponse:
    existing = user_store.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = user_store.create(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )

    access = create_access_token(str(user.id), user.role)
    refresh = create_refresh_token(str(user.id))

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    user = user_store.get_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(str(user.id), user.role)
    refresh = create_refresh_token(str(user.id))

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest) -> TokenResponse:
    decoded = decode_token(body.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = str(decoded["sub"])
    access = create_access_token(user_id, "developer")
    refresh = create_refresh_token(user_id)

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict[str, object] = Depends(get_current_user)) -> UserResponse:
    user = user_store.get_by_email(str(current_user.get("sub", "")))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )
