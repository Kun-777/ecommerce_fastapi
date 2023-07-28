from passlib.context import CryptContext
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
import smtplib
import requests
import json
import urllib.parse
from .config import settings

METER_TO_MILE = 0.000621371

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def send_verification_email(email: EmailStr):
    conf = ConnectionConfig(
        MAIL_USERNAME = settings.smtp_email,
        MAIL_PASSWORD = settings.smtp_pwd,
        MAIL_FROM = settings.smtp_email,
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
                            <a href="{settings.client_hostname}/verify_email" target="_blank" style="font-size: 16px; font-weight: bold; color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 5px; display: inline-block;">Verify Email</a>
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

def send_txt_message(phone_number, carrier, message):
    recipient = phone_number + carrier
    auth = (settings.smtp_email, settings.smtp_pwd)
 
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(auth[0], auth[1])
 
    server.sendmail(auth[0], recipient, message)

'''
Check if the given address is within our delivery range
Returns two values: (a boolean that indicates if the address is within our range, error message)
'''
def check_addr_within_range(customer_addr):
    origin = urllib.parse.quote(settings.store_addr)
    destination = urllib.parse.quote(customer_addr)
    GOOGLE_MAP_API_KEY = settings.google_map_api_key

    url = f'https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&units=imperial&key={GOOGLE_MAP_API_KEY}'

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    res_dict = json.loads(response.text)
    if res_dict['status'] != 'OK':
        return False, 'Sorry, something went wrong.'
    if res_dict['rows'][0]['elements'][0]['status'] != 'OK':
        return False, 'The address you entered could not be found.'
    else:
        dist_meter = res_dict['rows'][0]['elements'][0]['distance']['value'] 
        dist_mi = dist_meter * METER_TO_MILE
        if dist_mi > settings.delivery_range:
            return False, 'Sorry, the address you entered is out of our delivery range.'
        else:
            return True, ''

