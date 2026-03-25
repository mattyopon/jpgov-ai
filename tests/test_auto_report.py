# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the monthly auto-report service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.services.auto_report import (
    _generate_recommendations,
    build_monthly_report_data,
    generate_monthly_report,
    get_monthly_report,
    list_monthly_reports,
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


class TestMonthlyReportCRUD:
    """Monthly report CRUD tests."""

    def test_generate_report(self):
        """Should generate and persist a monthly report."""
        report = generate_monthly_report(
            organization_id="org-001",
            year=2026,
            month=3,
            score_summary={"current_score": 2.5, "delta": 0.3},
            gap_summary={"total_tasks": 10, "done": 5},
            incident_summary={"total": 2, "open": 1},
            evidence_coverage=0.65,
            recommendations=["改善タスクを進めてください。"],
        )
        assert report.organization_id == "org-001"
        assert report.year == 2026
        assert report.month == 3
        assert report.evidence_coverage == 0.65
        assert len(report.recommendations) == 1

    def test_get_report(self):
        """Should retrieve a monthly report."""
        generate_monthly_report(
            organization_id="org-001",
            year=2026,
            month=3,
        )
        report = get_monthly_report("org-001", 2026, 3)
        assert report is not None
        assert report.year == 2026
        assert report.month == 3

    def test_get_report_not_found(self):
        """Should return None for non-existent report."""
        assert get_monthly_report("org-001", 2025, 1) is None

    def test_list_reports(self):
        """Should list all reports for an organization."""
        generate_monthly_report("org-001", 2026, 1)
        generate_monthly_report("org-001", 2026, 2)
        generate_monthly_report("org-001", 2026, 3)

        reports = list_monthly_reports("org-001")
        assert len(reports) == 3

    def test_list_reports_ordered(self):
        """Should return reports in reverse chronological order."""
        generate_monthly_report("org-001", 2026, 1)
        generate_monthly_report("org-001", 2026, 3)
        generate_monthly_report("org-001", 2026, 2)

        reports = list_monthly_reports("org-001")
        assert reports[0].month == 3
        assert reports[1].month == 2
        assert reports[2].month == 1

    def test_list_reports_different_orgs(self):
        """Should isolate reports by organization."""
        generate_monthly_report("org-001", 2026, 1)
        generate_monthly_report("org-002", 2026, 1)

        assert len(list_monthly_reports("org-001")) == 1
        assert len(list_monthly_reports("org-002")) == 1

    def test_report_preserves_data(self):
        """Should preserve all data fields through JSON serialization."""
        generate_monthly_report(
            organization_id="org-001",
            year=2026,
            month=3,
            score_summary={"current_score": 2.5, "trend": "improving"},
            gap_summary={"total_tasks": 10},
            incident_summary={"total": 3},
            evidence_coverage=0.75,
            benchmark_comparison={"industry_avg": 2.0},
            recommendations=["アクション1", "アクション2"],
        )
        report = get_monthly_report("org-001", 2026, 3)
        assert report is not None
        assert report.score_summary["current_score"] == 2.5
        assert report.gap_summary["total_tasks"] == 10
        assert report.incident_summary["total"] == 3
        assert report.evidence_coverage == 0.75
        assert report.benchmark_comparison["industry_avg"] == 2.0
        assert len(report.recommendations) == 2


class TestRecommendations:
    """Recommendation generation tests."""

    def test_score_declining(self):
        """Should recommend action when score is declining."""
        recs = _generate_recommendations(
            score_summary={"delta": -0.5, "current_score": 1.5},
            gap_summary={},
            incident_summary={},
            evidence_coverage=0.8,
        )
        assert any("低下" in r for r in recs)

    def test_score_flat(self):
        """Should recommend progress check when score is flat."""
        recs = _generate_recommendations(
            score_summary={"delta": 0, "current_score": 2.0},
            gap_summary={},
            incident_summary={},
            evidence_coverage=0.8,
        )
        assert any("横ばい" in r for r in recs)

    def test_overdue_tasks(self):
        """Should flag overdue tasks."""
        recs = _generate_recommendations(
            score_summary={},
            gap_summary={"overdue": 3},
            incident_summary={},
            evidence_coverage=0.8,
        )
        assert any("期限超過" in r for r in recs)

    def test_many_todo_tasks(self):
        """Should flag many pending tasks."""
        recs = _generate_recommendations(
            score_summary={},
            gap_summary={"todo": 10},
            incident_summary={},
            evidence_coverage=0.8,
        )
        assert any("未着手" in r for r in recs)

    def test_open_incidents(self):
        """Should flag open incidents."""
        recs = _generate_recommendations(
            score_summary={},
            gap_summary={},
            incident_summary={"open": 2},
            evidence_coverage=0.8,
        )
        assert any("インシデント" in r for r in recs)

    def test_low_evidence_coverage(self):
        """Should flag low evidence coverage."""
        recs = _generate_recommendations(
            score_summary={},
            gap_summary={},
            incident_summary={},
            evidence_coverage=0.3,
        )
        assert any("エビデンスカバレッジ" in r for r in recs)

    def test_good_state(self):
        """Should give positive message when everything is fine."""
        recs = _generate_recommendations(
            score_summary={"delta": 0.5, "current_score": 3.0},
            gap_summary={"todo": 2, "overdue": 0},
            incident_summary={"open": 0},
            evidence_coverage=0.9,
        )
        assert any("良好" in r for r in recs)


class TestBuildMonthlyReport:
    """Build monthly report integration tests."""

    def test_build_report_empty_org(self):
        """Should build a report for org with no data."""
        report = build_monthly_report_data("org-001", 2026, 3)
        assert report.organization_id == "org-001"
        assert report.year == 2026
        assert report.month == 3
        # Should still have recommendations
        assert len(report.recommendations) > 0

    def test_build_report_persists(self):
        """Should persist the auto-generated report."""
        build_monthly_report_data("org-001", 2026, 3)
        report = get_monthly_report("org-001", 2026, 3)
        assert report is not None
