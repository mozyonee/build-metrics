from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_metrics.flake_detector import FlakeDetector
from build_metrics.import_manager import ImportManager
from build_metrics.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "run_success.json"


def _base(run_id: int, conclusion: str) -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["run"]["id"] = run_id
    data["jobs"][0]["id"] = run_id
    data["artifacts"][0]["id"] = run_id
    data["tests"] = [{"name": "test_login", "sha": data["run"]["head_sha"], "conclusion": conclusion}]
    return data


def test_flake_detects_pass_and_fail_on_same_sha(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    mgr = ImportManager()
    mgr.import_run(_base(1, "pass"), store)
    mgr.import_run(_base(2, "fail"), store)
    found = FlakeDetector().find(store, "acme/build_metrics")
    assert len(found) == 1
    assert found[0]["name"] == "test_login"


def test_flake_single_result_raises(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    mgr = ImportManager()
    mgr.import_run(_base(1, "pass"), store)
    with pytest.raises(LookupError):
        FlakeDetector().find(store, "acme/build_metrics")
