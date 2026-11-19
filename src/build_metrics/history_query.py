from __future__ import annotations

from build_metrics.store import Store


class HistoryQuery:
    def list_runs(self, store: Store, repo: str, branch: str) -> list[dict]:
        exists = store.conn.execute(
            "SELECT 1 FROM repositories WHERE full_name = ?",
            (repo,),
        ).fetchone()
        if exists is None:
            raise LookupError(f"unknown repository: {repo}")
        rows = store.conn.execute(
            """
            SELECT wr.duration_seconds AS duration,
                   wr.queue_seconds AS queue,
                   wr.conclusion AS conclusion,
                   (
                       SELECT ce.result FROM cache_events ce
                       WHERE ce.run_id = wr.id ORDER BY ce.id LIMIT 1
                   ) AS cache,
                   (
                       SELECT COALESCE(SUM(a.size_bytes), 0) FROM artifacts a
                       WHERE a.run_id = wr.id
                   ) AS artifact_size
            FROM workflow_runs wr
            WHERE wr.full_name = ? AND wr.branch = ?
            ORDER BY wr.updated_at
            """,
            (repo, branch),
        ).fetchall()
        return [dict(r) for r in rows]
