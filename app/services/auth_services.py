from datetime import datetime, timedelta, timezone
from jose import jwt
import secrets
import os

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.services.email_services import send_otp_email
from app.repository.owner_repository import (
    get_owner_by_email,
    get_owner_by_phone,
    create_owner
)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

pending_signups = {}


# -------------
#fucntions
def hash_password(password: str):
    return pwd_context.hash(password)


def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


def signup_owner( db: Session, name: str, email: str, phone: str, password: str):

    # Check email
    existing_email = get_owner_by_email(db, email)

    if existing_email:
        raise ValueError("Email already registered")

    # Check phone
    existing_phone = get_owner_by_phone(db, phone)

    if existing_phone:
        raise ValueError("Phone number already registered")

    # Hash password
    password_hash = hash_password(password)

    # Generate OTP
    otp = generate_otp()

    # OTP expires after 5 minutes
    expires_at = datetime.now() + timedelta(minutes=5)

    # Store temporary signup data
    pending_signups[email] = {
        "name": name,
        "phone": phone,
        "password_hash": password_hash,
        "otp": otp,
        "expires_at": expires_at,
    }

    send_otp_email(email, otp)

    return "OTP sent successfully"

# resend fucntion
def resend_otp(email: str):

    signup_data = pending_signups.get(email)

    if not signup_data:
        raise ValueError("Signup request not found")

    # Generate a new OTP
    otp = generate_otp()

    # Give the new OTP another 5 minutes
    expires_at = datetime.now() + timedelta(minutes=5)

    # Update existing signup data
    signup_data["otp"] = otp
    signup_data["expires_at"] = expires_at

    # Send new OTP
    send_otp_email(email, otp)

    return "OTP resent successfully"


def verify_otp(db: Session, email: str, otp: str):

    signup_data = pending_signups.get(email)

    if not signup_data:
        raise ValueError("Signup request not found")

    if signup_data["otp"] != otp:
        raise ValueError("Invalid OTP")

    if datetime.now() > signup_data["expires_at"]:
        del pending_signups[email]
        raise ValueError("OTP has expired")

    owner = create_owner(
        db=db,
        name=signup_data["name"],
        email=email,
        phone=signup_data["phone"],
        password=signup_data["password_hash"]
    )

    del pending_signups[email]

    return owner



def login_owner(db: Session, email: str, password: str):

    # Find owner by email
    owner = get_owner_by_email(db, email)

    if not owner:
        raise ValueError("Invalid email or password")

    # Verify password
    if not pwd_context.verify(password, owner.password):
        raise ValueError("Invalid email or password")

    access_token = create_access_token(owner.id)
    refresh_token = create_refresh_token(owner.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


def create_access_token(owner_id: int):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(owner_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# for first time
def create_refresh_token(owner_id: int):

    expire = datetime.now(timezone.utc) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(owner_id),
        "type": "refresh",
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

# if refresh token expire 
def refresh_access_token(refresh_token: str):

    try:
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except Exception:
        raise ValueError("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    owner_id = payload.get("sub")

    if not owner_id:
        raise ValueError("Invalid refresh token")

    return create_access_token(int(owner_id))