from __future__ import annotations

from datetime import datetime

from build_metrics.store import Store

_ALLOWED_CONCLUSIONS = {"success", "failure", "cancelled"}
_ALLOWED_CACHE = {"hit", "miss"}


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ImportManager:
    def import_run(self, payload: dict, store: Store) -> int:
        run = payload["run"]
        if run.get("status") != "completed":
            raise ValueError("status must be completed")
        if run.get("conclusion") not in _ALLOWED_CONCLUSIONS:
            raise ValueError("invalid conclusion")
        for cache in payload.get("caches", []):
            if cache.get("result") not in _ALLOWED_CACHE:
                raise ValueError("invalid cache result")

        started = _parse_ts(run["run_started_at"])
        created = _parse_ts(run["created_at"])
        updated = _parse_ts(run["updated_at"])
        duration_seconds = int((updated - started).total_seconds())
        queue_seconds = int((started - created).total_seconds())

        enriched = dict(run)
        enriched["duration_seconds"] = duration_seconds
        enriched["queue_seconds"] = queue_seconds
        full_name = run["repository"]["full_name"]
        return store.replace_run(
            full_name=full_name,
            run=enriched,
            jobs=payload.get("jobs", []),
            tests=payload.get("tests", []),
            caches=payload.get("caches", []),
            artifacts=payload.get("artifacts", []),
        )
