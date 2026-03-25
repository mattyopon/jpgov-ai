# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""定期レビューサイクルサービス.

四半期/半期/年次のレビュースケジュール設定、
レビュー実施記録、差分レポートを提供する。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.db.database import (
    AssessmentSnapshotRow,
    ReviewCycleRow,
    ReviewRecordRow,
    get_db,
)
from app.models import (
    ReviewCycle,
    ReviewCycleCreate,
    ReviewRecord,
    ReviewRecordCreate,
)


CYCLE_DAYS = {
    "quarterly": 90,
    "semi_annual": 180,
    "annual": 365,
}


def create_review_cycle(data: ReviewCycleCreate) -> ReviewCycle:
    """レビューサイクルを作成.

    Args:
        data: サイクル作成データ

    Returns:
        ReviewCycle: 作成されたサイクル
    """
    start = data.start_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days = CYCLE_DAYS.get(data.cycle_type, 90)

    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        start_dt = datetime.now(timezone.utc)

    next_review = (start_dt + timedelta(days=days)).strftime("%Y-%m-%d")

    cycle = ReviewCycle(
        organization_id=data.organization_id,
        cycle_type=data.cycle_type,
        start_date=start,
        next_review_date=next_review,
    )

    db = get_db()
    with db.get_session() as session:
        row = ReviewCycleRow(
            id=cycle.id,
            organization_id=cycle.organization_id,
            cycle_type=cycle.cycle_type,
            start_date=cycle.start_date,
            next_review_date=cycle.next_review_date,
            created_by=cycle.created_by,
            created_at=cycle.created_at,
        )
        session.add(row)
        session.commit()

    return cycle


def get_review_cycle(cycle_id: str) -> ReviewCycle | None:
    """レビューサイクルを取得.

    Args:
        cycle_id: サイクルID

    Returns:
        ReviewCycle | None: サイクル、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = session.query(ReviewCycleRow).filter_by(id=cycle_id).first()
        if row is None:
            return None
        return ReviewCycle(
            id=row.id,
            organization_id=row.organization_id,
            cycle_type=row.cycle_type,
            start_date=row.start_date,
            next_review_date=row.next_review_date,
            created_by=row.created_by,
            created_at=row.created_at,
        )


def list_review_cycles(organization_id: str) -> list[ReviewCycle]:
    """組織のレビューサイクル一覧を取得.

    Args:
        organization_id: 組織ID

    Returns:
        list[ReviewCycle]: サイクルリスト
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(ReviewCycleRow)
            .filter_by(organization_id=organization_id)
            .all()
        )
        return [
            ReviewCycle(
                id=r.id,
                organization_id=r.organization_id,
                cycle_type=r.cycle_type,
                start_date=r.start_date,
                next_review_date=r.next_review_date,
                created_by=r.created_by,
                created_at=r.created_at,
            )
            for r in rows
        ]


def advance_next_review(cycle_id: str) -> ReviewCycle | None:
    """次回レビュー日を次のサイクルに進める.

    Args:
        cycle_id: サイクルID

    Returns:
        ReviewCycle | None: 更新されたサイクル、またはNone
    """
    db = get_db()
    with db.get_session() as session:
        row = session.query(ReviewCycleRow).filter_by(id=cycle_id).first()
        if row is None:
            return None

        days = CYCLE_DAYS.get(row.cycle_type, 90)
        try:
            current_dt = datetime.strptime(row.next_review_date, "%Y-%m-%d")
        except ValueError:
            current_dt = datetime.now(timezone.utc)

        row.next_review_date = (current_dt + timedelta(days=days)).strftime("%Y-%m-%d")
        session.commit()

        return ReviewCycle(
            id=row.id,
            organization_id=row.organization_id,
            cycle_type=row.cycle_type,
            start_date=row.start_date,
            next_review_date=row.next_review_date,
            created_by=row.created_by,
            created_at=row.created_at,
        )


