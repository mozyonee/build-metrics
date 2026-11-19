from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_metrics.comparison import ComparisonManager
from build_metrics.import_manager import ImportManager
from build_metrics.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "run_success.json"


def _payload(run_id: int, branch: str) -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["run"]["id"] = run_id
    data["run"]["head_branch"] = branch
    data["jobs"][0]["id"] = run_id
    data["artifacts"][0]["id"] = run_id
    return data


def test_compare_returns_five_metrics(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    mgr = ImportManager()
    mgr.import_run(_payload(1, "main"), store)
    mgr.import_run(_payload(2, "release"), store)
    result = ComparisonManager().compare(store, "acme/build_metrics", "main", "release")
    assert set(result) == {
        "median_duration",
        "success_rate",
        "flake_count",
        "cache_hit_rate",
        "artifact_size",
    }


def test_compare_empty_side_raises(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    mgr = ImportManager()
    mgr.import_run(_payload(1, "main"), store)
    with pytest.raises(LookupError):
        ComparisonManager().compare(store, "acme/build_metrics", "main", "release")
