import os
import smtplib
from email.message import EmailMessage

from crewai.tools import tool

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")


@tool
def send_email(message: str) -> str:
    """
    Use this tool to send email to the user.
    Args:
        message: The body of the email.
    Returns:
        A string indicating the status of the email
    """

    msg = EmailMessage()

    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = "Stock Recommendations"

    msg.set_content(message)

    with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    return "Email Sent Successfully"
