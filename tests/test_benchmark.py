# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the benchmark service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import AssessmentResult, CategoryScore
from app.services.benchmark import (
    K_ANONYMITY_THRESHOLD,
    get_industry_benchmark,
    get_my_position,
    submit_benchmark_data,
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


def _make_assessment(score: float, level: int) -> AssessmentResult:
    """Create a mock assessment result."""
    return AssessmentResult(
        organization_id="org-test",
        overall_score=score,
        maturity_level=level,
        category_scores=[
            CategoryScore(
                category_id="C01",
                category_title="Category 1",
                score=score,
                maturity_level=level,
                question_count=3,
            ),
            CategoryScore(
                category_id="C02",
                category_title="Category 2",
                score=score * 0.8,
                maturity_level=max(1, level - 1),
                question_count=2,
            ),
        ],
    )


def _submit_n_orgs(n: int, industry: str = "IT", base_score: float = 2.0,
                   prefix: str = ""):
    """Submit benchmark data for n organizations."""
    tag = prefix or industry.lower().replace(" ", "")
    for i in range(n):
        score = base_score + (i * 0.2)
        assessment = _make_assessment(min(score, 4.0), min(int(score) + 1, 5))
        submit_benchmark_data(
            organization_id=f"org-{tag}-{i:03d}",
            industry=industry,
            size_bucket="medium",
            assessment=assessment,
        )


class TestBenchmark:
    """Industry benchmark tests."""

    def test_submit_benchmark_data(self):
        """Should submit benchmark data successfully."""
        assessment = _make_assessment(2.0, 3)
        result = submit_benchmark_data(
            "org-001", "IT", "medium", assessment,
        )
        assert result is True

    def test_submit_updates_existing(self):
        """Should update existing data on resubmit."""
        a1 = _make_assessment(1.0, 1)
        a2 = _make_assessment(3.0, 4)
        submit_benchmark_data("org-001", "IT", "medium", a1)
        submit_benchmark_data("org-001", "IT", "medium", a2)

        # Should only have one entry
        db = get_db()
        from app.db.database import BenchmarkDataRow
        with db.get_session() as session:
            count = session.query(BenchmarkDataRow).filter_by(
                organization_id="org-001"
            ).count()
        assert count == 1

    def test_k_anonymity_blocks_small_sample(self):
        """Should return None when sample is below k threshold."""
        _submit_n_orgs(K_ANONYMITY_THRESHOLD - 1)
        result = get_industry_benchmark("IT")
        assert result is None

    def test_k_anonymity_allows_sufficient_sample(self):
        """Should return benchmark when sample meets k threshold."""
        _submit_n_orgs(K_ANONYMITY_THRESHOLD)
        result = get_industry_benchmark("IT")
        assert result is not None
        assert result.sample_count == K_ANONYMITY_THRESHOLD

    def test_benchmark_avg_score(self):
        """Should calculate correct average score."""
        _submit_n_orgs(5, base_score=2.0)
        result = get_industry_benchmark("IT")
        assert result is not None
        assert result.avg_overall_score > 0

    def test_benchmark_category_benchmarks(self):
        """Should include category benchmarks."""
        _submit_n_orgs(5)
        result = get_industry_benchmark("IT")
        assert result is not None
        assert "C01" in result.category_benchmarks

    def test_benchmark_percentile_thresholds(self):
        """Should include percentile thresholds."""
        _submit_n_orgs(10)
        result = get_industry_benchmark("IT")
        assert result is not None
        assert "25" in result.percentile_thresholds
        assert "50" in result.percentile_thresholds
        assert "75" in result.percentile_thresholds

    def test_benchmark_top_improvement_areas(self):
        """Should include top improvement areas."""
        _submit_n_orgs(5)
        result = get_industry_benchmark("IT")
        assert result is not None
        assert len(result.top_improvement_areas) > 0

    def test_benchmark_by_size(self):
        """Should filter by size bucket."""
        for i in range(5):
            assessment = _make_assessment(2.0 + i * 0.1, 3)
            submit_benchmark_data(f"org-m-{i}", "IT", "medium", assessment)
        for i in range(5):
            assessment = _make_assessment(3.0 + i * 0.1, 4)
            submit_benchmark_data(f"org-l-{i}", "IT", "large", assessment)

        medium = get_industry_benchmark("IT", "medium")
        large = get_industry_benchmark("IT", "large")
        assert medium is not None
        assert large is not None
        assert large.avg_overall_score > medium.avg_overall_score

    def test_opt_out_excluded(self):
        """Opted-out orgs should not be included in benchmarks."""
        for i in range(4):
            assessment = _make_assessment(2.0, 3)
            submit_benchmark_data(f"org-{i}", "IT", "medium", assessment)

        # 5th org opts out
        assessment = _make_assessment(2.0, 3)
        submit_benchmark_data("org-optout", "IT", "medium", assessment, opt_in=False)

        # Only 4 opted-in, below threshold
        result = get_industry_benchmark("IT")
        assert result is None

    def test_different_industries_separate(self):
        """Different industries should have separate benchmarks."""
        _submit_n_orgs(5, industry="IT")
        _submit_n_orgs(5, industry="Finance")

        it_bench = get_industry_benchmark("IT")
        fin_bench = get_industry_benchmark("Finance")
        assert it_bench is not None
        assert fin_bench is not None

    def test_my_position(self):
        """Should calculate my position in the industry."""
        _submit_n_orgs(5, base_score=1.0)
        # Submit our own data
        our_assessment = _make_assessment(3.0, 4)
        submit_benchmark_data("org-ours", "IT", "medium", our_assessment)

        position = get_my_position("org-ours", "IT", 3.0)
        assert position is not None
        assert position.my_score == 3.0
        assert position.percentile > 0

    def test_my_position_insufficient_data(self):
        """Should return None when benchmark data is insufficient."""
        _submit_n_orgs(3)
        position = get_my_position("org-001", "IT", 2.0)
        assert position is None

    def test_my_position_gap_areas(self):
        """Should identify gap areas."""
        _submit_n_orgs(5, base_score=3.0)

        # Submit our data with lower scores
        our_assessment = _make_assessment(1.0, 1)
        submit_benchmark_data("org-ours", "IT", "medium", our_assessment)

        position = get_my_position("org-ours", "IT", 1.0)
        assert position is not None
        assert len(position.gap_areas) > 0
        # All gaps should be negative (we're below average)
        for gap in position.gap_areas:
            assert gap["gap"] < 0
