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
        title = "\u0417\u0432\u0456\u0442 \u043c\u0435\u0442\u0440\u0438\u043a \u0437\u0431\u0456\u0440\u043a\u0438"
        repo_label = "\u0420\u0435\u043f\u043e\u0437\u0438\u0442\u043e\u0440\u0456\u0439"
        duration_label = "\u0442\u0440\u0438\u0432\u0430\u043b\u0456\u0441\u0442\u044c"
        run_label = "\u043f\u0440\u043e\u0433\u0456\u043d"
        lines = [f"# {title}", "", f"{repo_label}: {repo}", ""]
        for row in selected:
            lines.append(
                f"- {run_label} {row['id']} ({row['branch']}): {duration_label} {row['duration_seconds']} \u0441"
            )
        text = "\n".join(lines) + "\n"
        lowered = text.lower()
        for bad in ("token", "authorization", "secret"):
            if bad in lowered:
                raise ValueError("forbidden substring in report")
        dest.write_text(text, encoding="utf-8")
        return dest
