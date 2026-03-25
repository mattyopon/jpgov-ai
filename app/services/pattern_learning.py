# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""パターン学習エンジン.

集約された診断データから「この業界×この規模の企業は、このGapが最も多い」パターンを学習し、
新規診断時にパターンDBを参照してAIの改善提案を補強する。

主な機能:
- GapPatternの集計と更新
- パターンマッチングによる優先度提案
- 改善アクションの成功率計算
- 同業他社の改善実績に基づく推奨
"""

from __future__ import annotations

import json

from app.db.database import (
    GapPatternRow,
    get_db,
)
from app.models import (
    GapAnalysisResult,
    GapPattern,
    PatternLearningResult,
    PatternMatch,
)

# k-anonymity threshold (same as benchmark)
K_ANONYMITY_THRESHOLD = 5


def record_gap_patterns(
    industry: str,
    size_bucket: str,
    gap_analysis: GapAnalysisResult,
) -> int:
    """ギャップ分析結果からパターンを記録・更新.

    Args:
        industry: 業界
        size_bucket: 企業規模
        gap_analysis: ギャップ分析結果

    Returns:
        int: 更新されたパターン数
    """
    db = get_db()
    updated = 0

    with db.get_session() as session:
        for gap in gap_analysis.gaps:
            if gap.status.value == "compliant":
                continue

            existing = (
                session.query(GapPatternRow)
                .filter_by(
                    industry=industry,
                    size_bucket=size_bucket,
                    requirement_id=gap.req_id,
                )
                .first()
            )

            if existing:
                existing.occurrence_count = (existing.occurrence_count or 0) + 1
                # Merge actions
                current_actions = json.loads(existing.typical_actions_json or "[]")
                for action in gap.improvement_actions:
                    if action and action not in current_actions:
                        current_actions.append(action)
                existing.typical_actions_json = json.dumps(
                    current_actions[:10], ensure_ascii=False
                )
            else:
                row = GapPatternRow(
                    industry=industry,
                    size_bucket=size_bucket,
                    requirement_id=gap.req_id,
                    occurrence_count=1,
                    resolved_count=0,
                    typical_actions_json=json.dumps(
                        gap.improvement_actions[:10], ensure_ascii=False
                    ),
                    avg_resolution_days=0.0,
                )
                session.add(row)

            updated += 1

        session.commit()

    return updated


def mark_gap_resolved(
    industry: str,
    size_bucket: str,
    requirement_id: str,
    resolution_days: float = 0.0,
) -> bool:
    """Gapの解決を記録.

    Args:
        industry: 業界
        size_bucket: 企業規模
        requirement_id: 要件ID
        resolution_days: 解決にかかった日数

    Returns:
        bool: 更新成功か
    """
    db = get_db()
    with db.get_session() as session:
        row = (
            session.query(GapPatternRow)
            .filter_by(
                industry=industry,
                size_bucket=size_bucket,
                requirement_id=requirement_id,
            )
            .first()
        )
        if row is None:
            return False

        row.resolved_count = (row.resolved_count or 0) + 1

        # Update rolling average of resolution days
        if resolution_days > 0:
            old_avg = row.avg_resolution_days or 0.0
            old_count = max(row.resolved_count - 1, 0)
            if old_count > 0:
                row.avg_resolution_days = round(
                    (old_avg * old_count + resolution_days) / row.resolved_count, 1
                )
            else:
                row.avg_resolution_days = round(resolution_days, 1)

        session.commit()

    return True


def get_patterns(
    industry: str,
    size_bucket: str = "",
) -> list[GapPattern]:
    """業界×規模のGapパターン一覧を取得.

    k-anonymity (k>=5) を保証.

    Args:
        industry: 業界
        size_bucket: 企業規模（省略時は全規模）

    Returns:
        list[GapPattern]: パターン一覧
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(GapPatternRow).filter_by(industry=industry)
        if size_bucket:
            query = query.filter_by(size_bucket=size_bucket)

        rows = query.order_by(GapPatternRow.occurrence_count.desc()).all()

    # k-anonymity: パターンの出現回数がk未満なら除外
    results = []
    for row in rows:
        if (row.occurrence_count or 0) < K_ANONYMITY_THRESHOLD:
            continue

        occurrence = row.occurrence_count or 0
        resolved = row.resolved_count or 0
        resolution_rate = round(resolved / occurrence, 2) if occurrence > 0 else 0.0

        results.append(GapPattern(
            id=row.id,
            industry=row.industry,
            size_bucket=row.size_bucket or "",
            requirement_id=row.requirement_id,
            occurrence_count=occurrence,
            resolved_count=resolved,
            resolution_rate=resolution_rate,
            typical_actions=json.loads(row.typical_actions_json or "[]"),
            avg_resolution_days=row.avg_resolution_days or 0.0,
            updated_at=row.updated_at or "",
        ))

    return results


