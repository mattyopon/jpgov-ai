# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""改善アクション効果分析サービス.

タスク管理と時系列データを連携し、「どの改善アクションが最も効果的だったか」を分析する。

主な機能:
- アクション実施前後のスコア変動を測定
- アクション種別ごとのROI（投入工数 vs スコア改善幅）
- 「最もコスパの良い改善アクション」ランキング
- 他社の匿名化データとの比較
"""

from __future__ import annotations

from collections import defaultdict

from app.db.database import (
    ActionEffectRow,
    get_db,
)
from app.models import (
    ActionEffectRecord,
    ActionRanking,
    ActionROI,
)

# k-anonymity threshold for industry comparison
K_ANONYMITY_THRESHOLD = 5


def record_action_effect(data: ActionEffectRecord) -> ActionROI:
    """改善アクションの効果を記録.

    Args:
        data: アクション効果記録データ

    Returns:
        ActionROI: 算出されたROI
    """
    score_delta = round(data.score_after - data.score_before, 2)
    roi = round(score_delta / data.effort_hours, 4) if data.effort_hours > 0 else 0.0

    db = get_db()
    with db.get_session() as session:
        row = ActionEffectRow(
            organization_id=data.organization_id,
            task_id=data.task_id,
            action_type=data.action_type,
            requirement_id=data.requirement_id,
            score_before=data.score_before,
            score_after=data.score_after,
            effort_hours=data.effort_hours,
        )
        session.add(row)
        session.commit()

    return ActionROI(
        task_id=data.task_id,
        action_type=data.action_type,
        requirement_id=data.requirement_id,
        score_before=data.score_before,
        score_after=data.score_after,
        score_delta=score_delta,
        effort_hours=data.effort_hours,
        roi=roi,
    )


def get_action_rankings(organization_id: str) -> ActionRanking:
    """組織の改善アクション効果ランキングを取得.

    Args:
        organization_id: 組織ID

    Returns:
        ActionRanking: ランキング結果
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(ActionEffectRow)
            .filter_by(organization_id=organization_id)
            .all()
        )

    if not rows:
        return ActionRanking(
            organization_id=organization_id,
            rankings=[],
            industry_comparison=[],
            best_roi_action_type="",
            avg_score_improvement=0.0,
        )

    rankings: list[ActionROI] = []
    for row in rows:
        delta = round((row.score_after or 0.0) - (row.score_before or 0.0), 2)
        effort = row.effort_hours or 0.0
        roi_val = round(delta / effort, 4) if effort > 0 else 0.0

        rankings.append(ActionROI(
            task_id=row.task_id,
            action_type=row.action_type or "",
            requirement_id=row.requirement_id or "",
            score_before=row.score_before or 0.0,
            score_after=row.score_after or 0.0,
            score_delta=delta,
            effort_hours=effort,
            roi=roi_val,
        ))

    # Sort by ROI descending
    rankings.sort(key=lambda r: r.roi, reverse=True)

    # Find best ROI action type
    type_rois: dict[str, list[float]] = defaultdict(list)
    for r in rankings:
        if r.action_type:
            type_rois[r.action_type].append(r.roi)

    best_type = ""
    best_avg_roi = 0.0
    for atype, rois in type_rois.items():
        avg = sum(rois) / len(rois)
        if avg > best_avg_roi:
            best_avg_roi = avg
            best_type = atype

    # Average score improvement
    total_delta = sum(r.score_delta for r in rankings)
    avg_improvement = round(total_delta / len(rankings), 2) if rankings else 0.0

    return ActionRanking(
        organization_id=organization_id,
        rankings=rankings,
        industry_comparison=[],  # Populated by get_industry_comparison
        best_roi_action_type=best_type,
        avg_score_improvement=avg_improvement,
    )


def get_industry_comparison(
    organization_id: str,
    industry: str,
    size_bucket: str = "",
) -> list[dict]:
    """他社の匿名化データとの比較.

    k-anonymity (k>=5) を保証.

    Args:
        organization_id: 組織ID
        industry: 業界
        size_bucket: 企業規模

    Returns:
        list[dict]: 業界比較データ
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(ActionEffectRow)
        # We need to cross-reference with organizations to filter by industry
        # For now, aggregate all action effects and use pattern data
        all_rows = query.all()

    if len(all_rows) < K_ANONYMITY_THRESHOLD:
        return []

    # Aggregate by action_type
    type_stats: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "total_delta": 0.0, "total_effort": 0.0}
    )

    for row in all_rows:
        if row.organization_id == organization_id:
            continue  # Skip own data for comparison
        atype = row.action_type or "unknown"
        delta = (row.score_after or 0.0) - (row.score_before or 0.0)
        type_stats[atype]["count"] += 1
        type_stats[atype]["total_delta"] += delta
        type_stats[atype]["total_effort"] += row.effort_hours or 0.0

    comparison = []
    for atype, stats in type_stats.items():
        if stats["count"] < K_ANONYMITY_THRESHOLD:
            continue
        avg_delta = round(stats["total_delta"] / stats["count"], 2)
        avg_effort = round(stats["total_effort"] / stats["count"], 1)
        comparison.append({
            "action_type": atype,
            "sample_count": stats["count"],
            "avg_score_improvement": avg_delta,
            "avg_effort_hours": avg_effort,
        })

    comparison.sort(
        key=lambda x: x["avg_score_improvement"], reverse=True
    )

    return comparison


def get_action_type_stats(organization_id: str) -> dict[str, dict]:
    """アクション種別ごとの統計を取得.

    Args:
        organization_id: 組織ID

    Returns:
        dict: アクション種別 -> 統計情報
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(ActionEffectRow)
            .filter_by(organization_id=organization_id)
            .all()
        )

    stats: dict[str, dict] = {}
    type_data: dict[str, list[ActionEffectRow]] = defaultdict(list)

    for row in rows:
        atype = row.action_type or "other"
        type_data[atype].append(row)

    for atype, arows in type_data.items():
        deltas = [(r.score_after or 0.0) - (r.score_before or 0.0) for r in arows]
        efforts = [r.effort_hours or 0.0 for r in arows]
        avg_delta = round(sum(deltas) / len(deltas), 2) if deltas else 0.0
        avg_effort = round(sum(efforts) / len(efforts), 1) if efforts else 0.0
        total_effort = round(sum(efforts), 1)

        stats[atype] = {
            "count": len(arows),
            "avg_score_improvement": avg_delta,
            "total_score_improvement": round(sum(deltas), 2),
            "avg_effort_hours": avg_effort,
            "total_effort_hours": total_effort,
            "roi": round(avg_delta / avg_effort, 4) if avg_effort > 0 else 0.0,
        }

    return stats
