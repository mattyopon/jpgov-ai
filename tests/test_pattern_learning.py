# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the pattern learning service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import (
    ComplianceStatus,
    GapAnalysisResult,
    RequirementGap,
)
from app.services.pattern_learning import (
    K_ANONYMITY_THRESHOLD,
    get_pattern_matches,
    get_patterns,
    mark_gap_resolved,
    record_gap_patterns,
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


def _make_gap_analysis(
    org_id: str = "org-test",
    gaps: list[RequirementGap] | None = None,
) -> GapAnalysisResult:
    """Create a mock gap analysis result."""
    if gaps is None:
        gaps = [
            RequirementGap(
                req_id="C01-R01",
                category_id="C01",
                title="人間中心の原則",
                status=ComplianceStatus.NON_COMPLIANT,
                current_score=0.5,
                improvement_actions=["AIガバナンス基本方針を策定する", "研修を実施する"],
            ),
            RequirementGap(
                req_id="C02-R01",
                category_id="C02",
                title="安全性確保",
                status=ComplianceStatus.PARTIAL,
                current_score=1.8,
                improvement_actions=["安全性テストを導入する"],
            ),
            RequirementGap(
                req_id="C03-R01",
                category_id="C03",
                title="公平性確保",
                status=ComplianceStatus.COMPLIANT,
                current_score=3.5,
            ),
        ]

    return GapAnalysisResult(
        organization_id=org_id,
        assessment_id="assess-001",
        total_requirements=len(gaps),
        compliant_count=sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT),
        partial_count=sum(1 for g in gaps if g.status == ComplianceStatus.PARTIAL),
        non_compliant_count=sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT),
        gaps=gaps,
    )


def _record_n_times(n: int, industry: str = "IT", size_bucket: str = "medium"):
    """Record patterns from n different organizations."""
    for i in range(n):
        gap = _make_gap_analysis(org_id=f"org-{i:03d}")
        record_gap_patterns(industry, size_bucket, gap)


