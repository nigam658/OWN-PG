import os
import smtplib
from email.message import EmailMessage


def send_otp_email(receiver_email: str, otp: str):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    message = EmailMessage()
    message["Subject"] = "MyPG - Email Verification OTP"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.set_content(
        f"""Hello,

    Your MyPG verification OTP is: {otp}

    This OTP will expire in 5 minutes.

    If you did not request this, please ignore this email.

    Regards,
    MyPG Team
    """
        )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)