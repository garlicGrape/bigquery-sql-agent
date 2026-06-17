import os
from dotenv import load_dotenv

load_dotenv()

MODEL: str = os.getenv("MODEL", "gemini-2.5-flash")
VERTEX_LOCATION: str = os.getenv("VERTEX_LOCATION", "us-central1")

BQ_PROJECT_ID: str = os.getenv("BQ_PROJECT_ID", "bigquery-public-data")
BQ_DATASET: str = os.getenv("BQ_DATASET", "new_york_citibike")
BQ_BILLING_PROJECT: str = os.getenv("BQ_BILLING_PROJECT", "msbai-dwd-sk7374")

MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
BYTE_CAP: int = int(os.getenv("BYTE_CAP", str(10 * 1024**3)))  # 10 GB
DEFAULT_LIMIT: int = int(os.getenv("DEFAULT_LIMIT", "100"))
MAX_RESULT_ROWS: int = int(os.getenv("MAX_RESULT_ROWS", "50"))
