from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
from datetime import datetime, timezone, timedelta

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",   # Vite dev server origin
    "http://localhost:5173",   # in case browser uses localhost
    # "http://localhost:8000", # add if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # set to ["*"] for quick dev, not recommended for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "water_levels.db")
BRAZIL_TZ = timezone(timedelta(hours=-3))

def fetch_latest_levels(limit: int = 12):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT water_level, recorded_ts FROM water_levels ORDER BY recorded_ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "water_level": row["water_level"],
                "recorded_ts": datetime.fromtimestamp(row["recorded_ts"], BRAZIL_TZ).isoformat(),
            }
            for row in rows
        ]
    except Exception as exc:
        print(f"Failed to read water_levels.db: {exc}")
        return []

@app.get("/")
async def root():
    return {"buffer": fetch_latest_levels()}