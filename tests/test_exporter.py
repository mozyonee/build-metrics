from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_metrics.exporter import ReportExporter
from build_metrics.import_manager import ImportManager
from build_metrics.store import Store

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "run_success.json"


def test_export_writes_duration(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ImportManager().import_run(payload, store)
    dest = tmp_path / "report.md"
    path = ReportExporter().export(
        store,
        "acme/build_metrics",
        "2026-11-01T00:00:00Z",
        "2026-11-02T00:00:00Z",
        dest,
    )
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "тривалість" in text


def test_export_empty_period_raises(tmp_path: Path) -> None:
    store = Store(tmp_path / "db.sqlite")
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ImportManager().import_run(payload, store)
    dest = tmp_path / "report.md"
    with pytest.raises(LookupError):
        ReportExporter().export(
            store,
            "acme/build_metrics",
            "2025-01-01T00:00:00Z",
            "2025-01-02T00:00:00Z",
            dest,
        )
    assert not dest.exists()
