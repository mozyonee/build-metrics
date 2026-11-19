from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_metrics.import_manager import ImportManager
from build_metrics.store import Store
from build_metrics.trend_analyzer import TrendAnalyzer

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "run_success.json"


def _payload(run_id: int, updated: str) -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["run"]["id"] = run_id
    data["run"]["updated_at"] = updated
    data["run"]["run_started_at"] = updated.replace("05:30", "00:30").replace("06:30", "01:30").replace("07:30", "02:30")
    # keep duration consistent via started/updated
    started = updated[:11] + "10:00:30Z"
    data["run"]["created_at"] = updated[:11] + "10:00:00Z"
    data["run"]["run_started_at"] = started
    data["run"]["updated_at"] = updated
    data["jobs"][0]["id"] = run_id
    data["artifacts"][0]["id"] = run_id
    return data


def test_trend_returns_three_points(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    mgr = ImportManager()
    mgr.import_run(_payload(1, "2026-11-01T10:05:30Z"), store)
    mgr.import_run(_payload(2, "2026-11-01T11:05:30Z"), store)
    mgr.import_run(_payload(3, "2026-11-01T12:05:30Z"), store)
    series = TrendAnalyzer().duration_series(store, "acme/build_metrics", "main")
    assert len(series) == 3
    assert series[0][0] < series[1][0] < series[2][0]
    assert all(isinstance(p[1], int) for p in series)


def test_trend_empty_branch_raises(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    mgr = ImportManager()
    mgr.import_run(_payload(1, "2026-11-01T10:05:30Z"), store)
    with pytest.raises(LookupError):
        TrendAnalyzer().duration_series(store, "acme/build_metrics", "empty")
