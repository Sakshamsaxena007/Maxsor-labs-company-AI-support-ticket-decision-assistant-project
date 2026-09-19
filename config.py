import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / "app.db"
KB_DIR = BASE_DIR / "knowledge_base"
DATA_DIR = BASE_DIR / "data"
EMBEDDINGS_PATH = BASE_DIR / "embeddings.npz"

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60

GEMINI_API_KEY = os.getenv("AQ.Ab8RN6KjpgzTf91ErbwfJLSvar8nqRfnodiH_7nOBJGYjp-P6g", "")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
