# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for multi-framework gap analysis."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS
from app.models import AnswerItem
from app.services.assessment import run_assessment
from app.services.gap_analysis import (
    run_gap_analysis,
    run_multi_framework_gap_analysis,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
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


class TestMultiFrameworkGap:
    """Multi-framework gap analysis tests."""

    @pytest.mark.asyncio
    async def test_basic_multi_framework(self):
        """All-zero should produce gaps with multiple framework violations."""
        assessment = run_assessment("org-001", _make_answers(0))
        gap_result = await run_gap_analysis(assessment)
        results = run_multi_framework_gap_analysis(gap_result)
        assert len(results) > 0
        # Each gap should have at least METI violation
        for r in results:
            assert len(r["violations"]) >= 1
            assert r["violations"][0]["framework"] in ("meti", "eu_ai_act", "iso42001", "nist", "ai_promotion_act")

    @pytest.mark.asyncio
    async def test_no_gaps_when_compliant(self):
        """All-max should produce no gaps."""
        assessment = run_assessment("org-001", _make_answers(4))
        gap_result = await run_gap_analysis(assessment)
        results = run_multi_framework_gap_analysis(gap_result)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_with_industry(self):
        """Multi-framework with industry should include industry violations."""
        assessment = run_assessment("org-001", _make_answers(0))
        gap_result = await run_gap_analysis(assessment)
        results = run_multi_framework_gap_analysis(
            gap_result, industry="financial", include_industry=True
        )
        assert len(results) > 0
        # At least some gaps should have industry violations
        has_industry = any(
            any(v["framework"] == "industry" for v in r["violations"])
            for r in results
        )
        assert has_industry

    @pytest.mark.asyncio
    async def test_exclude_nist(self):
        """Excluding NIST should not include NIST violations."""
        assessment = run_assessment("org-001", _make_answers(0))
        gap_result = await run_gap_analysis(assessment)
        results = run_multi_framework_gap_analysis(
            gap_result, include_nist=False
        )
        for r in results:
            assert all(v["framework"] != "nist" for v in r["violations"])

    @pytest.mark.asyncio
    async def test_exclude_eu(self):
        """Excluding EU should not include EU violations."""
        assessment = run_assessment("org-001", _make_answers(0))
        gap_result = await run_gap_analysis(assessment)
        results = run_multi_framework_gap_analysis(
            gap_result, include_eu=False
        )
        for r in results:
            assert all(v["framework"] != "eu_ai_act" for v in r["violations"])

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Results should be sorted by highest priority framework."""
        assessment = run_assessment("org-001", _make_answers(0))
        gap_result = await run_gap_analysis(assessment)
        results = run_multi_framework_gap_analysis(gap_result)
        if len(results) >= 2:
            # Each result's violations should be sorted by priority
            for r in results:
                priorities = [v["priority"] for v in r["violations"]]
                assert priorities == sorted(priorities)

    @pytest.mark.asyncio
    async def test_has_highest_priority_framework(self):
        """Each result should have highest_priority_framework field."""
        assessment = run_assessment("org-001", _make_answers(0))
        gap_result = await run_gap_analysis(assessment)
        results = run_multi_framework_gap_analysis(gap_result)
        for r in results:
            assert "highest_priority_framework" in r
            assert len(r["highest_priority_framework"]) > 0
