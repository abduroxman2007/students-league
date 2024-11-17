# utils.py

from .models import EmailVerification
from django.core.mail import EmailMessage
import random
import string

def generate_verification_code():
    """Generate a random 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=6))

def create_and_save_email_verification(user):
    """Create and save EmailVerification instance with generated code."""
    verification_code = generate_verification_code()

    # Create and save the EmailVerification instance with the code
    email_verification = EmailVerification.objects.create(
        user=user,
        verification_code=verification_code
    )
    return email_verification

def send_verification_email(user, emaul=None):
    """Send verification email with the verification code."""
    email_verification = EmailVerification.objects.get(user=user)
    verification_code = email_verification.verification_code
    mail_subject = 'Activate your account'
    message = f"""
    Hi {user.first_name},

    Please enter the code below to activate your account:
    {verification_code}

    If you did not register for this account, please ignore this email.
    """
    # Use the provided email or fallback to user.email if not provided
    email_to_send = email if email else user.email

    email = EmailMessage(mail_subject, message, to=[email_to_send])
    
    # Send email
    if not email.send():
        raise Exception("Could not send email. Please try again later.")

import secrets  # Import secrets for secure token generation
from django.core.mail import EmailMessage  # Import EmailMessage for sending emails

def generate_random_token(length=64):
    """Generate a secure random token."""
    return secrets.token_hex(length // 2)  # Generate a token of the specified length

def send_password_reset_email(user, token):
    """Send a password reset email to the user."""
    mail_subject = 'Reset Your Password'
    message = f"""
    Hi {user.first_name},

    You requested a password reset. Click the link below to reset your password:
    http://yourdomain.com/reset-password/{token}/

    If you did not request this, please ignore this email.
    """

    email = EmailMessage(mail_subject, message, to=[user.email])
    
    # Send email
    if not email.send():
        raise Exception("Could not send password reset email. Please try again later.")