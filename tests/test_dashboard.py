# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for the multi-regulation dashboard service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS
from app.models import AnswerItem
from app.services.assessment import run_assessment
from app.services.dashboard import build_multi_regulation_dashboard
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


class TestDashboard:
    """Multi-regulation dashboard tests."""

    @pytest.mark.asyncio
    async def test_dashboard_with_all_regulations(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        dashboard = build_multi_regulation_dashboard("org-001", gap, iso)
        assert dashboard.meti_status is not None
        assert dashboard.iso_status is not None
        assert dashboard.act_status is not None
        assert 0 <= dashboard.overall_compliance_rate <= 1.0

    @pytest.mark.asyncio
    async def test_dashboard_without_iso(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        dashboard = build_multi_regulation_dashboard("org-001", gap)
        assert dashboard.meti_status is not None
        assert dashboard.iso_status is None
        assert dashboard.act_status is not None

    @pytest.mark.asyncio
    async def test_dashboard_all_compliant(self):
        assessment = run_assessment("org-001", _make_answers(4))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        dashboard = build_multi_regulation_dashboard("org-001", gap, iso)
        assert dashboard.meti_status is not None
        assert dashboard.meti_status.compliance_rate == 1.0

    @pytest.mark.asyncio
    async def test_dashboard_all_non_compliant(self):
        assessment = run_assessment("org-001", _make_answers(0))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        dashboard = build_multi_regulation_dashboard("org-001", gap, iso)
        assert dashboard.meti_status is not None
        assert dashboard.meti_status.compliance_rate == 0.0

    @pytest.mark.asyncio
    async def test_priority_actions(self):
        assessment = run_assessment("org-001", _make_answers(0))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        dashboard = build_multi_regulation_dashboard("org-001", gap, iso)
        assert len(dashboard.priority_actions) > 0

    @pytest.mark.asyncio
    async def test_regulation_names(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        dashboard = build_multi_regulation_dashboard("org-001", gap, iso)
        assert "METI" in dashboard.meti_status.regulation_name
        assert "ISO" in dashboard.iso_status.regulation_name
        assert "AI推進法" in dashboard.act_status.regulation_name
