from __future__ import annotations

import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS repositories (
                full_name TEXT PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS workflow_runs (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                branch TEXT NOT NULL,
                sha TEXT NOT NULL,
                status TEXT NOT NULL,
                conclusion TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                queue_seconds INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                conclusion TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sha TEXT NOT NULL,
                conclusion TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cache_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                result TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                size_bytes INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch TEXT NOT NULL,
                previous_median REAL NOT NULL,
                recent_median REAL NOT NULL,
                fired INTEGER NOT NULL
            );
            """
        )
        self.conn.commit()

    def replace_run(
        self,
        *,
        full_name: str,
        run: dict,
        jobs: list[dict],
        tests: list[dict],
        caches: list[dict],
        artifacts: list[dict],
    ) -> int:
        run_id = int(run["id"])
        self.conn.execute(
            "INSERT OR IGNORE INTO repositories(full_name) VALUES (?)",
            (full_name,),
        )
        self.conn.execute("DELETE FROM jobs WHERE run_id = ?", (run_id,))
        self.conn.execute("DELETE FROM test_results WHERE run_id = ?", (run_id,))
        self.conn.execute("DELETE FROM cache_events WHERE run_id = ?", (run_id,))
        self.conn.execute("DELETE FROM artifacts WHERE run_id = ?", (run_id,))
        self.conn.execute("DELETE FROM workflow_runs WHERE id = ?", (run_id,))
        self.conn.execute(
            """
            INSERT INTO workflow_runs(
                id, full_name, branch, sha, status, conclusion,
                duration_seconds, queue_seconds, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                full_name,
                run["head_branch"],
                run["head_sha"],
                run["status"],
                run["conclusion"],
                run["duration_seconds"],
                run["queue_seconds"],
                run["updated_at"],
            ),
        )
        for job in jobs:
            self.conn.execute(
                "INSERT INTO jobs(id, run_id, name, conclusion) VALUES (?, ?, ?, ?)",
                (job["id"], run_id, job["name"], job["conclusion"]),
            )
        for test in tests:
            self.conn.execute(
                "INSERT INTO test_results(run_id, name, sha, conclusion) VALUES (?, ?, ?, ?)",
                (run_id, test["name"], test["sha"], test["conclusion"]),
            )
        for cache in caches:
            self.conn.execute(
                "INSERT INTO cache_events(run_id, key, result) VALUES (?, ?, ?)",
                (run_id, cache["key"], cache["result"]),
            )
        for artifact in artifacts:
            self.conn.execute(
                "INSERT INTO artifacts(id, run_id, name, size_bytes) VALUES (?, ?, ?, ?)",
                (artifact["id"], run_id, artifact["name"], artifact["size_in_bytes"]),
            )
        self.conn.commit()
        return run_id

    def count_runs(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM workflow_runs").fetchone()
        return int(row["c"])

    def insert_alert(self, branch: str, previous_median: float, recent_median: float, fired: bool) -> dict:
        cur = self.conn.execute(
            """
            INSERT INTO alerts(branch, previous_median, recent_median, fired)
            VALUES (?, ?, ?, ?)
            """,
            (branch, previous_median, recent_median, 1 if fired else 0),
        )
        self.conn.commit()
        return {
            "id": cur.lastrowid,
            "branch": branch,
            "previous_median": previous_median,
            "recent_median": recent_median,
            "fired": fired,
        }
