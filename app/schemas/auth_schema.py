from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if not value.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters and spaces")

        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if " " in value:
            raise ValueError("Email cannot contain spaces")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if " " in value:
            raise ValueError("Password cannot contain spaces")

        if not re.search(r"[A-Za-z]", value):
            raise ValueError("Password must contain at least one letter")

        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")

        return value


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if " " in value:
            raise ValueError("Email cannot contain spaces")

        return value

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value):
        if not value.isdigit():
            raise ValueError("OTP must contain only digits")

        return value

class ResendOTPRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if " " in value:
            raise ValueError("Email cannot contain spaces")

        return value

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if " " in value:
            raise ValueError("Email cannot contain spaces")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not value:
            raise ValueError("Password cannot be empty")

        if " " in value:
            raise ValueError("Password cannot contain spaces")

        return value


class RefreshTokenRequest(BaseModel):
    refresh_token: str