# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""AIインシデント管理サービス.

AIインシデントの記録・追跡・統計:
- インシデント種別（ハルシネーション、バイアス、データ漏洩等）
- 重大度（Critical/High/Medium/Low）
- 対応状況（Open/Investigating/Resolved/Closed）
- 根本原因分析（RCA）
- AI推進法第18条のインシデント報告義務との紐付け
- 統計ダッシュボード
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.db.database import IncidentRCARow, IncidentRow, get_db
from app.models import (
    Incident,
    IncidentCreate,
    IncidentRCA,
    IncidentRCACreate,
    IncidentSeverity,
    IncidentStats,
    IncidentStatus,
    IncidentType,
    IncidentUpdate,
)


def create_incident(data: IncidentCreate, actor_id: str = "") -> Incident:
    """インシデントを記録.

    Args:
        data: インシデント作成データ
        actor_id: 記録者のuser_id

    Returns:
        Incident: 作成されたインシデント
    """
    incident = Incident(
        organization_id=data.organization_id,
        title=data.title,
        description=data.description,
        incident_type=data.incident_type,
        severity=data.severity,
        affected_system=data.affected_system,
        impact_description=data.impact_description,
        detected_by=data.detected_by or actor_id,
        related_requirements=data.related_requirements,
        regulatory_report_required=data.regulatory_report_required,
    )

    db = get_db()
    with db.get_session() as session:
        row = IncidentRow(
            id=incident.id,
            organization_id=incident.organization_id,
            title=incident.title,
            description=incident.description,
            incident_type=incident.incident_type.value,
            severity=incident.severity.value,
            affected_system=incident.affected_system,
            impact_description=incident.impact_description,
            status=incident.status.value,
            detected_by=incident.detected_by,
            detected_at=incident.detected_at,
            related_requirements_json=json.dumps(incident.related_requirements),
            regulatory_report_required=1 if incident.regulatory_report_required else 0,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )
        session.add(row)
        session.commit()

    return incident


def get_incident(incident_id: str) -> Incident | None:
    """インシデントを取得.

    Args:
        incident_id: インシデントID

    Returns:
        Incident | None: インシデント、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = session.query(IncidentRow).filter_by(id=incident_id).first()
        if row is None:
            return None
        return _row_to_model(row)


def update_incident(
    incident_id: str,
    update: IncidentUpdate,
) -> Incident | None:
    """インシデントを更新.

    Args:
        incident_id: インシデントID
        update: 更新データ

    Returns:
        Incident | None: 更新されたインシデント、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = session.query(IncidentRow).filter_by(id=incident_id).first()
        if row is None:
            return None

        if update.status is not None:
            row.status = update.status.value
        if update.severity is not None:
            row.severity = update.severity.value
        if update.impact_description is not None:
            row.impact_description = update.impact_description
        if update.resolved_at is not None:
            row.resolved_at = update.resolved_at
        if update.regulatory_report_sent is not None:
            row.regulatory_report_sent = 1 if update.regulatory_report_sent else 0

        row.updated_at = datetime.now(timezone.utc).isoformat()
        session.commit()
        return _row_to_model(row)


