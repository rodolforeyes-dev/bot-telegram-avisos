import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ICS_PATH = PROJECT_ROOT / "fifa-world-cup-2026.ics"
MATCHES_PATH = DATA_DIR / "matches.json"
DB_PATH = DATA_DIR / "bot.db"
