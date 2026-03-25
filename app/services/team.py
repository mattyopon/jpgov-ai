# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""チーム管理サービス.

Organization（組織）とユーザーの紐付け、ロール管理、
チームメンバーの招待・削除を提供する。
"""

from __future__ import annotations


from app.db.database import (
    OrganizationMemberRow,
    OrganizationRow,
    get_db,
)
from app.models import (
    OrganizationMember,
    OrganizationMemberInvite,
    OrganizationMemberUpdate,
    ROLE_PERMISSIONS,
    TeamSummary,
    UserRole,
)


def add_member(
    invite: OrganizationMemberInvite,
    user_id: str,
    display_name: str = "",
    invited_by: str = "",
) -> OrganizationMember:
    """組織にメンバーを追加.

    Args:
        invite: 招待データ
        user_id: ユーザーID
        display_name: 表示名
        invited_by: 招待者のuser_id

    Returns:
        OrganizationMember: 追加されたメンバー
    """
    member = OrganizationMember(
        organization_id=invite.organization_id,
        user_id=user_id,
        email=invite.email,
        display_name=display_name,
        role=invite.role,
        invited_by=invited_by,
    )

    db = get_db()
    with db.get_session() as session:
        row = OrganizationMemberRow(
            id=member.id,
            organization_id=member.organization_id,
            user_id=member.user_id,
            email=member.email,
            display_name=member.display_name,
            role=member.role.value,
            invited_by=member.invited_by,
            joined_at=member.joined_at,
        )
        session.add(row)
        session.commit()

    return member


def remove_member(organization_id: str, user_id: str) -> bool:
    """組織からメンバーを削除.

    Args:
        organization_id: 組織ID
        user_id: 削除するユーザーID

    Returns:
        bool: 削除成功かどうか
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(OrganizationMemberRow)
            .filter_by(organization_id=organization_id, user_id=user_id)
            .first()
        )
        if row is None:
            return False
        session.delete(row)
        session.commit()
    return True


def update_member_role(
    organization_id: str,
    user_id: str,
    update: OrganizationMemberUpdate,
) -> OrganizationMember | None:
    """メンバーのロールを更新.

    Args:
        organization_id: 組織ID
        user_id: 対象ユーザーID
        update: 更新データ

    Returns:
        OrganizationMember | None: 更新後のメンバー、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(OrganizationMemberRow)
            .filter_by(organization_id=organization_id, user_id=user_id)
            .first()
        )
        if row is None:
            return None

        if update.role is not None:
            row.role = update.role.value

        session.commit()

        return OrganizationMember(
            id=row.id,
            organization_id=row.organization_id,
            user_id=row.user_id,
            email=row.email,
            display_name=row.display_name,
            role=UserRole(row.role),
            invited_by=row.invited_by,
            joined_at=row.joined_at,
        )


def get_member(organization_id: str, user_id: str) -> OrganizationMember | None:
    """組織メンバーを取得.

    Args:
        organization_id: 組織ID
        user_id: ユーザーID

    Returns:
        OrganizationMember | None: メンバー、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(OrganizationMemberRow)
            .filter_by(organization_id=organization_id, user_id=user_id)
            .first()
        )
        if row is None:
            return None
        return OrganizationMember(
            id=row.id,
            organization_id=row.organization_id,
            user_id=row.user_id,
            email=row.email,
            display_name=row.display_name,
            role=UserRole(row.role),
            invited_by=row.invited_by,
            joined_at=row.joined_at,
        )


def list_members(organization_id: str) -> list[OrganizationMember]:
    """組織のメンバー一覧を取得.

    Args:
        organization_id: 組織ID

    Returns:
        list[OrganizationMember]: メンバーリスト
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(OrganizationMemberRow)
            .filter_by(organization_id=organization_id)
            .all()
        )
        return [
            OrganizationMember(
                id=r.id,
                organization_id=r.organization_id,
                user_id=r.user_id,
                email=r.email,
                display_name=r.display_name,
                role=UserRole(r.role),
                invited_by=r.invited_by,
                joined_at=r.joined_at,
            )
            for r in rows
        ]


def get_user_organizations(user_id: str) -> list[dict]:
    """ユーザーが所属する組織の一覧を取得.

    Args:
        user_id: ユーザーID

    Returns:
        list[dict]: 組織情報のリスト
    """
    db = get_db()
    with db.get_session() as session:
        member_rows = (
            session.query(OrganizationMemberRow)
            .filter_by(user_id=user_id)
            .all()
        )

        results = []
        for mr in member_rows:
            org_row = (
                session.query(OrganizationRow)
                .filter_by(id=mr.organization_id)
                .first()
            )
            if org_row:
                results.append({
                    "organization_id": org_row.id,
                    "organization_name": org_row.name,
                    "role": mr.role,
                    "joined_at": mr.joined_at,
                })

        return results


def get_team_summary(organization_id: str) -> TeamSummary | None:
    """チームサマリーを取得.

    Args:
        organization_id: 組織ID

    Returns:
        TeamSummary | None: サマリー、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        org_row = (
            session.query(OrganizationRow)
            .filter_by(id=organization_id)
            .first()
        )
        if org_row is None:
            return None

    members = list_members(organization_id)

    return TeamSummary(
        organization_id=organization_id,
        organization_name=org_row.name,
        member_count=len(members),
        members=members,
    )


def has_permission(
    organization_id: str,
    user_id: str,
    permission: str,
) -> bool:
    """ユーザーが指定権限を持つか判定.

    Args:
        organization_id: 組織ID
        user_id: ユーザーID
        permission: 権限文字列

    Returns:
        bool: 権限があるかどうか
    """
    member = get_member(organization_id, user_id)
    if member is None:
        return False

    role_perms = ROLE_PERMISSIONS.get(member.role.value, [])
    return permission in role_perms
