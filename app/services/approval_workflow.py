# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""承認ワークフローサービス.

ポリシー変更の承認フロー: 作成->レビュー->承認->適用
承認/却下/差し戻し、監査証跡への自動記録を提供する。
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.db.database import ApprovalRequestRow, get_db
from app.models import (
    ApprovalAction,
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalStatus,
)


def create_approval_request(
    data: ApprovalRequestCreate,
    requested_by: str = "",
) -> ApprovalRequest:
    """承認リクエストを作成.

    Args:
        data: リクエスト作成データ
        requested_by: リクエスト作成者のuser_id

    Returns:
        ApprovalRequest: 作成されたリクエスト
    """
    request = ApprovalRequest(
        organization_id=data.organization_id,
        request_type=data.request_type,
        title=data.title,
        description=data.description,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        requested_by=requested_by,
        approver_id=data.approver_id,
    )

    db = get_db()
    with db.get_session() as session:
        row = ApprovalRequestRow(
            id=request.id,
            organization_id=request.organization_id,
            request_type=request.request_type,
            title=request.title,
            description=request.description,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            requested_by=request.requested_by,
            approver_id=request.approver_id,
            status=request.status.value,
            comment=request.comment,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )
        session.add(row)
        session.commit()

    return request


def get_approval_request(request_id: str) -> ApprovalRequest | None:
    """承認リクエストを取得.

    Args:
        request_id: リクエストID

    Returns:
        ApprovalRequest | None: リクエスト、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(ApprovalRequestRow)
            .filter_by(id=request_id)
            .first()
        )
        if row is None:
            return None
        return _row_to_model(row)


def process_approval(
    request_id: str,
    action: ApprovalAction,
    actor_id: str = "",
) -> ApprovalRequest | None:
    """承認/却下/差し戻しを処理.

    Args:
        request_id: リクエストID
        action: アクション（approved / rejected / returned）
        actor_id: 処理者のuser_id

    Returns:
        ApprovalRequest | None: 更新されたリクエスト、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(ApprovalRequestRow)
            .filter_by(id=request_id)
            .first()
        )
        if row is None:
            return None

        # Only pending requests can be processed
        if row.status != ApprovalStatus.PENDING.value:
            return _row_to_model(row)

        row.status = action.action.value
        row.comment = action.comment
        row.updated_at = datetime.now(timezone.utc).isoformat()

        session.commit()

        return _row_to_model(row)


def list_approval_requests(
    organization_id: str,
    status: ApprovalStatus | None = None,
    approver_id: str = "",
) -> list[ApprovalRequest]:
    """承認リクエスト一覧を取得.

    Args:
        organization_id: 組織ID
        status: フィルタするステータス
        approver_id: 承認者IDでフィルタ

    Returns:
        list[ApprovalRequest]: リクエストリスト
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(ApprovalRequestRow).filter_by(
            organization_id=organization_id,
        )
        if status is not None:
            query = query.filter_by(status=status.value)
        if approver_id:
            query = query.filter_by(approver_id=approver_id)

        rows = query.order_by(ApprovalRequestRow.created_at.desc()).all()

        return [_row_to_model(r) for r in rows]


def get_pending_count(organization_id: str) -> int:
    """承認待ちのリクエスト数を取得.

    Args:
        organization_id: 組織ID

    Returns:
        int: 承認待ちの件数
    """
    db = get_db()
    with db.get_session() as session:
        count = (
            session.query(ApprovalRequestRow)
            .filter_by(
                organization_id=organization_id,
                status=ApprovalStatus.PENDING.value,
            )
            .count()
        )
    return count


def _row_to_model(row: ApprovalRequestRow) -> ApprovalRequest:
    """DBの行をモデルに変換.

    Args:
        row: DB行

    Returns:
        ApprovalRequest: モデル
    """
    return ApprovalRequest(
        id=row.id,
        organization_id=row.organization_id,
        request_type=row.request_type,
        title=row.title,
        description=row.description,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        requested_by=row.requested_by,
        approver_id=row.approver_id,
        status=ApprovalStatus(row.status),
        comment=row.comment,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
