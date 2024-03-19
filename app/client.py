from datetime import datetime

import requests

import authentication
from config import API_BASE_URL
from constants import MEASUREMENTS_URL, EXPERIMENTS_URL


def compose_headers():
    access_token = authentication.get_client_auth_token()
    return {"Authorization": f"Bearer {access_token}"}


def start_experiment(experiment_id: int) -> bool:
    url = f"{API_BASE_URL}/{EXPERIMENTS_URL}/{experiment_id}/start"

    headers = compose_headers()

    response = requests.put(url, headers=headers)

    return response.ok


def post_measurement(experiment_id: int, current: float, voltage: float) -> bool:
    url = f"{API_BASE_URL}/{MEASUREMENTS_URL}"

    payload = {
        "experiment_id": experiment_id,
        "timestamp": datetime.utcnow().timestamp(),
        "voltage": voltage,
        "current": current
    }

    headers = compose_headers()

    response = requests.post(url, json=payload, headers=headers)

    return response.ok
