# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the review cycle service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import (
    AssessmentResult,
    CategoryScore,
    ReviewCycleCreate,
    ReviewRecordCreate,
)
from app.services.review_cycle import (
    advance_next_review,
    create_review_cycle,
    create_review_record,
    get_review_cycle,
    get_upcoming_reviews,
    list_review_cycles,
    list_review_records,
)
from app.services.timeline import save_snapshot


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


class TestReviewCycle:
    """Review cycle tests."""

    def test_create_quarterly_cycle(self):
        """Should create a quarterly review cycle."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
            start_date="2026-01-01",
        ))
        assert cycle.cycle_type == "quarterly"
        assert cycle.start_date == "2026-01-01"
        assert cycle.next_review_date == "2026-04-01"

    def test_create_semi_annual_cycle(self):
        """Should create a semi-annual review cycle."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="semi_annual",
            start_date="2026-01-01",
        ))
        assert cycle.next_review_date == "2026-06-30"

    def test_create_annual_cycle(self):
        """Should create an annual review cycle."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="annual",
            start_date="2026-01-01",
        ))
        assert cycle.next_review_date == "2027-01-01"

    def test_get_review_cycle(self):
        """Should retrieve a cycle by ID."""
        created = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
            start_date="2026-01-01",
        ))
        fetched = get_review_cycle(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_nonexistent_cycle(self):
        """Should return None for nonexistent cycle."""
        assert get_review_cycle("nonexistent") is None

    def test_list_review_cycles(self):
        """Should list all cycles for an org."""
        create_review_cycle(ReviewCycleCreate(
            organization_id="org-001", cycle_type="quarterly",
        ))
        create_review_cycle(ReviewCycleCreate(
            organization_id="org-001", cycle_type="annual",
        ))
        cycles = list_review_cycles("org-001")
        assert len(cycles) == 2

    def test_advance_next_review(self):
        """Should advance the next review date."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
            start_date="2026-01-01",
        ))
        assert cycle.next_review_date == "2026-04-01"

        updated = advance_next_review(cycle.id)
        assert updated is not None
        assert updated.next_review_date == "2026-06-30"

    def test_advance_nonexistent(self):
        """Should return None for nonexistent cycle."""
        assert advance_next_review("nonexistent") is None

    def test_create_review_record(self):
        """Should create a review record."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
            start_date="2026-01-01",
        ))

        record = create_review_record(ReviewRecordCreate(
            organization_id="org-001",
            cycle_id=cycle.id,
            review_date="2026-04-01",
            reviewer="user-001",
            notes="First quarterly review",
        ))
        assert record.cycle_id == cycle.id
        assert record.reviewer == "user-001"

    def test_review_record_advances_cycle(self):
        """Creating a review record should advance the next review date."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
            start_date="2026-01-01",
        ))
        original_next = cycle.next_review_date

        create_review_record(ReviewRecordCreate(
            organization_id="org-001",
            cycle_id=cycle.id,
        ))

        updated_cycle = get_review_cycle(cycle.id)
        assert updated_cycle is not None
        assert updated_cycle.next_review_date != original_next

    def test_list_review_records(self):
        """Should list review records."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
        ))
        create_review_record(ReviewRecordCreate(
            organization_id="org-001",
            cycle_id=cycle.id,
            notes="Review 1",
        ))
        create_review_record(ReviewRecordCreate(
            organization_id="org-001",
            cycle_id=cycle.id,
            notes="Review 2",
        ))

        records = list_review_records("org-001", cycle.id)
        assert len(records) == 2

    def test_list_review_records_all_cycles(self):
        """Should list records across all cycles when cycle_id is empty."""
        c1 = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001", cycle_type="quarterly",
        ))
        c2 = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001", cycle_type="annual",
        ))
        create_review_record(ReviewRecordCreate(
            organization_id="org-001", cycle_id=c1.id,
        ))
        create_review_record(ReviewRecordCreate(
            organization_id="org-001", cycle_id=c2.id,
        ))

        records = list_review_records("org-001")
        assert len(records) == 2

    def test_upcoming_reviews(self):
        """Should return upcoming review dates."""
        create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
            start_date="2026-01-01",
        ))
        upcoming = get_upcoming_reviews("org-001")
        assert len(upcoming) == 1
        assert upcoming[0]["next_review_date"] == "2026-04-01"

    def test_delta_report_no_previous(self):
        """Delta report should indicate no previous data."""
        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
        ))
        record = create_review_record(ReviewRecordCreate(
            organization_id="org-001",
            cycle_id=cycle.id,
        ))
        assert record.delta_report.get("has_previous") is False

    def test_delta_report_with_previous(self):
        """Delta report should show differences with previous snapshot."""
        # Create two snapshots
        a1 = AssessmentResult(
            id="a1", organization_id="org-001",
            overall_score=1.0, maturity_level=1,
            category_scores=[CategoryScore(
                category_id="C01", category_title="T", score=1.0,
                maturity_level=1, question_count=3,
            )],
        )
        a2 = AssessmentResult(
            id="a2", organization_id="org-001",
            overall_score=2.0, maturity_level=3,
            category_scores=[CategoryScore(
                category_id="C01", category_title="T", score=2.0,
                maturity_level=3, question_count=3,
            )],
        )
        save_snapshot("org-001", a1)
        save_snapshot("org-001", a2)

        cycle = create_review_cycle(ReviewCycleCreate(
            organization_id="org-001",
            cycle_type="quarterly",
        ))
        record = create_review_record(ReviewRecordCreate(
            organization_id="org-001",
            cycle_id=cycle.id,
            assessment_id="a2",
        ))
        assert record.delta_report.get("has_previous") is True
        assert record.delta_report.get("overall_delta") == 1.0
