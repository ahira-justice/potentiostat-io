import os

from dotenv import load_dotenv


load_dotenv()

ABLY_API_KEY = os.environ.get("ABLY_API_KEY")
API_BASE_URL = os.environ.get("API_BASE_URL")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