def create_review_record(data: ReviewRecordCreate) -> ReviewRecord:
    """レビュー実施記録を作成.

    Args:
        data: レビュー記録データ

    Returns:
        ReviewRecord: 作成されたレビュー記録
    """
    # 差分レポートを生成
    delta_report = _build_delta_report(data.organization_id, data.assessment_id)

    record = ReviewRecord(
        organization_id=data.organization_id,
        cycle_id=data.cycle_id,
        review_date=data.review_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        assessment_id=data.assessment_id,
        reviewer=data.reviewer,
        notes=data.notes,
        delta_report=delta_report,
    )

    db = get_db()
    with db.get_session() as session:
        row = ReviewRecordRow(
            id=record.id,
            organization_id=record.organization_id,
            cycle_id=record.cycle_id,
            review_date=record.review_date,
            assessment_id=record.assessment_id,
            reviewer=record.reviewer,
            notes=record.notes,
            delta_report_json=json.dumps(record.delta_report, default=str),
            created_at=record.created_at,
        )
        session.add(row)
        session.commit()

    # 次回レビュー日を進める
    advance_next_review(data.cycle_id)

    return record


def list_review_records(organization_id: str, cycle_id: str = "") -> list[ReviewRecord]:
    """レビュー記録の一覧を取得.

    Args:
        organization_id: 組織ID
        cycle_id: サイクルID（省略時は全件）

    Returns:
        list[ReviewRecord]: レビュー記録リスト
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(ReviewRecordRow).filter_by(
            organization_id=organization_id,
        )
        if cycle_id:
            query = query.filter_by(cycle_id=cycle_id)

        rows = query.order_by(ReviewRecordRow.review_date).all()

        return [
            ReviewRecord(
                id=r.id,
                organization_id=r.organization_id,
                cycle_id=r.cycle_id,
                review_date=r.review_date,
                assessment_id=r.assessment_id,
                reviewer=r.reviewer,
                notes=r.notes,
                delta_report=json.loads(r.delta_report_json),
                created_at=r.created_at,
            )
            for r in rows
        ]


def get_upcoming_reviews(organization_id: str) -> list[dict]:
    """次回レビュー予定を取得.

    Args:
        organization_id: 組織ID

    Returns:
        list[dict]: 次回レビュー予定のリスト
    """
    cycles = list_review_cycles(organization_id)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    results = []
    for cycle in cycles:
        is_overdue = cycle.next_review_date <= today if cycle.next_review_date else False
        results.append({
            "cycle_id": cycle.id,
            "cycle_type": cycle.cycle_type,
            "next_review_date": cycle.next_review_date,
            "is_overdue": is_overdue,
        })

    # Sort by next_review_date
    results.sort(key=lambda x: x.get("next_review_date", ""))
    return results


def _build_delta_report(
    organization_id: str,
    current_assessment_id: str,
) -> dict:
    """前回→今回の差分レポートを生成.

    Args:
        organization_id: 組織ID
        current_assessment_id: 現在の診断ID

    Returns:
        dict: 差分レポート
    """
    db = get_db()
    with db.get_session() as session:
        snapshots = (
            session.query(AssessmentSnapshotRow)
            .filter_by(organization_id=organization_id)
            .order_by(AssessmentSnapshotRow.created_at.desc())
            .limit(2)
            .all()
        )

    if len(snapshots) < 2:
        return {
            "has_previous": False,
            "message": "前回のデータがありません。初回レビューです。",
        }

    current = snapshots[0]
    previous = snapshots[1]

    current_cats = json.loads(current.category_scores_json)
    previous_cats = json.loads(previous.category_scores_json)

    category_deltas = {}
    for cat_id, score in current_cats.items():
        prev_score = previous_cats.get(cat_id, 0.0)
        category_deltas[cat_id] = {
            "current": score,
            "previous": prev_score,
            "delta": round(score - prev_score, 2),
        }

    return {
        "has_previous": True,
        "previous_assessment_id": previous.assessment_id,
        "current_assessment_id": current.assessment_id,
        "overall_delta": round(
            current.overall_score - previous.overall_score, 2
        ),
        "current_score": current.overall_score,
        "previous_score": previous.overall_score,
        "category_deltas": category_deltas,
    }
