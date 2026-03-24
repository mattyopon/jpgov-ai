# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for the gap analysis service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, all_requirements
from app.models import AnswerItem, ComplianceStatus
from app.services.assessment import run_assessment
from app.services.gap_analysis import run_gap_analysis


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
    return [
        AnswerItem(question_id=q.question_id, selected_index=score)
        for q in ASSESSMENT_QUESTIONS
    ]


class TestGapAnalysis:
    """Gap analysis tests."""

    @pytest.mark.asyncio
    async def test_all_non_compliant(self):
        """All zero scores should result in all non-compliant."""
        assessment = run_assessment("org-001", _make_answers(0))
        result = await run_gap_analysis(assessment)
        assert result.non_compliant_count == len(all_requirements())
        assert result.compliant_count == 0

    @pytest.mark.asyncio
    async def test_all_compliant(self):
        """All max scores should result in all compliant."""
        assessment = run_assessment("org-001", _make_answers(4))
        result = await run_gap_analysis(assessment)
        assert result.compliant_count == len(all_requirements())
        assert result.non_compliant_count == 0

    @pytest.mark.asyncio
    async def test_gap_count_matches_requirements(self):
        """Gap count should match total requirements."""
        assessment = run_assessment("org-001", _make_answers(2))
        result = await run_gap_analysis(assessment)
        assert result.total_requirements == len(all_requirements())
        assert len(result.gaps) == len(all_requirements())

    @pytest.mark.asyncio
    async def test_gaps_have_actions(self):
        """Non-compliant gaps should have improvement actions."""
        assessment = run_assessment("org-001", _make_answers(0))
        result = await run_gap_analysis(assessment)
        for gap in result.gaps:
            if gap.status != ComplianceStatus.COMPLIANT:
                assert len(gap.improvement_actions) > 0

    @pytest.mark.asyncio
    async def test_has_ai_recommendations(self):
        """Result should have AI recommendations (fallback)."""
        assessment = run_assessment("org-001", _make_answers(1))
        result = await run_gap_analysis(assessment)
        assert result.ai_recommendations
        assert len(result.ai_recommendations) > 0

    @pytest.mark.asyncio
    async def test_priority_assignment(self):
        """Non-compliant gaps should have high priority."""
        assessment = run_assessment("org-001", _make_answers(0))
        result = await run_gap_analysis(assessment)
        for gap in result.gaps:
            if gap.status == ComplianceStatus.NON_COMPLIANT:
                assert gap.priority == "high"
