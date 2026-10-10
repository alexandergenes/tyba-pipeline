import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "output"

DB_DSN = (
    f"host={os.getenv('DB_HOST', 'localhost')} "
    f"port={os.getenv('DB_PORT', '5432')} "
    f"dbname={os.getenv('DB_NAME', 'movimientos')} "
    f"user={os.getenv('DB_USER', 'tyba')} "
    f"password={os.getenv('DB_PASSWORD', 'tyba')}"
)