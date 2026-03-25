# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the timeline service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import AssessmentResult, CategoryScore
from app.services.timeline import (
    get_latest_snapshot,
    get_timeline,
    save_snapshot,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


def _make_assessment(org_id: str, score: float, level: int,
                     assessment_id: str = "") -> AssessmentResult:
    """Create a mock assessment result."""
    return AssessmentResult(
        id=assessment_id or f"assess-{score}",
        organization_id=org_id,
        overall_score=score,
        maturity_level=level,
        category_scores=[
            CategoryScore(
                category_id="C01",
                category_title="Test",
                score=score,
                maturity_level=level,
                question_count=3,
            ),
        ],
    )


class TestTimeline:
    """Timeline tracking tests."""

    def test_save_snapshot(self):
        """Should save a snapshot."""
        assessment = _make_assessment("org-001", 2.0, 3)
        snapshot = save_snapshot("org-001", assessment)
        assert snapshot.organization_id == "org-001"
        assert snapshot.overall_score == 2.0
        assert snapshot.maturity_level == 3

    def test_empty_timeline(self):
        """Empty timeline should return no entries."""
        result = get_timeline("org-001")
        assert result.organization_id == "org-001"
        assert len(result.entries) == 0
        assert result.trend == "stable"

    def test_single_entry_timeline(self):
        """Single entry should have delta of 0."""
        assessment = _make_assessment("org-001", 1.5, 2)
        save_snapshot("org-001", assessment)

        result = get_timeline("org-001")
        assert len(result.entries) == 1
        assert result.entries[0].delta_from_previous == 0.0

    def test_multiple_entries_delta(self):
        """Should calculate delta between entries."""
        save_snapshot("org-001", _make_assessment("org-001", 1.0, 1, "a1"))
        save_snapshot("org-001", _make_assessment("org-001", 1.5, 2, "a2"))
        save_snapshot("org-001", _make_assessment("org-001", 2.0, 3, "a3"))

        result = get_timeline("org-001")
        assert len(result.entries) == 3
        assert result.entries[0].delta_from_previous == 0.0
        assert result.entries[1].delta_from_previous == 0.5
        assert result.entries[2].delta_from_previous == 0.5

    def test_trend_improving(self):
        """Should detect improving trend."""
        save_snapshot("org-001", _make_assessment("org-001", 1.0, 1, "a1"))
        save_snapshot("org-001", _make_assessment("org-001", 1.5, 2, "a2"))
        save_snapshot("org-001", _make_assessment("org-001", 2.0, 3, "a3"))

        result = get_timeline("org-001")
        assert result.trend == "improving"

    def test_trend_declining(self):
        """Should detect declining trend."""
        save_snapshot("org-001", _make_assessment("org-001", 3.0, 4, "a1"))
        save_snapshot("org-001", _make_assessment("org-001", 2.5, 3, "a2"))
        save_snapshot("org-001", _make_assessment("org-001", 2.0, 3, "a3"))

        result = get_timeline("org-001")
        assert result.trend == "declining"

    def test_category_scores_in_snapshot(self):
        """Should store category scores."""
        assessment = _make_assessment("org-001", 2.0, 3)
        snapshot = save_snapshot("org-001", assessment)
        assert "C01" in snapshot.category_scores
        assert snapshot.category_scores["C01"] == 2.0

    def test_get_latest_snapshot(self):
        """Should return the most recent snapshot."""
        save_snapshot("org-001", _make_assessment("org-001", 1.0, 1, "a1"))
        save_snapshot("org-001", _make_assessment("org-001", 2.0, 3, "a2"))

        latest = get_latest_snapshot("org-001")
        assert latest is not None
        assert latest.overall_score == 2.0

    def test_get_latest_snapshot_empty(self):
        """Should return None when no snapshots exist."""
        assert get_latest_snapshot("org-001") is None

    def test_separate_org_timelines(self):
        """Different orgs should have separate timelines."""
        save_snapshot("org-001", _make_assessment("org-001", 1.0, 1, "a1"))
        save_snapshot("org-002", _make_assessment("org-002", 3.0, 4, "a2"))

        t1 = get_timeline("org-001")
        t2 = get_timeline("org-002")
        assert len(t1.entries) == 1
        assert len(t2.entries) == 1
        assert t1.entries[0].overall_score == 1.0
        assert t2.entries[0].overall_score == 3.0
