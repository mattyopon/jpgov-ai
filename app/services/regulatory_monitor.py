# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""規制変更モニターサービス.

AI推進法/METIガイドライン/ISO 42001の変更を追跡し、
顧客への影響を自動分析する。

主な機能:
- 規制変更の登録（管理者が手動で登録）
- 顧客の現在のスコアに対する影響分析
- 影響を受ける要件の自動特定
- 対応アクションの自動提案
- Slack通知連携
"""

from __future__ import annotations

import json

from app.db.database import (
    GapAnalysisRow,
    RegulatoryUpdateRow,
    get_db,
)
from app.models import (
    RegulatoryImpact,
    RegulatoryImpactReport,
    RegulatoryUpdate,
    RegulatoryUpdateCreate,
)


def register_update(data: RegulatoryUpdateCreate) -> RegulatoryUpdate:
    """規制変更を登録.

    Args:
        data: 規制変更登録データ

    Returns:
        RegulatoryUpdate: 登録された規制変更
    """
    update = RegulatoryUpdate(
        regulation_name=data.regulation_name,
        title=data.title,
        description=data.description,
        change_type=data.change_type,
        affected_requirements=data.affected_requirements,
        effective_date=data.effective_date,
        deadline=data.deadline,
        severity=data.severity,
        created_by=data.created_by,
    )

    db = get_db()
    with db.get_session() as session:
        row = RegulatoryUpdateRow(
            id=update.id,
            regulation_name=update.regulation_name,
            title=update.title,
            description=update.description,
            change_type=update.change_type,
            affected_requirements_json=json.dumps(
                update.affected_requirements, ensure_ascii=False
            ),
            effective_date=update.effective_date,
            deadline=update.deadline,
            severity=update.severity,
            created_by=update.created_by,
        )
        session.add(row)
        session.commit()

    return update


def list_updates(
    regulation_name: str = "",
    severity: str = "",
) -> list[RegulatoryUpdate]:
    """規制変更一覧を取得.

    Args:
        regulation_name: 規制名でフィルタ（省略時は全て）
        severity: 重大度でフィルタ（省略時は全て）

    Returns:
        list[RegulatoryUpdate]: 規制変更一覧
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(RegulatoryUpdateRow)
        if regulation_name:
            query = query.filter_by(regulation_name=regulation_name)
        if severity:
            query = query.filter_by(severity=severity)

        rows = query.order_by(RegulatoryUpdateRow.created_at.desc()).all()

    return [_row_to_model(r) for r in rows]


def get_update(update_id: str) -> RegulatoryUpdate | None:
    """規制変更を取得.

    Args:
        update_id: 規制変更ID

    Returns:
        RegulatoryUpdate | None
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(RegulatoryUpdateRow)
            .filter_by(id=update_id)
            .first()
        )
        if row is None:
            return None
        return _row_to_model(row)


def analyze_impact(
    update_id: str,
    organization_id: str,
    current_scores: dict[str, float] | None = None,
) -> RegulatoryImpact | None:
    """規制変更の組織への影響を分析.

    Args:
        update_id: 規制変更ID
        organization_id: 組織ID
        current_scores: 要件IDごとの現在スコア（省略時はDBから取得試行）

    Returns:
        RegulatoryImpact | None
    """
    update = get_update(update_id)
    if update is None:
        return None

    # Try to get current scores from latest gap analysis if not provided
    if current_scores is None:
        current_scores = _get_latest_scores(organization_id)

    # Analyze impact on each affected requirement
    affected_scores: dict[str, float] = {}
    impact_messages: list[str] = []
    actions: list[str] = []

    for req_id in update.affected_requirements:
        score = current_scores.get(req_id, 0.0)
        affected_scores[req_id] = score

        if score < 3.0:
            impact_messages.append(
                f"要件{req_id}: 現在スコア{score:.1f} — "
                f"規制変更により基準が厳格化される可能性があります"
            )
            actions.append(f"要件{req_id}のスコアを3.0以上に改善してください")
        elif score < 4.0:
            impact_messages.append(
                f"要件{req_id}: 現在スコア{score:.1f} — "
                f"影響は限定的ですが確認を推奨します"
            )

    # Build estimated impact summary
    if not update.affected_requirements:
        estimated_impact = "影響範囲が未指定のため、詳細な分析ができません"
    elif not affected_scores:
        estimated_impact = "影響範囲が未指定のため、詳細な分析ができません"
    else:
        avg_affected = sum(affected_scores.values()) / len(affected_scores)

        if avg_affected < 1.5:
            estimated_impact = "重大な影響: 複数の要件で大幅なスコア低下の可能性があります"
        elif avg_affected < 2.5:
            estimated_impact = "中程度の影響: 一部の要件でスコア低下の可能性があります"
        elif avg_affected < 3.5:
            estimated_impact = "軽微な影響: 確認は必要ですが大きな影響はありません"
        else:
            estimated_impact = "影響なし: 現在の対応状況で十分です"

    return RegulatoryImpact(
        update_id=update_id,
        organization_id=organization_id,
        regulation_name=update.regulation_name,
        title=update.title,
        affected_requirements=update.affected_requirements,
        current_scores=affected_scores,
        estimated_impact=estimated_impact,
        recommended_actions=actions,
        deadline=update.deadline,
        severity=update.severity,
    )


def analyze_all_impacts(
    organization_id: str,
    current_scores: dict[str, float] | None = None,
) -> RegulatoryImpactReport:
    """全規制変更の影響を一括分析.

    Args:
        organization_id: 組織ID
        current_scores: 要件IDごとの現在スコア

    Returns:
        RegulatoryImpactReport
    """
    updates = list_updates()
    impacts: list[RegulatoryImpact] = []

    for update in updates:
        impact = analyze_impact(
            update.id, organization_id, current_scores
        )
        if impact is not None:
            impacts.append(impact)

    high_count = sum(1 for i in impacts if i.severity == "high")

    return RegulatoryImpactReport(
        organization_id=organization_id,
        impacts=impacts,
        total_updates=len(updates),
        high_severity_count=high_count,
    )


def delete_update(update_id: str) -> bool:
    """規制変更を削除.

    Args:
        update_id: 規制変更ID

    Returns:
        bool: 削除成功か
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(RegulatoryUpdateRow)
            .filter_by(id=update_id)
            .first()
        )
        if row is None:
            return False
        session.delete(row)
        session.commit()
    return True


def _row_to_model(row: RegulatoryUpdateRow) -> RegulatoryUpdate:
    """DB行をモデルに変換."""
    return RegulatoryUpdate(
        id=row.id,
        regulation_name=row.regulation_name,
        title=row.title,
        description=row.description or "",
        change_type=row.change_type or "amendment",
        affected_requirements=json.loads(
            row.affected_requirements_json or "[]"
        ),
        effective_date=row.effective_date or "",
        deadline=row.deadline or "",
        severity=row.severity or "medium",
        created_by=row.created_by or "",
        created_at=row.created_at or "",
    )


def _get_latest_scores(organization_id: str) -> dict[str, float]:
    """最新のギャップ分析からスコアを取得.

    Args:
        organization_id: 組織ID

    Returns:
        dict[str, float]: 要件ID -> スコア
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(GapAnalysisRow)
            .filter_by(organization_id=organization_id)
            .order_by(GapAnalysisRow.created_at.desc())
            .first()
        )
        if row is None:
            return {}

    try:
        data = json.loads(row.result_json or "{}")
        gaps = data.get("gaps", [])
        return {g["req_id"]: g.get("current_score", 0.0) for g in gaps}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}