def get_pattern_matches(
    industry: str,
    size_bucket: str,
    gap_analysis: GapAnalysisResult,
) -> PatternLearningResult:
    """新規診断結果に対してパターンマッチングを実行.

    「あなたと同じ業界の企業は、このGapをこう解決した」という推奨を生成。

    Args:
        industry: 業界
        size_bucket: 企業規模
        gap_analysis: ギャップ分析結果

    Returns:
        PatternLearningResult: パターンマッチング結果
    """
    patterns = get_patterns(industry, size_bucket)
    if not patterns:
        # size_bucket指定で見つからなければ全規模で再検索
        patterns = get_patterns(industry)

    pattern_map = {p.requirement_id: p for p in patterns}

    matches: list[PatternMatch] = []
    for gap in gap_analysis.gaps:
        if gap.status.value == "compliant":
            continue

        pattern = pattern_map.get(gap.req_id)
        if pattern is None:
            continue

        # Priority suggestion based on occurrence frequency and resolution rate
        priority = _suggest_priority(pattern)

        matches.append(PatternMatch(
            requirement_id=gap.req_id,
            requirement_title=gap.title,
            industry=industry,
            occurrence_count=pattern.occurrence_count,
            resolution_rate=pattern.resolution_rate,
            recommended_actions=pattern.typical_actions[:5],
            avg_resolution_days=pattern.avg_resolution_days,
            priority_suggestion=priority,
        ))

    # Sort by occurrence count descending (most common gaps first)
    matches.sort(key=lambda m: m.occurrence_count, reverse=True)

    return PatternLearningResult(
        organization_id=gap_analysis.organization_id,
        industry=industry,
        size_bucket=size_bucket,
        matches=matches,
        total_patterns=len(patterns),
        message=_build_summary_message(matches, industry),
    )


def _suggest_priority(pattern: GapPattern) -> str:
    """パターンから優先度を推定.

    Args:
        pattern: Gapパターン

    Returns:
        str: "high" / "medium" / "low"
    """
    # High occurrence + low resolution rate = high priority
    if pattern.occurrence_count >= 10 and pattern.resolution_rate < 0.3:
        return "high"
    if pattern.occurrence_count >= 5 and pattern.resolution_rate < 0.5:
        return "high"
    if pattern.resolution_rate >= 0.7:
        return "low"
    return "medium"


def _build_summary_message(matches: list[PatternMatch], industry: str) -> str:
    """パターンマッチング結果のサマリーメッセージを生成.

    Args:
        matches: マッチング結果
        industry: 業界

    Returns:
        str: サマリーメッセージ
    """
    if not matches:
        return f"{industry}業界のパターンデータが十分にありません。"

    high_count = sum(1 for m in matches if m.priority_suggestion == "high")
    total = len(matches)

    msg = f"{industry}業界の同規模企業{total}件のパターンに一致しました。"
    if high_count > 0:
        msg += f" うち{high_count}件は優先的に対応すべきGapです。"

    return msg
