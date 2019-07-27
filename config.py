import os
from pathlib import Path

sql_config = {
    "host": "127.0.0.1",
    "user": "captain",
    # "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "db": "db",
    "charset": 'utf8mb4'
}
TOKEN = os.getenv("TOKEN")

I18N_DOMAIN = 'atlantida'

BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'
