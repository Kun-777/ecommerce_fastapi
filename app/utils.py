from passlib.context import CryptContext
from fastapi import FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from typing import List

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def send_verification_email(email: EmailStr):
    conf = ConnectionConfig(
        MAIL_USERNAME ="alex.fulin.jiang@gmail.com",
        MAIL_PASSWORD = "twpmocqvjpmququg",
        MAIL_FROM = "alex.fulin.jiang@gmail.com",
        MAIL_PORT = 587,
        MAIL_SERVER = "smtp.gmail.com",
        MAIL_STARTTLS = True,
        MAIL_SSL_TLS = False,
        USE_CREDENTIALS = True,
        VALIDATE_CERTS = True
    )

    html = f"""
            <!DOCTYPE html>
                <html>
                <head>
                <meta charset="UTF-8">
                <title>Email Verification</title>
                </head>
                <body style="font-family: Arial, sans-serif;">

                <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse;">
                    <tr>
                    <td align="center" bgcolor="#f2f2f2" style="padding: 40px 0;">
                        <h1>Email Verification</h1>
                        <p>Please verify your email address by clicking the button below:</p>
                        <table border="0" cellpadding="0" cellspacing="0" style="margin-top: 30px;">
                        <tr>
                            <td align="center" bgcolor="#3498db" style="border-radius: 5px;">
                            <a href="http://localhost:3000/verify_email" target="_blank" style="font-size: 16px; font-weight: bold; color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 5px; display: inline-block;">Verify Email</a>
                            </td>
                        </tr>
                        </table>
                    </td>
                    </tr>
                </table>

                </body>
                </html>
            """


    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[email],
        body=html,
        subtype=MessageType.html)

    fm = FastMail(conf)
    await fm.send_message(message)
