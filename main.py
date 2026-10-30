"""Safe configuration API scaffold for the MTTL-W01 project.

This service stores outlet labels only. It deliberately does not speak to the
power strip or issue relay commands.
"""

import os
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DB_PATH = DATA_DIR / "config.sqlite3"
API_TOKEN = os.environ.get("API_TOKEN", "")

app = FastAPI(
    title="SFN Power Backend",
    version="0.1.0",
    description="Configuration-only API scaffold; device switching is disabled.",
)


def get_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize() -> None:
    with closing(get_db()) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS outlets (
                outlet_number INTEGER PRIMARY KEY CHECK(outlet_number BETWEEN 1 AND 4),
                name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 64)
            )"""
        )
        for number in range(1, 5):
            db.execute(
                "INSERT OR IGNORE INTO outlets(outlet_number, name) VALUES (?, ?)",
                (number, f"Outlet {number}"),
            )
        db.commit()


initialize()


def require_api_token(authorization: str | None = Header(default=None)) -> None:
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="API_TOKEN is not configured")
    expected = f"Bearer {API_TOKEN}"
    if authorization is None or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


class OutletName(BaseModel):
    name: str = Field(min_length=1, max_length=64, pattern=r".*\S.*")


class OutletNames(BaseModel):
    outlets: list[OutletName] = Field(min_length=4, max_length=4)


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "device_control": "disabled"}


@app.get("/api/outlets", dependencies=[Depends(require_api_token)])
def list_outlets() -> dict[str, list[dict[str, int | str]]]:
    with closing(get_db()) as db:
        rows = db.execute(
            "SELECT outlet_number, name FROM outlets ORDER BY outlet_number"
        ).fetchall()
    return {
        "outlets": [
            {"number": row["outlet_number"], "name": row["name"]} for row in rows
        ]
    }


@app.put("/api/outlets", dependencies=[Depends(require_api_token)])
def update_outlets(payload: OutletNames) -> dict[str, list[dict[str, int | str]]]:
    names = [item.name.strip() for item in payload.outlets]
    if any(not name for name in names):
        raise HTTPException(status_code=422, detail="Names cannot be blank")
    with closing(get_db()) as db:
        db.executemany(
            "UPDATE outlets SET name = ? WHERE outlet_number = ?",
            [(name, number) for number, name in enumerate(names, start=1)],
        )
        db.commit()
    return list_outlets()
