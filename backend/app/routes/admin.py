
from datetime import datetime, timedelta, timezone
import os

import jwt
from pwdlib import PasswordHash

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import SessionLocal
from app.models import Admin
from jose import JWTError, jwt

from fastapi import Depends, HTTPException, status

security = HTTPBearer()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(lambda: SessionLocal())
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    admin = db.query(Admin).filter(Admin.username == username).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found"
        )

    return admin


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


# Configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "replace-this-with-a-long-random-secret-key"
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()

security = HTTPBearer()


# Database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Request schemas
class AdminRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class AdminLogin(BaseModel):
    username: str
    password: str


# Generate JWT token
def create_access_token(username: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# Verify JWT token and get logged-in admin
def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if not username:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    admin = db.query(Admin).filter(
        Admin.username == username
    ).first()

    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Admin not found"
        )

    return admin


# ADMIN REGISTRATION
@router.post("/register")
def register_admin(
    request: AdminRegister,
    db: Session = Depends(get_db)
):
    if db.query(Admin).first():
        raise HTTPException(
            status_code=403,
            detail="Admin registration is closed"
        )

    existing = db.query(Admin).filter(
        (Admin.username == request.username) |
        (Admin.email == request.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    admin = Admin(
        username=request.username,
        email=request.email,
        hashed_password=password_hash.hash(request.password)
    )

    try:
        db.add(admin)
        db.commit()
        db.refresh(admin)

        return {
            "success": True,
            "message": "Admin registered successfully",
            "admin_id": admin.id
        }

    except Exception as e:
        db.rollback()
        print("ADMIN REGISTRATION ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Admin registration failed. Check backend terminal."
        )


# ADMIN LOGIN
@router.post("/login")
def login_admin(
    request: AdminLogin,
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(
        Admin.username == request.username
    ).first()

    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not password_hash.verify(
        request.password,
        admin.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token(admin.username)

    return {
        "success": True,
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "username": admin.username
    }


# PROTECTED ADMIN PROFILE
@router.get("/profile")
def admin_profile(
    admin: Admin = Depends(get_current_admin)
):
    return {
        "success": True,
        "username": admin.username,
        "email": admin.email
    }
