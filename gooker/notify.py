import os
from typing import Literal
import smtplib
from email.message import EmailMessage


def send_email(subject: str, body: str, recipients: list[str]):
    account = os.environ["GMAIL_ACCOUNT"]
    password = os.environ["GMAIL_PASSWORD"]

    server = smtplib.SMTP("smtp.gmail.com", 587)
    try:
        server.starttls()
        server.login(account, password)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = account
        msg["To"] = recipients
        msg.set_content(body)

        server.send_message(msg)

    finally:
        server.quit()


async def send_message(method: str, subject: str, body: str, recipients: list[str]):
    if method == "email":
        send_email(subject, body, recipients)
