# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the prediction service."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.db.database import (
    ActionEffectRow,
    AssessmentSnapshotRow,
    RegulatoryUpdateRow,
    get_db,
    reset_db,
)
from app.services.prediction import (
    LEVEL_3_SCORE,
    predict_score,
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


def _add_snapshot(
    org_id: str,
    score: float,
    days_ago: int = 0,
    category_scores: dict | None = None,
):
    """Add a snapshot to the DB."""
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    cat_scores = category_scores or {"C01": score, "C02": score * 0.8}

    db = get_db()
    with db.get_session() as session:
        row = AssessmentSnapshotRow(
            organization_id=org_id,
            assessment_id=f"assess-{days_ago}",
            overall_score=score,
            maturity_level=int(score) + 1,
            category_scores_json=json.dumps(cat_scores),
            created_at=ts,
        )
        session.add(row)
        session.commit()


def _add_action_effect(
    org_id: str,
    score_delta: float = 0.5,
):
    """Add an action effect record."""
    db = get_db()
    with db.get_session() as session:
        row = ActionEffectRow(
            organization_id=org_id,
            task_id=f"task-{score_delta}",
            action_type="training",
            score_before=1.0,
            score_after=1.0 + score_delta,
            effort_hours=10.0,
        )
        session.add(row)
        session.commit()


def _add_regulatory_update(severity: str = "high"):
    """Add a regulatory update."""
    db = get_db()
    with db.get_session() as session:
        row = RegulatoryUpdateRow(
            regulation_name="METI",
            title="Test update",
            severity=severity,
            affected_requirements_json="[]",
        )
        session.add(row)
        session.commit()


class TestPrediction:
    """Prediction service tests."""

    def test_predict_no_data(self):
        """Should return zero prediction with no data."""
        result = predict_score("org-empty")
        assert result.current_score == 0.0
        assert result.predicted_score == 0.0
        assert result.trend == "stable"
        assert result.confidence == "low"

    def test_predict_single_snapshot(self):
        """Single snapshot should return stable prediction."""
        _add_snapshot("org-001", 2.0, days_ago=0)
        result = predict_score("org-001")
        assert result.current_score == 2.0
        assert result.trend == "stable"
        assert result.confidence == "low"

    def test_predict_improving_trend(self):
        """Should detect improving trend."""
        _add_snapshot("org-001", 1.0, days_ago=90)
        _add_snapshot("org-001", 1.5, days_ago=60)
        _add_snapshot("org-001", 2.0, days_ago=30)
        _add_snapshot("org-001", 2.5, days_ago=0)

        result = predict_score("org-001")
        assert result.current_score == 2.5
        assert result.trend == "improving"
        assert result.monthly_rate > 0

    def test_predict_declining_trend(self):
        """Should detect declining trend."""
        _add_snapshot("org-001", 3.0, days_ago=90)
        _add_snapshot("org-001", 2.5, days_ago=60)
        _add_snapshot("org-001", 2.0, days_ago=30)
        _add_snapshot("org-001", 1.5, days_ago=0)

        result = predict_score("org-001")
        assert result.trend == "declining"
        assert result.monthly_rate < 0

    def test_predict_stable_trend(self):
        """Should detect stable trend."""
        _add_snapshot("org-001", 2.0, days_ago=90)
        _add_snapshot("org-001", 2.01, days_ago=60)
        _add_snapshot("org-001", 2.0, days_ago=30)
        _add_snapshot("org-001", 2.01, days_ago=0)

        result = predict_score("org-001")
        assert result.trend == "stable"

    def test_predict_days_to_level3(self):
        """Should estimate days to Level 3."""
        _add_snapshot("org-001", 1.0, days_ago=60)
        _add_snapshot("org-001", 1.5, days_ago=30)
        _add_snapshot("org-001", 2.0, days_ago=0)

        result = predict_score("org-001")
        assert result.days_to_level3 > 0
        assert result.current_score < LEVEL_3_SCORE

    def test_predict_already_level3(self):
        """Should return 0 days when already at Level 3."""
        _add_snapshot("org-001", 2.5, days_ago=30)
        _add_snapshot("org-001", 3.0, days_ago=0)

        result = predict_score("org-001")
        assert result.days_to_level3 == 0

    def test_predict_with_target_date(self):
        """Should predict score at specified target date."""
        _add_snapshot("org-001", 1.0, days_ago=60)
        _add_snapshot("org-001", 2.0, days_ago=0)

        future = (datetime.now(timezone.utc) + timedelta(days=180)).strftime("%Y-%m-%d")
        result = predict_score("org-001", target_date=future)
        assert result.prediction_date == future
        # Should predict higher score in 180 days for improving trend
        assert result.predicted_score > 2.0

    def test_predict_with_target_score(self):
        """Should calculate days to custom target score."""
        _add_snapshot("org-001", 1.0, days_ago=60)
        _add_snapshot("org-001", 2.0, days_ago=0)

        result = predict_score("org-001", target_score=3.0)
        assert result.target_score == 3.0
        assert result.days_to_target > 0

    def test_predict_score_capped_at_4(self):
        """Predicted score should not exceed 4.0."""
        _add_snapshot("org-001", 3.0, days_ago=30)
        _add_snapshot("org-001", 3.8, days_ago=0)

        future = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
        result = predict_score("org-001", target_date=future)
        assert result.predicted_score <= 4.0

    def test_predict_score_not_negative(self):
        """Predicted score should not go below 0.0."""
        _add_snapshot("org-001", 1.0, days_ago=30)
        _add_snapshot("org-001", 0.5, days_ago=0)

        future = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
        result = predict_score("org-001", target_date=future)
        assert result.predicted_score >= 0.0

    def test_predict_required_actions(self):
        """Should estimate required action count."""
        _add_snapshot("org-001", 1.0, days_ago=30)
        _add_snapshot("org-001", 1.5, days_ago=0)

        # Add action effect data to establish avg impact
        _add_action_effect("org-001", score_delta=0.3)
        _add_action_effect("org-001", score_delta=0.5)

        result = predict_score("org-001")
        assert result.required_actions > 0

    def test_predict_required_actions_default_estimate(self):
        """Should use default estimate when no action data."""
        _add_snapshot("org-001", 1.0, days_ago=30)
        _add_snapshot("org-001", 1.5, days_ago=0)

        result = predict_score("org-001")
        # Should still estimate using default
        assert result.required_actions > 0

    def test_predict_regulatory_adjustment(self):
        """Should include regulatory impact adjustment."""
        _add_snapshot("org-001", 2.0, days_ago=30)
        _add_snapshot("org-001", 2.2, days_ago=0)
        _add_regulatory_update(severity="high")

        result = predict_score("org-001")
        assert result.regulatory_impact_adjustment < 0

    def test_predict_no_regulatory_adjustment(self):
        """Should have zero adjustment when no high-severity updates."""
        _add_snapshot("org-001", 2.0, days_ago=30)
        _add_snapshot("org-001", 2.2, days_ago=0)

        result = predict_score("org-001")
        assert result.regulatory_impact_adjustment == 0.0

    def test_predict_category_predictions(self):
        """Should predict category-level scores."""
        _add_snapshot("org-001", 1.0, days_ago=60, category_scores={"C01": 1.0, "C02": 0.5})
        _add_snapshot("org-001", 2.0, days_ago=0, category_scores={"C01": 2.0, "C02": 1.5})

        result = predict_score("org-001")
        assert "C01" in result.category_predictions
        assert "C02" in result.category_predictions
        # C01 should be predicted to improve
        assert result.category_predictions["C01"] >= 2.0

    def test_predict_confidence_high(self):
        """Should have high confidence with many data points and good fit."""
        for i in range(6):
            score = 1.0 + i * 0.3
            _add_snapshot("org-001", score, days_ago=(5 - i) * 30)

        result = predict_score("org-001")
        # With 6 data points in a clear linear trend, should be medium or high
        assert result.confidence in ("medium", "high")

    def test_organizations_isolated(self):
        """Predictions for one org should not use another's data."""
        _add_snapshot("org-A", 1.0, days_ago=30)
        _add_snapshot("org-A", 2.0, days_ago=0)
        _add_snapshot("org-B", 3.0, days_ago=30)
        _add_snapshot("org-B", 3.5, days_ago=0)

        a_result = predict_score("org-A")
        b_result = predict_score("org-B")
        assert a_result.current_score == 2.0
        assert b_result.current_score == 3.5
