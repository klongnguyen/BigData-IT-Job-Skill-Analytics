"""Serving integrity and dashboard regressions; no Spark or local data required."""

import json
from pathlib import Path

import pandas as pd
import pytest

from dashboard.data import (
    GoldError, directory_evidence, load_gold, select_scope, sha256,
    summarize_skills, trend_calendar,
)


@pytest.fixture
def gold_fixture(tmp_path):
    run_id = "test-gold-run"
    run_dir = tmp_path / "data/gold/global/runs" / run_id
    rows = []
    for source, month, n, count, origin in [
        ("kaggle_historical_archive", "2023-01", 10, 9, "source_tags"),
        ("kaggle_historical_archive", "2023-02", 90, 9, "source_tags"),
        ("kaggle_historical_archive", "2023-04", 20, 0, "source_tags"),
        ("arbeitnow", "2026-10", 20, 10, "extracted_from_jd"),
    ]:
        rows.append(dict(source=source, month=month, occupation="Data Engineer",
                         taxonomy_version="v0.1", skills_origin=origin, skill="python",
                         job_count=n, source_month_jobs=n, occupation_job_count=n,
                         origin_job_count=n, skill_evidence_jobs=count, skill_job_count=count,
                         demand_rate=count/n, known_country_jobs=0, known_experience_jobs=0,
                         observed_delta_pp=-80.0 if month == "2023-02" else None,
                         consecutive_observed_month=month == "2023-02"))
    frame = pd.DataFrame(rows)
    tables = {
        "market_stats": frame[["source", "month", "job_count", "skill_evidence_jobs", "known_country_jobs", "known_experience_jobs"]],
        "occupation_stats": frame[["source", "month", "occupation", "job_count", "source_month_jobs"]],
        "skill_evidence_stats": frame.drop(columns=["skill", "skill_job_count", "demand_rate", "observed_delta_pp", "consecutive_observed_month"]),
        "skill_stats": frame.drop(columns=["observed_delta_pp", "consecutive_observed_month"]),
        "skill_trends": frame,
    }
    outputs = {}
    for name, table in tables.items():
        directory = run_dir / name
        directory.mkdir(parents=True)
        table.to_parquet(directory / "part.parquet", index=False)
        outputs[name] = {"rows": len(table), "path": "X:/old-machine/ignored", **directory_evidence(directory)}
    manifest = {
        "schema_version": 1, "status": "completed", "run_id": run_id,
        "analysis_type": "observed_descriptive_only", "taxonomy_version": "v0.1",
        "completed_at": "2026-10-12T13:00:00Z", "input": {"silver_rows": 140},
        "outputs": outputs,
        "predictive_gate": {"decision": "NO_GO", "predictive_claims": "Insufficient evidence",
                            "missing_months_between_first_and_last": ["2023-03"],
                            "checks": [{"id": "continuity", "status": "FAIL", "detail": "Missing observations"}]},
    }
    audit_path = tmp_path / "docs/data/phase03_analytics_audit.json"
    audit_path.parent.mkdir(parents=True)

    def publish():
        (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        audit = {**manifest, "manifest_sha256": sha256(run_dir / "manifest.json")}
        audit_path.write_text(json.dumps(audit), encoding="utf-8")

    publish()
    return tmp_path, run_dir, manifest, publish


def test_pinned_run_is_portable_and_gate_is_preserved(gold_fixture):
    root, _, _, _ = gold_fixture
    run = load_gold(root)
    assert len(run.tables) == 5
    assert run.tables["market_stats"].job_count.sum() == 140
    assert run.manifest["predictive_gate"]["decision"] == "NO_GO"
    assert not any("prediction" in name for name in run.tables)


@pytest.mark.parametrize("failure", ["manifest", "parquet", "missing", "extra", "rows", "schema", "key", "gate"])
def test_integrity_failure_is_closed(gold_fixture, failure):
    root, directory, manifest, publish = gold_fixture
    if failure == "manifest":
        with (directory / "manifest.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
    elif failure == "parquet":
        with (directory / "skill_stats/part.parquet").open("ab") as stream:
            stream.write(b"tampered")
    elif failure == "missing":
        (directory / "skill_stats/part.parquet").unlink()
    elif failure == "extra":
        (directory / "skill_stats/unlisted.txt").write_text("extra")
    elif failure == "rows":
        manifest["outputs"]["skill_stats"]["rows"] += 1
        publish()
    elif failure in ("schema", "key"):
        path = directory / "skill_stats/part.parquet"
        frame = pd.read_parquet(path)
        if failure == "schema":
            frame = frame.drop(columns=["skill_job_count"])
        else:
            frame = pd.concat([frame.iloc[:1], frame.iloc[:1], frame.iloc[2:]], ignore_index=True)
        frame.to_parquet(path, index=False)
        manifest["outputs"]["skill_stats"].update(directory_evidence(path.parent))
        publish()
    else:
        path = root / "docs/data/phase03_analytics_audit.json"
        audit = json.loads(path.read_text())
        audit["predictive_gate"]["decision"] = "GO"
        path.write_text(json.dumps(audit), encoding="utf-8")
    with pytest.raises(GoldError):
        load_gold(root)


def test_weighted_denominator_includes_jobs_without_skill(gold_fixture):
    run = load_gold(gold_fixture[0])
    skills = select_scope(run.tables["skill_stats"], "kaggle_historical_archive", ["2023-01", "2023-02", "2023-04"])
    occ = select_scope(run.tables["occupation_stats"], "kaggle_historical_archive", ["2023-01", "2023-02", "2023-04"])
    result = summarize_skills(skills, occ).iloc[0]
    assert result.skill_job_count == 18
    assert result.denominator_jobs == 120
    assert result.demand_rate == pytest.approx(.15)
    assert result.demand_rate != pytest.approx(skills.demand_rate.mean())
    # Duplicate evidence mode is not silently merged into the tags numerator.
    other = skills.assign(skills_origin="extracted_from_jd", skill_job_count=0)
    result = summarize_skills(pd.concat([skills, other]), occ)
    assert len(result) == 2
    assert sorted(result.demand_rate) == [0, .15]


def test_source_filter_empty_and_missing_zero(gold_fixture):
    run = load_gold(gold_fixture[0])
    trends = run.tables["skill_trends"]
    with pytest.raises(ValueError, match="one source"):
        select_scope(trends, ["arbeitnow", "kaggle_historical_archive"], ["2023-01"])
    assert select_scope(trends, "arbeitnow", ["2023-01"]).empty
    assert select_scope(trends, "arbeitnow", []).empty
    assert select_scope(trends, "arbeitnow", ["2026-10"], []).empty
    with pytest.raises(ValueError, match="one source"):
        trend_calendar(trends, "2023-01", "2026-10")
    scoped = select_scope(trends, "kaggle_historical_archive", ["2023-01", "2023-02", "2023-04"])
    timeline = trend_calendar(scoped, "2023-01", "2023-04").set_index("month")
    assert pd.isna(timeline.loc["2023-03", "demand_rate"])
    assert timeline.loc["2023-04", "demand_rate"] == 0
    assert pd.isna(timeline.loc["2023-04", "observed_delta_pp"])
    assert timeline.loc["2023-02", "observed_delta_pp"] == -80


def test_streamlit_pages_filters_empty_and_no_go(gold_fixture, monkeypatch):
    from streamlit.testing.v1 import AppTest
    import dashboard.data

    run = load_gold(gold_fixture[0])
    monkeypatch.setattr(dashboard.data, "load_gold", lambda **kwargs: run)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard/app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "120"
    for page in ["Nhóm nghề", "Kỹ năng & xu hướng", "So sánh nghề", "Dự báo & bằng chứng"]:
        app.radio(key="page").set_value(page).run()
        assert not app.exception, page
    assert any("NO_GO" in w.value and "Insufficient evidence" in w.value for w in app.warning)
    app.radio(key="page").set_value("Dữ liệu 2026").run()
    assert not app.exception
    assert any(metric.value == "19.706" for metric in app.metric)
    app.radio(key="page").set_value("Kỹ năng & xu hướng").run()
    assert app.metric[0].value == "15.00%"
    app.selectbox(key="source").set_value("arbeitnow").run()
    assert not app.exception
    assert app.metric[0].value == "50.00%"
    app.multiselect(key="months_arbeitnow").set_value([]).run()
    assert not app.exception
    assert any("Không có quan sát" in i.value for i in app.info)


def test_streamlit_missing_artifact_message(monkeypatch):
    from streamlit.testing.v1 import AppTest
    import dashboard.data

    def missing(**kwargs):
        raise GoldError("Missing pinned run")

    monkeypatch.setattr(dashboard.data, "load_gold", missing)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard/app.py"), default_timeout=30).run()
    assert not app.exception
    assert "Không thể mở dữ liệu Gold" in app.error[0].value
