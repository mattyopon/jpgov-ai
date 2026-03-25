# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""時系列追跡サービス.

AssessmentSnapshotの保存と、成熟度推移データの生成を提供する。
"""

from __future__ import annotations

import json
from datetime import datetime

from app.db.database import AssessmentSnapshotRow, get_db
from app.models import (
    AssessmentResult,
    AssessmentSnapshot,
    TimelineEntry,
    TimelineResponse,
)


def save_snapshot(
    organization_id: str,
    assessment: AssessmentResult,
) -> AssessmentSnapshot:
    """診断結果のスナップショットを保存.

    Args:
        organization_id: 組織ID
        assessment: 診断結果

    Returns:
        AssessmentSnapshot: 保存されたスナップショット
    """
    cat_scores = {
        cs.category_id: cs.score for cs in assessment.category_scores
    }

    snapshot = AssessmentSnapshot(
        organization_id=organization_id,
        assessment_id=assessment.id,
        overall_score=assessment.overall_score,
        maturity_level=assessment.maturity_level,
        category_scores=cat_scores,
    )

    db = get_db()
    with db.get_session() as session:
        row = AssessmentSnapshotRow(
            id=snapshot.id,
            organization_id=snapshot.organization_id,
            assessment_id=snapshot.assessment_id,
            overall_score=snapshot.overall_score,
            maturity_level=snapshot.maturity_level,
            category_scores_json=json.dumps(snapshot.category_scores),
            created_at=snapshot.created_at,
        )
        session.add(row)
        session.commit()

    return snapshot


def get_timeline(organization_id: str) -> TimelineResponse:
    """組織の成熟度推移データを取得.

    Args:
        organization_id: 組織ID

    Returns:
        TimelineResponse: 時系列データ
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(AssessmentSnapshotRow)
            .filter_by(organization_id=organization_id)
            .order_by(AssessmentSnapshotRow.created_at)
            .all()
        )

    entries: list[TimelineEntry] = []
    prev_score = 0.0

    for i, row in enumerate(rows):
        cat_scores = json.loads(row.category_scores_json)
        delta = round(row.overall_score - prev_score, 2) if i > 0 else 0.0

        entries.append(TimelineEntry(
            assessment_id=row.assessment_id,
            timestamp=row.created_at,
            overall_score=row.overall_score,
            maturity_level=row.maturity_level,
            category_scores=cat_scores,
            delta_from_previous=delta,
        ))
        prev_score = row.overall_score

    # Trend calculation
    trend = _calculate_trend(entries)

    # Predict level 3 date
    predicted = _predict_level3_date(entries)

    return TimelineResponse(
        organization_id=organization_id,
        entries=entries,
        trend=trend,
        predicted_level3_date=predicted,
    )


def _calculate_trend(entries: list[TimelineEntry]) -> str:
    """トレンドを計算.

    Args:
        entries: 時系列エントリのリスト

    Returns:
        str: "improving" / "stable" / "declining"
    """
    if len(entries) < 2:
        return "stable"

    # 直近3エントリのdeltaの平均で判定
    recent = entries[-3:] if len(entries) >= 3 else entries
    deltas = [e.delta_from_previous for e in recent if e.delta_from_previous != 0.0]

    if not deltas:
        return "stable"

    avg_delta = sum(deltas) / len(deltas)

    if avg_delta > 0.1:
        return "improving"
    elif avg_delta < -0.1:
        return "declining"
    return "stable"


def _predict_level3_date(entries: list[TimelineEntry]) -> str:
    """Level 3到達予測日を計算.

    Args:
        entries: 時系列エントリのリスト

    Returns:
        str: 予測日のISO文字列、または空文字列
    """
    if len(entries) < 2:
        return ""

    latest = entries[-1]
    if latest.overall_score >= 2.4:  # Already level 3+
        return ""

    # 改善速度を計算（最新2エントリから）
    first = entries[0]
    last = entries[-1]

    try:
        first_dt = datetime.fromisoformat(first.timestamp.replace("Z", "+00:00"))
        last_dt = datetime.fromisoformat(last.timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return ""

    days_elapsed = (last_dt - first_dt).days
    if days_elapsed <= 0:
        return ""

    score_gain = last.overall_score - first.overall_score
    if score_gain <= 0:
        return ""

    # Level 3 = score 2.4
    remaining = 2.4 - last.overall_score
    rate_per_day = score_gain / days_elapsed
    days_needed = int(remaining / rate_per_day)

    from datetime import timedelta
    predicted_date = last_dt + timedelta(days=days_needed)
    return predicted_date.strftime("%Y-%m-%d")


def get_latest_snapshot(
    organization_id: str,
) -> AssessmentSnapshot | None:
    """直近のスナップショットを取得.

    Args:
        organization_id: 組織ID

    Returns:
        AssessmentSnapshot | None: 直近のスナップショット
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(AssessmentSnapshotRow)
            .filter_by(organization_id=organization_id)
            .order_by(AssessmentSnapshotRow.created_at.desc())
            .first()
        )
        if row is None:
            return None

        return AssessmentSnapshot(
            id=row.id,
            organization_id=row.organization_id,
            assessment_id=row.assessment_id,
            overall_score=row.overall_score,
            maturity_level=row.maturity_level,
            category_scores=json.loads(row.category_scores_json),
            created_at=row.created_at,
        )
