"""Gold document IDs and digests are stable across row ordering."""

import pandas as pd
import pytest

pymongo = pytest.importorskip("pymongo")

from src.serving.mongo_gold import table_documents


def test_canonical_documents_are_order_independent():
    frame = pd.DataFrame([
        {"month": "2026-10", "source": "a", "job_count": 2, "rate": None},
        {"month": "2026-09", "source": "a", "job_count": 1, "rate": .5},
    ])
    first, first_hash = table_documents(frame, ["month", "source"])
    second, second_hash = table_documents(frame.iloc[::-1], ["month", "source"])
    assert first == second and first_hash == second_hash
    assert first[1]["row"]["rate"] is None
