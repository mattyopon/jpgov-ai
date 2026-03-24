# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the export service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS
from app.models import AnswerItem, ExportFormat
from app.services.assessment import run_assessment
from app.services.export_service import (
    export_assessment,
    export_gap_analysis,
    export_iso_check,
    generate_iso_certification_package,
    generate_meti_report_package,
)
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


class TestExportService:
    """Export service tests."""

    @pytest.mark.asyncio
    async def test_export_assessment_json(self):
        assessment = run_assessment("org-001", _make_answers(2))
        result = export_assessment(assessment, ExportFormat.JSON)
        assert "overall_score" in result
        assert "category_scores" in result

    @pytest.mark.asyncio
    async def test_export_assessment_csv(self):
        assessment = run_assessment("org-001", _make_answers(2))
        result = export_assessment(assessment, ExportFormat.CSV)
        assert "category_id" in result
        assert "score" in result

    @pytest.mark.asyncio
    async def test_export_gap_analysis_json(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        result = export_gap_analysis(gap, ExportFormat.JSON)
        assert "gaps" in result

    @pytest.mark.asyncio
    async def test_export_gap_analysis_csv(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        result = export_gap_analysis(gap, ExportFormat.CSV)
        assert "req_id" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_export_iso_check_json(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        result = export_iso_check(iso, ExportFormat.JSON)
        assert "items" in result

    @pytest.mark.asyncio
    async def test_export_iso_check_csv(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        result = export_iso_check(iso, ExportFormat.CSV)
        assert "clause" in result

    @pytest.mark.asyncio
    async def test_iso_certification_package(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        iso = run_iso_check(gap)
        package = generate_iso_certification_package(assessment, gap, iso, "Test Corp")
        assert package.package_type == "iso42001_certification"
        assert len(package.files) >= 7  # 6 data files + 1 summary

    @pytest.mark.asyncio
    async def test_meti_report_package(self):
        assessment = run_assessment("org-001", _make_answers(2))
        gap = await run_gap_analysis(assessment)
        package = generate_meti_report_package(assessment, gap, "Test Corp")
        assert package.package_type == "meti_report"
        assert len(package.files) >= 3
