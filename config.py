import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_IDS = os.getenv('ADMIN_IDS')