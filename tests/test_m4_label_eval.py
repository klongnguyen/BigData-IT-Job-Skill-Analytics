"""Independent-label scoring must keep coverage separate from precision."""

import csv

import pytest

from src.skills.label_eval import FIELDS, evaluate_labels


def test_label_metrics_distinguish_occupation_and_skill_errors(tmp_path):
    path = tmp_path / "labels.csv"
    rows = [
        {"source": "example", "source_record_id": "1", "title": "Data Engineer",
         "description": "SQL and Python", "predicted_occupation": "Data Engineer",
         "predicted_skills": "python;sql", "is_it": "1", "gold_occupation": "Data Engineer",
         "gold_skills": "python", "annotator": "Reviewer A"},
        {"source": "example", "source_record_id": "2", "title": "IT Specialist",
         "description": "SQL", "predicted_occupation": "Other IT",
         "predicted_skills": "", "is_it": "1", "gold_occupation": "Data Engineer",
         "gold_skills": "sql", "annotator": "Reviewer A"},
        {"source": "example", "source_record_id": "3", "title": "Sales",
         "description": "", "predicted_occupation": "Other IT",
         "predicted_skills": "", "is_it": "0", "gold_occupation": "Out of scope",
         "gold_skills": "", "annotator": "Reviewer A"},
        {"source": "example", "source_record_id": "4", "title": "Unlabeled",
         "description": "", "predicted_occupation": "Other IT", "annotator": ""},
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    result = evaluate_labels(path)
    source = result["sources"]["example"]
    assert result["sample_rows"] == 4 and result["labeled_rows"] == 3
    assert source["in_scope_it_rows"] == 2 and source["out_of_scope_rows"] == 1
    assert source["title_coverage"] == .5
    assert source["occupation_accuracy"] == .5
    assert source["occupation_macro_f1"] == pytest.approx(1 / 3)
    assert source["skill_micro"]["precision"] == .5
    assert source["skill_micro"]["recall"] == .5


def test_invalid_manual_label_fails_closed(tmp_path):
    path = tmp_path / "labels.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({"source": "example", "source_record_id": "1", "is_it": "maybe",
                         "annotator": "Reviewer A"})
    with pytest.raises(ValueError, match="is_it"):
        evaluate_labels(path)
