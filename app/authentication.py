from datetime import timedelta, datetime

import requests

from config import API_BASE_URL, CLIENT_ID, CLIENT_SECRET
from constants import AUTH_URL

ACCESS_TOKEN = {}


def is_token_expired() -> bool:
    expiry = ACCESS_TOKEN.get("expiry")

    if not expiry:
        return True

    return expiry > datetime.utcnow()


def get_client_auth_token() -> dict:
    global ACCESS_TOKEN

    if not is_token_expired():
        return ACCESS_TOKEN["access_token"]

    return fetch_client_access_token()


def fetch_client_access_token() -> dict:
    global ACCESS_TOKEN

    url = f"{API_BASE_URL}/{AUTH_URL}/client-login"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}

    response = requests.post(url, json=payload).json()

    access_token = response.get("access_token")
    expires_in = response.get("expires_in")
    expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    ACCESS_TOKEN = {"access_token": access_token, "expiry": expiry}

    return access_token
