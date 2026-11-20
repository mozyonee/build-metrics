from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_metrics.import_manager import ImportManager
from build_metrics.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "run_success.json"


def test_import_completed_run_saves_duration(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    run_id = ImportManager().import_run(payload, store)
    assert run_id == 101
    row = store.conn.execute("SELECT duration_seconds, queue_seconds FROM workflow_runs WHERE id = 101").fetchone()
    assert int(row["duration_seconds"]) == 300
    assert int(row["queue_seconds"]) == 30


def test_import_queued_run_leaves_database_unchanged(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ImportManager().import_run(payload, store)
    before = store.count_runs()
    bad = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bad["run"]["id"] = 202
    bad["run"]["status"] = "queued"
    with pytest.raises(ValueError):
        ImportManager().import_run(bad, store)
    assert store.count_runs() == before
