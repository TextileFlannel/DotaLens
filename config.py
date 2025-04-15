import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
STRATZ_TOKEN = os.getenv('STRATZ_API_KEY')
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
