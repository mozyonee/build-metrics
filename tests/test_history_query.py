from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_metrics.history_query import HistoryQuery
from build_metrics.import_manager import ImportManager
from build_metrics.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "run_success.json"


def _payload(run_id: int, branch: str = "main") -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["run"]["id"] = run_id
    data["run"]["head_branch"] = branch
    data["jobs"][0]["id"] = run_id
    data["artifacts"][0]["id"] = run_id
    return data


def test_history_returns_two_runs(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    mgr = ImportManager()
    mgr.import_run(_payload(1), store)
    mgr.import_run(_payload(2), store)
    rows = HistoryQuery().list_runs(store, "acme/build_metrics", "main")
    assert len(rows) == 2
    assert {"duration", "queue", "conclusion", "cache", "artifact_size"} <= set(rows[0])


def test_history_unknown_repo_raises(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    with pytest.raises(LookupError):
        HistoryQuery().list_runs(store, "missing/repo", "main")
