from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from build_metrics.import_manager import ImportManager
from build_metrics.notifier import DegradationNotifier
from build_metrics.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "run_success.json"


def _make_run(run_id: int, duration: int, when: datetime) -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    started = when
    created = when - timedelta(seconds=30)
    updated = when + timedelta(seconds=duration)
    data["run"]["id"] = run_id
    data["run"]["created_at"] = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["run"]["run_started_at"] = started.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["run"]["updated_at"] = updated.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["jobs"][0]["id"] = run_id
    data["artifacts"][0]["id"] = 1000 + run_id
    return data


def _seed(store: Store, recent_duration: int) -> None:
    mgr = ImportManager()
    base = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)
    for i in range(20):
        mgr.import_run(_make_run(i + 1, 100, base + timedelta(hours=i)), store)
    for i in range(20):
        mgr.import_run(_make_run(i + 21, recent_duration, base + timedelta(hours=20 + i)), store)


def test_notifier_fires_when_median_grows_over_20_percent(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    _seed(store, 130)
    alert = DegradationNotifier().evaluate(store, "acme/build_metrics", "main")
    assert alert is not None
    assert alert["fired"] is True


def test_notifier_silent_when_growth_within_20_percent(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    _seed(store, 110)
    alert = DegradationNotifier().evaluate(store, "acme/build_metrics", "main")
    assert alert is None
    count = store.conn.execute("SELECT COUNT(*) AS c FROM alerts").fetchone()["c"]
    assert int(count) == 0
