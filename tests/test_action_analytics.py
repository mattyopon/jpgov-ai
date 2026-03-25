# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the action analytics service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import ActionEffectRecord
from app.services.action_analytics import (
    K_ANONYMITY_THRESHOLD,
    get_action_rankings,
    get_action_type_stats,
    get_industry_comparison,
    record_action_effect,
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


def _make_effect(
    org_id: str = "org-001",
    task_id: str = "task-001",
    action_type: str = "policy_creation",
    requirement_id: str = "C01-R01",
    score_before: float = 1.0,
    score_after: float = 2.0,
    effort_hours: float = 10.0,
) -> ActionEffectRecord:
    """Create a mock action effect record."""
    return ActionEffectRecord(
        organization_id=org_id,
        task_id=task_id,
        action_type=action_type,
        requirement_id=requirement_id,
        score_before=score_before,
        score_after=score_after,
        effort_hours=effort_hours,
    )


class TestActionAnalytics:
    """Action analytics tests."""

    def test_record_action_effect(self):
        """Should record an action effect and return ROI."""
        data = _make_effect()
        roi = record_action_effect(data)

        assert roi.task_id == "task-001"
        assert roi.score_delta == 1.0
        assert roi.effort_hours == 10.0
        assert roi.roi == 0.1  # 1.0 / 10.0

    def test_record_with_zero_effort(self):
        """Should handle zero effort hours."""
        data = _make_effect(effort_hours=0.0)
        roi = record_action_effect(data)
        assert roi.roi == 0.0

    def test_record_negative_delta(self):
        """Should handle negative score changes."""
        data = _make_effect(score_before=3.0, score_after=2.0)
        roi = record_action_effect(data)
        assert roi.score_delta == -1.0

    def test_rankings_empty(self):
        """Should return empty rankings for org with no data."""
        result = get_action_rankings("org-empty")
        assert len(result.rankings) == 0
        assert result.avg_score_improvement == 0.0
        assert result.best_roi_action_type == ""

    def test_rankings_single_action(self):
        """Should rank a single action."""
        record_action_effect(_make_effect())
        result = get_action_rankings("org-001")
        assert len(result.rankings) == 1
        assert result.rankings[0].roi == 0.1

    def test_rankings_multiple_actions(self):
        """Should sort actions by ROI descending."""
        record_action_effect(_make_effect(
            task_id="t1", action_type="training",
            score_before=1.0, score_after=3.0, effort_hours=5.0
        ))  # ROI = 0.4
        record_action_effect(_make_effect(
            task_id="t2", action_type="policy",
            score_before=1.0, score_after=1.5, effort_hours=10.0
        ))  # ROI = 0.05
        record_action_effect(_make_effect(
            task_id="t3", action_type="audit",
            score_before=2.0, score_after=3.5, effort_hours=8.0
        ))  # ROI = 0.1875

        result = get_action_rankings("org-001")
        assert len(result.rankings) == 3
        # Should be sorted by ROI descending
        assert result.rankings[0].roi >= result.rankings[1].roi
        assert result.rankings[1].roi >= result.rankings[2].roi

    def test_rankings_best_roi_type(self):
        """Should identify the best ROI action type."""
        record_action_effect(_make_effect(
            task_id="t1", action_type="training",
            score_before=1.0, score_after=3.0, effort_hours=5.0
        ))
        record_action_effect(_make_effect(
            task_id="t2", action_type="training",
            score_before=1.0, score_after=2.5, effort_hours=5.0
        ))
        record_action_effect(_make_effect(
            task_id="t3", action_type="policy",
            score_before=1.0, score_after=1.5, effort_hours=20.0
        ))

        result = get_action_rankings("org-001")
        assert result.best_roi_action_type == "training"

    def test_rankings_avg_improvement(self):
        """Should calculate average score improvement."""
        record_action_effect(_make_effect(
            task_id="t1", score_before=1.0, score_after=2.0
        ))
        record_action_effect(_make_effect(
            task_id="t2", score_before=2.0, score_after=3.0
        ))
        result = get_action_rankings("org-001")
        assert result.avg_score_improvement == 1.0

    def test_industry_comparison_insufficient_data(self):
        """Should return empty when insufficient data for k-anonymity."""
        record_action_effect(_make_effect(org_id="org-other"))
        result = get_industry_comparison("org-001", "IT")
        assert result == []

    def test_industry_comparison_sufficient_data(self):
        """Should return comparison when sufficient data."""
        for i in range(K_ANONYMITY_THRESHOLD + 1):
            record_action_effect(_make_effect(
                org_id=f"org-other-{i}",
                task_id=f"task-{i}",
                action_type="training",
                score_before=1.0, score_after=2.0, effort_hours=5.0,
            ))
        result = get_industry_comparison("org-001", "IT")
        assert len(result) > 0
        assert result[0]["action_type"] == "training"

    def test_industry_comparison_excludes_own_data(self):
        """Should exclude own organization's data from comparison."""
        # Add own data
        record_action_effect(_make_effect(
            org_id="org-001", task_id="own-task",
            action_type="training", score_before=1.0, score_after=4.0
        ))
        # Add others' data
        for i in range(K_ANONYMITY_THRESHOLD + 1):
            record_action_effect(_make_effect(
                org_id=f"org-other-{i}",
                task_id=f"task-{i}",
                action_type="training",
                score_before=1.0, score_after=2.0, effort_hours=5.0,
            ))

        result = get_industry_comparison("org-001", "IT")
        assert len(result) > 0
        # Average should reflect others' data, not own (avg delta ~1.0)
        assert result[0]["avg_score_improvement"] == 1.0

    def test_action_type_stats_empty(self):
        """Should return empty stats for org with no data."""
        result = get_action_type_stats("org-empty")
        assert result == {}

    def test_action_type_stats(self):
        """Should calculate stats per action type."""
        record_action_effect(_make_effect(
            task_id="t1", action_type="training",
            score_before=1.0, score_after=2.0, effort_hours=5.0
        ))
        record_action_effect(_make_effect(
            task_id="t2", action_type="training",
            score_before=1.5, score_after=3.0, effort_hours=8.0
        ))
        record_action_effect(_make_effect(
            task_id="t3", action_type="policy",
            score_before=2.0, score_after=2.5, effort_hours=10.0
        ))

        stats = get_action_type_stats("org-001")
        assert "training" in stats
        assert "policy" in stats
        assert stats["training"]["count"] == 2
        assert stats["policy"]["count"] == 1

    def test_action_type_stats_roi(self):
        """Should calculate ROI per action type."""
        record_action_effect(_make_effect(
            task_id="t1", action_type="training",
            score_before=1.0, score_after=3.0, effort_hours=10.0
        ))
        stats = get_action_type_stats("org-001")
        assert stats["training"]["roi"] == 0.2  # 2.0/10.0

    def test_organizations_isolated(self):
        """Rankings for one org should not include another's data."""
        record_action_effect(_make_effect(org_id="org-A", task_id="t1"))
        record_action_effect(_make_effect(org_id="org-B", task_id="t2"))

        a_rankings = get_action_rankings("org-A")
        b_rankings = get_action_rankings("org-B")
        assert len(a_rankings.rankings) == 1
        assert len(b_rankings.rankings) == 1
