from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth_dependencies import get_current_user
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schema import SignupRequest, VerifyOTPRequest, LoginRequest, RefreshTokenRequest, ResendOTPRequest
from app.services.auth_services import signup_owner, verify_otp, login_owner, refresh_access_token, resend_otp


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):

    try:
        message = signup_owner(
            db=db,
            name=request.name,
            email=request.email,
            phone=request.phone,
            password=request.password
        )

        return {
            "message": message
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/verify-otp")
def verify_signup_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):

    try:
        owner = verify_otp(
            db=db,
            email=request.email,
            otp=request.otp
        )

        return {
            "message": "Signup successful",
            "owner_id": owner.id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/resend-otp")
def resend_signup_otp(
    request: ResendOTPRequest,
    db: Session = Depends(get_db)
):

    try:
        message = resend_otp(
            email=request.email
        )

        return {
            "message": message
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    try:
        tokens = login_owner(
            db=db,
            email=request.email,
            password=request.password
        )

        return {
            "message": "Login successful",
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest):

    try:
        access_token = refresh_access_token(
            request.refresh_token
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


@router.get("/me")
def get_me(
    owner_id: int = Depends(get_current_user)
):
    return {
        "owner_id": owner_id
    }
