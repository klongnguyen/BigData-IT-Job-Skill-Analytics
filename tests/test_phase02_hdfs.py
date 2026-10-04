"""HDFS smoke is opt-in and never treats local filesystem as HDFS evidence."""

import json
import os

import pytest

from src.common.run_manifest import file_entry
from src.processing.hdfs_smoke import run_hdfs_smoke


def test_rejects_local_uri_before_starting_spark(tmp_path):
    with pytest.raises(ValueError, match="genuine hdfs"):
        run_hdfs_smoke(tmp_path, "file:///tmp/not-hdfs")


@pytest.mark.hdfs
def test_live_hdfs_round_trip(tmp_path):
    uri = os.environ.get("PHASE02_HDFS_URI")
    if not uri:
        pytest.skip("PHASE02_HDFS_URI is not configured; no HDFS acceptance evidence")
    run_dir = tmp_path / "runs" / "hdfs_fixture"
    records = run_dir / "records"
    records.mkdir(parents=True)
    path = records / "batch_001.json"
    path.write_text(json.dumps([{"source": "fixture", "title": "Data Analyst"}]), encoding="utf-8")
    manifest = {"schema_version": 1, "run_id": "hdfs_fixture", "kind": "historical",
                "status": "complete", "total_rows": 1, "files": [file_entry(run_dir, path, 1)]}
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    evidence_path = run_hdfs_smoke(run_dir, uri, evidence_dir=tmp_path / "evidence")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["status"] == "completed"
    assert evidence["input_rows"] == evidence["output_rows"] == 1
    assert evidence["hdfs_uri"].startswith("hdfs://")
