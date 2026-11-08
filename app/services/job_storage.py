
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "jobs.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                job_status TEXT NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_job(job_id):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO jobs (job_id, job_status, result)
            VALUES (?, ?, ?)
            """,
            (job_id, "Queued", None)
        )


def update_job(job_id, status, result=None):
    result_json = json.dumps(result) if result is not None else None

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE jobs
            SET job_status = ?, result = ?
            WHERE job_id = ?
            """,
            (status, result_json, job_id)
        )


def get_job(job_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM jobs WHERE job_id = ?",
            (job_id,)
        ).fetchone()

    if row is None:
        return None

    return {
        "job_id": row["job_id"],
        "job_status": row["job_status"],
        "result": json.loads(row["result"]) if row["result"] else None
    }