def list_incidents(
    organization_id: str,
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    incident_type: IncidentType | None = None,
) -> list[Incident]:
    """インシデント一覧を取得.

    Args:
        organization_id: 組織ID
        status: ステータスフィルタ
        severity: 重大度フィルタ
        incident_type: 種別フィルタ

    Returns:
        list[Incident]: インシデントリスト
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(IncidentRow).filter_by(organization_id=organization_id)
        if status is not None:
            query = query.filter_by(status=status.value)
        if severity is not None:
            query = query.filter_by(severity=severity.value)
        if incident_type is not None:
            query = query.filter_by(incident_type=incident_type.value)

        rows = query.order_by(IncidentRow.created_at.desc()).all()
        return [_row_to_model(r) for r in rows]


def get_incident_stats(organization_id: str) -> IncidentStats:
    """インシデント統計を取得.

    Args:
        organization_id: 組織ID

    Returns:
        IncidentStats: 統計データ
    """
    incidents = list_incidents(organization_id)

    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    open_count = 0
    resolution_hours: list[float] = []

    for inc in incidents:
        by_severity[inc.severity.value] = by_severity.get(inc.severity.value, 0) + 1
        by_type[inc.incident_type.value] = by_type.get(inc.incident_type.value, 0) + 1
        by_status[inc.status.value] = by_status.get(inc.status.value, 0) + 1

        if inc.status in (IncidentStatus.OPEN, IncidentStatus.INVESTIGATING):
            open_count += 1

        if inc.resolved_at and inc.detected_at:
            try:
                detected = datetime.fromisoformat(inc.detected_at)
                resolved = datetime.fromisoformat(inc.resolved_at)
                hours = (resolved - detected).total_seconds() / 3600
                resolution_hours.append(hours)
            except (ValueError, TypeError):
                pass

    avg_hours = sum(resolution_hours) / len(resolution_hours) if resolution_hours else 0.0

    return IncidentStats(
        organization_id=organization_id,
        total_count=len(incidents),
        by_severity=by_severity,
        by_type=by_type,
        by_status=by_status,
        avg_resolution_hours=round(avg_hours, 2),
        open_count=open_count,
    )


# ── RCA (Root Cause Analysis) ───────────────────────────────────

def create_rca(data: IncidentRCACreate) -> IncidentRCA:
    """根本原因分析を作成.

    Args:
        data: RCA作成データ

    Returns:
        IncidentRCA: 作成されたRCA
    """
    rca = IncidentRCA(
        incident_id=data.incident_id,
        root_cause=data.root_cause,
        contributing_factors=data.contributing_factors,
        corrective_actions=data.corrective_actions,
        preventive_actions=data.preventive_actions,
        lessons_learned=data.lessons_learned,
    )

    db = get_db()
    with db.get_session() as session:
        row = IncidentRCARow(
            id=rca.id,
            incident_id=rca.incident_id,
            root_cause=rca.root_cause,
            contributing_factors_json=json.dumps(rca.contributing_factors, ensure_ascii=False),
            corrective_actions_json=json.dumps(rca.corrective_actions, ensure_ascii=False),
            preventive_actions_json=json.dumps(rca.preventive_actions, ensure_ascii=False),
            lessons_learned=rca.lessons_learned,
            created_at=rca.created_at,
        )
        session.add(row)
        session.commit()

    return rca


def get_rca(incident_id: str) -> IncidentRCA | None:
    """インシデントのRCAを取得.

    Args:
        incident_id: インシデントID

    Returns:
        IncidentRCA | None: RCA、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(IncidentRCARow)
            .filter_by(incident_id=incident_id)
            .first()
        )
        if row is None:
            return None
        return IncidentRCA(
            id=row.id,
            incident_id=row.incident_id,
            root_cause=row.root_cause,
            contributing_factors=json.loads(row.contributing_factors_json),
            corrective_actions=json.loads(row.corrective_actions_json),
            preventive_actions=json.loads(row.preventive_actions_json),
            lessons_learned=row.lessons_learned,
            created_at=row.created_at,
        )


# ── AI推進法第18条連携 ────────────────────────────────────────

def get_regulatory_reportable_incidents(organization_id: str) -> list[Incident]:
    """規制当局報告が必要なインシデントを取得.

    AI推進法第18条のインシデント報告義務に基づく。

    Args:
        organization_id: 組織ID

    Returns:
        list[Incident]: 報告義務があるインシデントリスト
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(IncidentRow)
            .filter_by(
                organization_id=organization_id,
                regulatory_report_required=1,
            )
            .order_by(IncidentRow.created_at.desc())
            .all()
        )
        return [_row_to_model(r) for r in rows]


# ── Helpers ─────────────────────────────────────────────────────

def _row_to_model(row: IncidentRow) -> Incident:
    """DBの行をモデルに変換."""
    return Incident(
        id=row.id,
        organization_id=row.organization_id,
        title=row.title,
        description=row.description,
        incident_type=IncidentType(row.incident_type),
        severity=IncidentSeverity(row.severity),
        affected_system=row.affected_system,
        impact_description=row.impact_description,
        status=IncidentStatus(row.status),
        detected_by=row.detected_by,
        detected_at=row.detected_at,
        resolved_at=row.resolved_at,
        related_requirements=json.loads(row.related_requirements_json),
        regulatory_report_required=bool(row.regulatory_report_required),
        regulatory_report_sent=bool(row.regulatory_report_sent),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
