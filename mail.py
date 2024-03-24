import smtplib
import ssl
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")


def sent_email(name, email, phone, message):
    message = f"Subject:New Message\n\nName:{name}\nEmail:{email}\nPhone:{phone}\nMessage:{message}"

    port = 465
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, EMAIL, message)
