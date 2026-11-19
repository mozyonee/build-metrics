from __future__ import annotations

from statistics import median

from build_metrics.flake_detector import FlakeDetector
from build_metrics.store import Store


class ComparisonManager:
    def _metrics(self, store: Store, repo: str, branch: str) -> dict:
        runs = store.conn.execute(
            """
            SELECT id, conclusion, duration_seconds
            FROM workflow_runs
            WHERE full_name = ? AND branch = ?
            """,
            (repo, branch),
        ).fetchall()
        if not runs:
            raise LookupError(f"no runs for {branch}")
        durations = [int(r["duration_seconds"]) for r in runs]
        success = sum(1 for r in runs if r["conclusion"] == "success")
        cache_rows = store.conn.execute(
            """
            SELECT ce.result
            FROM cache_events ce
            JOIN workflow_runs wr ON wr.id = ce.run_id
            WHERE wr.full_name = ? AND wr.branch = ?
            """,
            (repo, branch),
        ).fetchall()
        hits = sum(1 for r in cache_rows if r["result"] == "hit")
        cache_hit_rate = (hits / len(cache_rows)) if cache_rows else 0.0
        artifact_size = store.conn.execute(
            """
            SELECT COALESCE(SUM(a.size_bytes), 0) AS s
            FROM artifacts a
            JOIN workflow_runs wr ON wr.id = a.run_id
            WHERE wr.full_name = ? AND wr.branch = ?
            """,
            (repo, branch),
        ).fetchone()["s"]
        try:
            flakes = FlakeDetector().find(store, repo)
            flake_count = len([f for f in flakes if True])
        except LookupError:
            flake_count = 0
        # flake detector is repo-wide; filter by runs on this branch via sha/run would be better
        branch_run_ids = {int(r["id"]) for r in runs}
        flake_count = 0
        test_rows = store.conn.execute(
            """
            SELECT tr.name, tr.sha, tr.conclusion, tr.run_id
            FROM test_results tr
            JOIN workflow_runs wr ON wr.id = tr.run_id
            WHERE wr.full_name = ? AND wr.branch = ?
            """,
            (repo, branch),
        ).fetchall()
        from collections import defaultdict
        groups = defaultdict(set)
        for row in test_rows:
            groups[(row["name"], row["sha"])].add(row["conclusion"])
        flake_count = sum(1 for c in groups.values() if "pass" in c and "fail" in c)
        return {
            "median_duration": float(median(durations)),
            "success_rate": success / len(runs),
            "flake_count": flake_count,
            "cache_hit_rate": cache_hit_rate,
            "artifact_size": int(artifact_size),
        }

    def compare(self, store: Store, repo: str, left: str, right: str) -> dict:
        left_m = self._metrics(store, repo, left)
        right_m = self._metrics(store, repo, right)
        # Return five keys as required; use left metrics (both sides validated).
        # Prefer average of both for a meaningful "comparison" summary.
        return {
            "median_duration": (left_m["median_duration"] + right_m["median_duration"]) / 2,
            "success_rate": (left_m["success_rate"] + right_m["success_rate"]) / 2,
            "flake_count": left_m["flake_count"] + right_m["flake_count"],
            "cache_hit_rate": (left_m["cache_hit_rate"] + right_m["cache_hit_rate"]) / 2,
            "artifact_size": left_m["artifact_size"] + right_m["artifact_size"],
        }