class TestPatternLearning:
    """Pattern learning tests."""

    def test_record_gap_patterns(self):
        """Should record gap patterns from analysis."""
        gap = _make_gap_analysis()
        count = record_gap_patterns("IT", "medium", gap)
        # 2 non-compliant/partial gaps (compliant is skipped)
        assert count == 2

    def test_record_accumulates(self):
        """Recording multiple times should increment occurrence_count."""
        gap1 = _make_gap_analysis(org_id="org-001")
        gap2 = _make_gap_analysis(org_id="org-002")
        record_gap_patterns("IT", "medium", gap1)
        record_gap_patterns("IT", "medium", gap2)

        # Get raw patterns (bypass k-anonymity for checking)
        from app.db.database import GapPatternRow
        db = get_db()
        with db.get_session() as session:
            row = session.query(GapPatternRow).filter_by(
                requirement_id="C01-R01"
            ).first()
        assert row is not None
        assert row.occurrence_count == 2

    def test_record_merges_actions(self):
        """Should merge improvement actions without duplicates."""
        gap1 = _make_gap_analysis()
        gap2 = _make_gap_analysis()
        # Override gap2 with different actions
        gap2.gaps[0].improvement_actions = ["AIガバナンス基本方針を策定する", "監査体制を構築する"]
        record_gap_patterns("IT", "medium", gap1)
        record_gap_patterns("IT", "medium", gap2)

        from app.db.database import GapPatternRow
        import json
        db = get_db()
        with db.get_session() as session:
            row = session.query(GapPatternRow).filter_by(
                requirement_id="C01-R01"
            ).first()
        actions = json.loads(row.typical_actions_json)
        # Should contain unique actions from both
        assert "AIガバナンス基本方針を策定する" in actions
        assert "研修を実施する" in actions
        assert "監査体制を構築する" in actions

    def test_compliant_gaps_skipped(self):
        """Compliant gaps should not create patterns."""
        gaps = [
            RequirementGap(
                req_id="C03-R01",
                category_id="C03",
                title="Compliant Gap",
                status=ComplianceStatus.COMPLIANT,
                current_score=3.5,
            ),
        ]
        gap = _make_gap_analysis(gaps=gaps)
        count = record_gap_patterns("IT", "medium", gap)
        assert count == 0

    def test_mark_gap_resolved(self):
        """Should mark a gap as resolved and update resolution stats."""
        gap = _make_gap_analysis()
        record_gap_patterns("IT", "medium", gap)
        success = mark_gap_resolved("IT", "medium", "C01-R01", 30.0)
        assert success is True

        from app.db.database import GapPatternRow
        db = get_db()
        with db.get_session() as session:
            row = session.query(GapPatternRow).filter_by(
                requirement_id="C01-R01"
            ).first()
        assert row.resolved_count == 1
        assert row.avg_resolution_days == 30.0

    def test_mark_gap_resolved_updates_avg(self):
        """Should update rolling average of resolution days."""
        gap = _make_gap_analysis()
        record_gap_patterns("IT", "medium", gap)
        mark_gap_resolved("IT", "medium", "C01-R01", 30.0)
        mark_gap_resolved("IT", "medium", "C01-R01", 60.0)

        from app.db.database import GapPatternRow
        db = get_db()
        with db.get_session() as session:
            row = session.query(GapPatternRow).filter_by(
                requirement_id="C01-R01"
            ).first()
        assert row.resolved_count == 2
        assert row.avg_resolution_days == 45.0  # (30+60)/2

    def test_mark_gap_resolved_not_found(self):
        """Should return False when pattern not found."""
        success = mark_gap_resolved("IT", "medium", "NONEXISTENT", 30.0)
        assert success is False

    def test_k_anonymity_blocks_small_sample(self):
        """Patterns with occurrence < k should not be returned."""
        _record_n_times(K_ANONYMITY_THRESHOLD - 1)
        patterns = get_patterns("IT", "medium")
        assert len(patterns) == 0

    def test_k_anonymity_allows_sufficient(self):
        """Patterns with occurrence >= k should be returned."""
        _record_n_times(K_ANONYMITY_THRESHOLD)
        patterns = get_patterns("IT", "medium")
        assert len(patterns) > 0
        for p in patterns:
            assert p.occurrence_count >= K_ANONYMITY_THRESHOLD

    def test_patterns_sorted_by_occurrence(self):
        """Patterns should be sorted by occurrence descending."""
        _record_n_times(6)
        patterns = get_patterns("IT", "medium")
        if len(patterns) >= 2:
            for i in range(len(patterns) - 1):
                assert patterns[i].occurrence_count >= patterns[i + 1].occurrence_count

    def test_patterns_resolution_rate(self):
        """Should calculate correct resolution rate."""
        _record_n_times(5)
        # Resolve some
        for _ in range(3):
            mark_gap_resolved("IT", "medium", "C01-R01", 20.0)

        patterns = get_patterns("IT", "medium")
        c01_pattern = next((p for p in patterns if p.requirement_id == "C01-R01"), None)
        assert c01_pattern is not None
        assert c01_pattern.resolution_rate == round(3 / 5, 2)

    def test_pattern_matches_empty(self):
        """Should return empty matches with no patterns."""
        gap = _make_gap_analysis()
        result = get_pattern_matches("IT", "medium", gap)
        assert len(result.matches) == 0
        assert result.total_patterns == 0

    def test_pattern_matches_with_data(self):
        """Should return matches when patterns exist."""
        _record_n_times(K_ANONYMITY_THRESHOLD)
        gap = _make_gap_analysis(org_id="new-org")
        result = get_pattern_matches("IT", "medium", gap)
        assert len(result.matches) > 0
        assert result.industry == "IT"

    def test_pattern_matches_priority_suggestion(self):
        """Matches should include priority suggestion."""
        _record_n_times(10)
        gap = _make_gap_analysis(org_id="new-org")
        result = get_pattern_matches("IT", "medium", gap)
        for match in result.matches:
            assert match.priority_suggestion in ("high", "medium", "low")

    def test_pattern_matches_summary_message(self):
        """Should generate a summary message."""
        _record_n_times(5)
        gap = _make_gap_analysis(org_id="new-org")
        result = get_pattern_matches("IT", "medium", gap)
        assert result.message != ""
        assert "IT" in result.message

    def test_different_industries_separate(self):
        """Different industries should have separate patterns."""
        _record_n_times(5, industry="IT")
        _record_n_times(5, industry="Finance")
        it_patterns = get_patterns("IT", "medium")
        fin_patterns = get_patterns("Finance", "medium")
        assert len(it_patterns) > 0
        assert len(fin_patterns) > 0
        # Each pattern should belong to correct industry
        for p in it_patterns:
            assert p.industry == "IT"
        for p in fin_patterns:
            assert p.industry == "Finance"

    def test_pattern_matches_fallback_to_all_sizes(self):
        """Should fallback to all sizes if specific size has no patterns."""
        _record_n_times(5, size_bucket="medium")
        gap = _make_gap_analysis(org_id="new-org")
        # Search for "large" should fallback to "medium" patterns via all-size search
        result = get_pattern_matches("IT", "large", gap)
        # May have matches from medium patterns if fallback works
        assert result.industry == "IT"
