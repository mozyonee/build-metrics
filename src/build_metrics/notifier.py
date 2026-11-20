from __future__ import annotations

from statistics import median

from build_metrics.store import Store


class DegradationNotifier:
    def evaluate(self, store: Store, repo: str, branch: str) -> dict | None:
        rows = store.conn.execute(
            """
            SELECT duration_seconds
            FROM workflow_runs
            WHERE full_name = ? AND branch = ? AND conclusion = 'success'
            ORDER BY updated_at
            """,
            (repo, branch),
        ).fetchall()
        if len(rows) < 40:
            raise LookupError("need 40 successful runs")
        window = rows[-40:]
        previous = [int(r["duration_seconds"]) for r in window[:20]]
        recent = [int(r["duration_seconds"]) for r in window[20:]]
        prev_med = float(median(previous))
        recent_med = float(median(recent))
        if recent_med > prev_med * 1.20:
            return store.insert_alert(branch, prev_med, recent_med, True)
        return None
