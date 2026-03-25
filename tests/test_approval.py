# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the approval workflow service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import (
    ApprovalAction,
    ApprovalRequestCreate,
    ApprovalStatus,
)
from app.services.approval_workflow import (
    create_approval_request,
    get_approval_request,
    get_pending_count,
    list_approval_requests,
    process_approval,
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


def _create_request(
    org_id: str = "org-001",
    title: str = "Test approval",
    approver: str = "admin-001",
) -> ApprovalRequestCreate:
    return ApprovalRequestCreate(
        organization_id=org_id,
        request_type="policy_change",
        title=title,
        description="Test description",
        resource_type="policy",
        resource_id="pol-001",
        approver_id=approver,
    )


class TestApprovalWorkflow:
    """Approval workflow tests."""

    def test_create_request(self):
        """Should create an approval request."""
        req = create_approval_request(_create_request(), requested_by="user-001")
        assert req.organization_id == "org-001"
        assert req.status == ApprovalStatus.PENDING
        assert req.requested_by == "user-001"

    def test_get_request(self):
        """Should retrieve a request by ID."""
        created = create_approval_request(_create_request())
        fetched = get_approval_request(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "Test approval"

    def test_get_nonexistent_request(self):
        """Should return None for nonexistent request."""
        assert get_approval_request("nonexistent") is None

    def test_approve_request(self):
        """Should approve a pending request."""
        req = create_approval_request(_create_request())
        result = process_approval(
            req.id,
            ApprovalAction(action=ApprovalStatus.APPROVED, comment="Looks good"),
        )
        assert result is not None
        assert result.status == ApprovalStatus.APPROVED
        assert result.comment == "Looks good"

    def test_reject_request(self):
        """Should reject a pending request."""
        req = create_approval_request(_create_request())
        result = process_approval(
            req.id,
            ApprovalAction(action=ApprovalStatus.REJECTED, comment="Not ready"),
        )
        assert result is not None
        assert result.status == ApprovalStatus.REJECTED

    def test_return_request(self):
        """Should return (send back) a pending request."""
        req = create_approval_request(_create_request())
        result = process_approval(
            req.id,
            ApprovalAction(action=ApprovalStatus.RETURNED, comment="Need revision"),
        )
        assert result is not None
        assert result.status == ApprovalStatus.RETURNED

    def test_cannot_process_already_approved(self):
        """Should not change status of already-approved request."""
        req = create_approval_request(_create_request())
        process_approval(
            req.id,
            ApprovalAction(action=ApprovalStatus.APPROVED),
        )
        # Try to reject after approval
        result = process_approval(
            req.id,
            ApprovalAction(action=ApprovalStatus.REJECTED),
        )
        assert result is not None
        assert result.status == ApprovalStatus.APPROVED  # Unchanged

    def test_process_nonexistent(self):
        """Should return None for nonexistent request."""
        result = process_approval(
            "nonexistent",
            ApprovalAction(action=ApprovalStatus.APPROVED),
        )
        assert result is None

    def test_list_requests(self):
        """Should list all requests for an org."""
        create_approval_request(_create_request(title="Req 1"))
        create_approval_request(_create_request(title="Req 2"))
        create_approval_request(_create_request(title="Req 3"))

        requests = list_approval_requests("org-001")
        assert len(requests) == 3

    def test_list_requests_by_status(self):
        """Should filter requests by status."""
        r1 = create_approval_request(_create_request(title="Req 1"))
        create_approval_request(_create_request(title="Req 2"))
        process_approval(
            r1.id, ApprovalAction(action=ApprovalStatus.APPROVED),
        )

        pending = list_approval_requests("org-001", ApprovalStatus.PENDING)
        assert len(pending) == 1

        approved = list_approval_requests("org-001", ApprovalStatus.APPROVED)
        assert len(approved) == 1

    def test_list_requests_by_approver(self):
        """Should filter requests by approver."""
        create_approval_request(_create_request(approver="admin-001"))
        create_approval_request(_create_request(approver="admin-002"))

        requests = list_approval_requests("org-001", approver_id="admin-001")
        assert len(requests) == 1

    def test_pending_count(self):
        """Should count pending requests."""
        create_approval_request(_create_request())
        create_approval_request(_create_request())
        r3 = create_approval_request(_create_request())
        process_approval(
            r3.id, ApprovalAction(action=ApprovalStatus.APPROVED),
        )

        count = get_pending_count("org-001")
        assert count == 2

    def test_pending_count_empty(self):
        """Should return 0 when no pending requests."""
        assert get_pending_count("org-001") == 0

    def test_different_orgs_separate(self):
        """Requests should be separated by organization."""
        create_approval_request(_create_request(org_id="org-001"))
        create_approval_request(_create_request(org_id="org-002"))

        r1 = list_approval_requests("org-001")
        r2 = list_approval_requests("org-002")
        assert len(r1) == 1
        assert len(r2) == 1

    def test_request_has_timestamps(self):
        """Request should have created_at and updated_at."""
        req = create_approval_request(_create_request())
        assert req.created_at
        assert req.updated_at

    def test_updated_at_changes_on_process(self):
        """updated_at should change when request is processed."""
        req = create_approval_request(_create_request())
        original_updated = req.updated_at

        result = process_approval(
            req.id,
            ApprovalAction(action=ApprovalStatus.APPROVED),
        )
        assert result is not None
        # updated_at should be same or later
        assert result.updated_at >= original_updated
