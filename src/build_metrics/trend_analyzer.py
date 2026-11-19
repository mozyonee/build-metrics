from __future__ import annotations

from build_metrics.store import Store


class TrendAnalyzer:
    def duration_series(self, store: Store, repo: str, branch: str) -> list[tuple]:
        rows = store.conn.execute(
            """
            SELECT updated_at, duration_seconds
            FROM workflow_runs
            WHERE full_name = ? AND branch = ? AND conclusion = 'success'
            ORDER BY updated_at
            """,
            (repo, branch),
        ).fetchall()
        if not rows:
            raise LookupError("no successful runs")
        return [(r["updated_at"], int(r["duration_seconds"])) for r in rows]
