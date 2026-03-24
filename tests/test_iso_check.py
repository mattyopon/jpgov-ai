# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the ISO 42001 check service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.iso42001 import (
    ISO_CLAUSES,
    all_iso_requirements,
    get_iso_to_meti_mapping,
    get_meti_to_iso_mapping,
)
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS
from app.models import AnswerItem
from app.services.assessment import run_assessment
from app.services.gap_analysis import run_gap_analysis
from app.services.iso_check import run_iso_check


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


class TestISOGuidelines:
    """ISO 42001 guideline data tests."""

    def test_clauses_exist(self):
        assert len(ISO_CLAUSES) >= 7

    def test_all_requirements_not_empty(self):
        reqs = all_iso_requirements()
        assert len(reqs) > 0

    def test_all_have_meti_mapping(self):
        for req in all_iso_requirements():
            # Most requirements should have METI mapping
            assert isinstance(req.meti_mapping, list)

    def test_meti_to_iso_mapping(self):
        mapping = get_meti_to_iso_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_iso_to_meti_mapping(self):
        mapping = get_iso_to_meti_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) > 0


class TestISOCheck:
    """ISO 42001 check service tests."""

    @pytest.mark.asyncio
    async def test_check_all_zeros(self):
        assessment = run_assessment("org-001", _make_answers(0))
        gap = await run_gap_analysis(assessment)
        result = run_iso_check(gap)
        assert result.total_requirements == len(all_iso_requirements())
        assert result.compliant_count == 0
        # All items should be either non_compliant or not_assessed (score=0)
        assert result.non_compliant_count + result.not_assessed_count > 0

    @pytest.mark.asyncio
    async def test_check_all_max(self):
        assessment = run_assessment("org-001", _make_answers(4))
        gap = await run_gap_analysis(assessment)
        result = run_iso_check(gap)
        assert result.compliant_count > 0
        assert result.overall_score > 3.0

    @pytest.mark.asyncio
    async def test_check_has_clause_summaries(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        result = run_iso_check(gap)
        assert len(result.clause_summaries) == len(ISO_CLAUSES)

    @pytest.mark.asyncio
    async def test_check_items_have_meti_mapping(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        result = run_iso_check(gap)
        for item in result.items:
            assert isinstance(item.meti_mapping, list)
