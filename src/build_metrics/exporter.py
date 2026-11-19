from __future__ import annotations

from datetime import datetime
from pathlib import Path

from build_metrics.store import Store


def _parse(value: str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


class ReportExporter:
    def export(self, store: Store, repo: str, start, end, dest: Path) -> Path:
        start_dt = _parse(start)
        end_dt = _parse(end)
        rows = store.conn.execute(
            """
            SELECT id, branch, duration_seconds, updated_at
            FROM workflow_runs
            WHERE full_name = ?
            ORDER BY updated_at
            """,
            (repo,),
        ).fetchall()
        selected = []
        for row in rows:
            ts = _parse(row["updated_at"])
            if start_dt <= ts <= end_dt:
                selected.append(row)
        if not selected:
            raise LookupError("empty period")
        dest = Path(dest)
        lines = ["# Звіт метрик збірки", "", f"Репозиторій: {repo}", ""]
        for row in selected:
            lines.append(f"- прогін {row['id']} ({row['branch']}): тривалість {row['duration_seconds']} с")
        text = "\n".join(lines) + "\n"
        lowered = text.lower()
        for bad in ("token", "authorization", "secret"):
            if bad in lowered:
                raise ValueError("forbidden substring in report")
        dest.write_text(text, encoding="utf-8")
        return dest
