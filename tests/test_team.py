# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the team management service."""

from __future__ import annotations


import pytest

from app.db.database import OrganizationRow, get_db, reset_db
from app.models import (
    OrganizationMemberInvite,
    OrganizationMemberUpdate,
    ROLE_PERMISSIONS,
    UserRole,
)
from app.services.team import (
    add_member,
    get_member,
    get_team_summary,
    get_user_organizations,
    has_permission,
    list_members,
    remove_member,
    update_member_role,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    # Create a test organization
    with db.get_session() as session:
        session.add(OrganizationRow(
            id="org-001",
            name="Test Corp",
            industry="IT",
            size="medium",
        ))
        session.commit()
    yield
    reset_db()


def _invite(org_id: str = "org-001", email: str = "user@test.com",
            role: UserRole = UserRole.MEMBER) -> OrganizationMemberInvite:
    return OrganizationMemberInvite(
        organization_id=org_id,
        email=email,
        role=role,
    )


class TestTeamManagement:
    """Team management tests."""

    def test_add_member(self):
        """Should add a member to the organization."""
        member = add_member(_invite(), user_id="user-001", display_name="Test User")
        assert member.organization_id == "org-001"
        assert member.user_id == "user-001"
        assert member.role == UserRole.MEMBER

    def test_list_members(self):
        """Should list all members."""
        add_member(_invite(email="a@test.com"), user_id="user-a")
        add_member(_invite(email="b@test.com"), user_id="user-b")
        members = list_members("org-001")
        assert len(members) == 2

    def test_remove_member(self):
        """Should remove a member."""
        add_member(_invite(), user_id="user-001")
        assert remove_member("org-001", "user-001") is True
        assert get_member("org-001", "user-001") is None

    def test_remove_nonexistent_member(self):
        """Should return False for nonexistent member."""
        assert remove_member("org-001", "nonexistent") is False

    def test_update_member_role(self):
        """Should update member role."""
        add_member(_invite(), user_id="user-001")
        updated = update_member_role(
            "org-001", "user-001",
            OrganizationMemberUpdate(role=UserRole.ADMIN),
        )
        assert updated is not None
        assert updated.role == UserRole.ADMIN

    def test_update_nonexistent_member(self):
        """Should return None for nonexistent member."""
        result = update_member_role(
            "org-001", "nonexistent",
            OrganizationMemberUpdate(role=UserRole.ADMIN),
        )
        assert result is None

    def test_get_member(self):
        """Should retrieve a specific member."""
        add_member(_invite(), user_id="user-001", display_name="Alice")
        member = get_member("org-001", "user-001")
        assert member is not None
        assert member.display_name == "Alice"

    def test_get_nonexistent_member(self):
        """Should return None for nonexistent member."""
        assert get_member("org-001", "nonexistent") is None

    def test_user_organizations(self):
        """Should list organizations for a user."""
        add_member(_invite(), user_id="user-001")
        orgs = get_user_organizations("user-001")
        assert len(orgs) == 1
        assert orgs[0]["organization_name"] == "Test Corp"

    def test_team_summary(self):
        """Should return team summary."""
        add_member(_invite(email="a@test.com"), user_id="user-a")
        add_member(_invite(email="b@test.com"), user_id="user-b")
        summary = get_team_summary("org-001")
        assert summary is not None
        assert summary.member_count == 2
        assert summary.organization_name == "Test Corp"

    def test_team_summary_nonexistent_org(self):
        """Should return None for nonexistent org."""
        assert get_team_summary("nonexistent") is None

    def test_has_permission_owner(self):
        """Owner should have all permissions."""
        add_member(_invite(role=UserRole.OWNER), user_id="user-001")
        assert has_permission("org-001", "user-001", "org.manage") is True
        assert has_permission("org-001", "user-001", "org.delete") is True

    def test_has_permission_viewer(self):
        """Viewer should have limited permissions."""
        add_member(_invite(role=UserRole.VIEWER), user_id="user-001")
        assert has_permission("org-001", "user-001", "assessment.view") is True
        assert has_permission("org-001", "user-001", "org.manage") is False

    def test_has_permission_nonmember(self):
        """Non-member should have no permissions."""
        assert has_permission("org-001", "nonexistent", "assessment.view") is False

    def test_all_roles_defined(self):
        """All UserRole values should have permission definitions."""
        for role in UserRole:
            assert role.value in ROLE_PERMISSIONS

    def test_multiple_orgs_per_user(self):
        """A user can belong to multiple organizations."""
        db = get_db()
        with db.get_session() as session:
            session.add(OrganizationRow(
                id="org-002",
                name="Second Corp",
                industry="Finance",
            ))
            session.commit()

        add_member(_invite(org_id="org-001"), user_id="user-001")
        add_member(_invite(org_id="org-002"), user_id="user-001")
        orgs = get_user_organizations("user-001")
        assert len(orgs) == 2
