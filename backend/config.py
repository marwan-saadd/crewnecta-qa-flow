"""Backend configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MOCK_TRANSCRIPTS_PATH = DATA_DIR / "mock_transcripts.json"

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

HOST = "0.0.0.0"
PORT = 8000
