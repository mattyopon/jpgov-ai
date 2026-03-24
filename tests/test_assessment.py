# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the assessment service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS
from app.models import AnswerItem
from app.services.assessment import run_assessment


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


def _make_answers(score: int) -> list[AnswerItem]:
    """Create answers with a uniform selected_index."""
    return [
        AnswerItem(question_id=q.question_id, selected_index=score)
        for q in ASSESSMENT_QUESTIONS
    ]


class TestAssessment:
    """Self-Assessment tests."""

    def test_all_zeros(self):
        """All lowest scores should give maturity level 1."""
        result = run_assessment("org-001", _make_answers(0))
        assert result.overall_score == 0.0
        assert result.maturity_level == 1
        assert len(result.category_scores) == 10

    def test_all_max(self):
        """All highest scores should give maturity level 5."""
        result = run_assessment("org-001", _make_answers(4))
        assert result.overall_score == 4.0
        assert result.maturity_level == 5

    def test_mid_scores(self):
        """Mid-range scores should give maturity level 3."""
        result = run_assessment("org-001", _make_answers(2))
        assert result.overall_score == 2.0
        assert result.maturity_level == 3

    def test_category_count(self):
        """Should have scores for all 10 categories."""
        result = run_assessment("org-001", _make_answers(2))
        cat_ids = {cs.category_id for cs in result.category_scores}
        assert len(cat_ids) == 10

    def test_empty_answers(self):
        """Empty answers should give all zeros."""
        result = run_assessment("org-001", [])
        assert result.overall_score == 0.0
        assert result.maturity_level == 1

    def test_partial_answers(self):
        """Partial answers should still work."""
        answers = [
            AnswerItem(question_id="Q01", selected_index=4),
            AnswerItem(question_id="Q02", selected_index=4),
        ]
        result = run_assessment("org-001", answers)
        # C01 should have high score, others should be 0
        c01 = next(cs for cs in result.category_scores if cs.category_id == "C01")
        assert c01.score == 4.0

    def test_result_has_id(self):
        """Result should have a unique ID."""
        result = run_assessment("org-001", _make_answers(2))
        assert result.id
        assert len(result.id) > 0

    def test_result_has_timestamp(self):
        """Result should have a timestamp."""
        result = run_assessment("org-001", _make_answers(2))
        assert result.timestamp
