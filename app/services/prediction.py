# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""予測分析サービス.

時系列データから将来のスコアを予測する。

主な機能:
- 線形回帰ベースのスコア予測（次回レビュー時の予測スコア）
- 「このペースならLevel 3達成は○ヶ月後」
- 規制変更の影響を加味した予測
- 目標スコアに到達するために必要なアクション数の推定
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.db.database import (
    ActionEffectRow,
    AssessmentSnapshotRow,
    RegulatoryUpdateRow,
    get_db,
)
from app.models import ScorePrediction

# Level 3 threshold score
LEVEL_3_SCORE = 2.4


def predict_score(
    organization_id: str,
    target_date: str = "",
    target_score: float = LEVEL_3_SCORE,
) -> ScorePrediction:
    """将来のスコアを予測.

    線形回帰ベースで、過去の改善トレンドから未来を推定する。

    Args:
        organization_id: 組織ID
        target_date: 予測対象日（ISO形式、省略時は90日後）
        target_score: 目標スコア（デフォルト=Level 3の2.4）

    Returns:
        ScorePrediction: 予測結果
    """
    snapshots = _get_snapshots(organization_id)

    if not snapshots:
        return ScorePrediction(
            organization_id=organization_id,
            current_score=0.0,
            predicted_score=0.0,
            target_score=target_score,
            trend="stable",
            confidence="low",
            monthly_rate=0.0,
        )

    current_score = snapshots[-1]["score"]
    current_dt = _parse_dt(snapshots[-1]["timestamp"])

    # Parse target date
    if target_date:
        try:
            pred_dt = _parse_dt(target_date)
        except (ValueError, TypeError):
            pred_dt = current_dt + timedelta(days=90)
    else:
        pred_dt = current_dt + timedelta(days=90)

    # Calculate trend using linear regression
    slope, confidence = _linear_regression(snapshots)

    # Monthly rate (slope is per day)
    monthly_rate = round(slope * 30, 4)

    # Trend determination
    if monthly_rate > 0.05:
        trend = "improving"
    elif monthly_rate < -0.05:
        trend = "declining"
    else:
        trend = "stable"

    # Predict score at target date
    days_ahead = max((pred_dt - current_dt).days, 0)
    predicted_raw = current_score + slope * days_ahead
    predicted_score = round(min(max(predicted_raw, 0.0), 4.0), 2)

    # Days to target score
    days_to_target = 0
    if current_score < target_score and slope > 0:
        remaining = target_score - current_score
        days_to_target = int(remaining / slope)
    elif current_score >= target_score:
        days_to_target = 0  # Already achieved

    # Days to Level 3
    days_to_level3 = 0
    if current_score < LEVEL_3_SCORE and slope > 0:
        remaining_l3 = LEVEL_3_SCORE - current_score
        days_to_level3 = int(remaining_l3 / slope)
    elif current_score >= LEVEL_3_SCORE:
        days_to_level3 = 0

    # Required actions estimation
    avg_action_impact = _get_avg_action_impact(organization_id)
    required_actions = 0
    if avg_action_impact > 0 and current_score < target_score:
        remaining_score = target_score - current_score
        required_actions = max(1, int(remaining_score / avg_action_impact + 0.5))

    # Regulatory impact adjustment
    reg_adjustment = _get_regulatory_adjustment(organization_id)

    # Category-level predictions
    cat_predictions = _predict_categories(snapshots, days_ahead)

    prediction_date = pred_dt.strftime("%Y-%m-%d")

    return ScorePrediction(
        organization_id=organization_id,
        current_score=current_score,
        predicted_score=predicted_score,
        prediction_date=prediction_date,
        days_to_level3=days_to_level3,
        days_to_target=days_to_target,
        target_score=target_score,
        trend=trend,
        confidence=confidence,
        monthly_rate=monthly_rate,
        required_actions=required_actions,
        regulatory_impact_adjustment=reg_adjustment,
        category_predictions=cat_predictions,
    )


def _get_snapshots(organization_id: str) -> list[dict]:
    """スナップショット一覧を取得.

    Args:
        organization_id: 組織ID

    Returns:
        list[dict]: スナップショットデータ
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(AssessmentSnapshotRow)
            .filter_by(organization_id=organization_id)
            .order_by(AssessmentSnapshotRow.created_at)
            .all()
        )

    return [
        {
            "score": row.overall_score,
            "timestamp": row.created_at,
            "category_scores": json.loads(row.category_scores_json or "{}"),
        }
        for row in rows
    ]


def _parse_dt(ts: str) -> datetime:
    """タイムスタンプをパース.

    常にtimezone-awareなdatetimeを返す。

    Args:
        ts: ISO形式のタイムスタンプ or YYYY-MM-DD

    Returns:
        datetime (timezone-aware)
    """
    if not ts:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        # Try simple date format
        try:
            return datetime.strptime(ts, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)


def _linear_regression(
    snapshots: list[dict],
) -> tuple[float, str]:
    """線形回帰でスコアのトレンドを計算.

    Args:
        snapshots: スナップショットデータ

    Returns:
        tuple[float, str]: (日次変化率, 信頼度)
    """
    if len(snapshots) < 2:
        return (0.0, "low")

    # Convert to (days_from_first, score) pairs
    first_dt = _parse_dt(snapshots[0]["timestamp"])
    points: list[tuple[float, float]] = []

    for snap in snapshots:
        dt = _parse_dt(snap["timestamp"])
        days = (dt - first_dt).total_seconds() / 86400.0
        points.append((days, snap["score"]))

    # Simple least squares
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)

    denominator = n * sum_x2 - sum_x ** 2
    if abs(denominator) < 1e-10:
        return (0.0, "low")

    slope = (n * sum_xy - sum_x * sum_y) / denominator

    # Confidence based on sample size and R-squared
    mean_y = sum_y / n
    ss_tot = sum((p[1] - mean_y) ** 2 for p in points)
    intercept = (sum_y - slope * sum_x) / n
    ss_res = sum((p[1] - (intercept + slope * p[0])) ** 2 for p in points)

    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    if n >= 5 and r_squared > 0.7:
        confidence = "high"
    elif n >= 3 and r_squared > 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    return (round(slope, 6), confidence)


def _get_avg_action_impact(organization_id: str) -> float:
    """平均アクション効果を取得.

    Args:
        organization_id: 組織ID

    Returns:
        float: 平均スコア改善幅
    """
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(ActionEffectRow)
            .filter_by(organization_id=organization_id)
            .all()
        )

    if not rows:
        return 0.2  # Default estimate

    deltas = [
        (r.score_after or 0.0) - (r.score_before or 0.0)
        for r in rows
    ]
    positive_deltas = [d for d in deltas if d > 0]

    if not positive_deltas:
        return 0.2

    return round(sum(positive_deltas) / len(positive_deltas), 2)


def _get_regulatory_adjustment(organization_id: str) -> float:
    """規制変更によるスコア調整を計算.

    未対応の高重大度の規制変更があれば負の調整を返す.

    Args:
        organization_id: 組織ID

    Returns:
        float: 規制調整値（通常は0.0または負の値）
    """
    db = get_db()
    with db.get_session() as session:
        high_updates = (
            session.query(RegulatoryUpdateRow)
            .filter_by(severity="high")
            .all()
        )

    if not high_updates:
        return 0.0

    # Each high-severity update potentially reduces score
    adjustment = -0.1 * len(high_updates)
    return round(max(adjustment, -1.0), 2)


def _predict_categories(
    snapshots: list[dict],
    days_ahead: int,
) -> dict[str, float]:
    """カテゴリ別スコア予測.

    Args:
        snapshots: スナップショットデータ
        days_ahead: 予測日数

    Returns:
        dict[str, float]: カテゴリID -> 予測スコア
    """
    if len(snapshots) < 2:
        if snapshots:
            return snapshots[-1].get("category_scores", {})
        return {}

    # Collect category time series
    cat_series: dict[str, list[tuple[float, float]]] = {}
    first_dt = _parse_dt(snapshots[0]["timestamp"])

    for snap in snapshots:
        dt = _parse_dt(snap["timestamp"])
        days = (dt - first_dt).total_seconds() / 86400.0
        for cat_id, score in snap.get("category_scores", {}).items():
            if cat_id not in cat_series:
                cat_series[cat_id] = []
            cat_series[cat_id].append((days, score))

    predictions = {}
    last_day = (
        _parse_dt(snapshots[-1]["timestamp"]) - first_dt
    ).total_seconds() / 86400.0

    for cat_id, points in cat_series.items():
        if len(points) < 2:
            predictions[cat_id] = points[-1][1] if points else 0.0
            continue

        # Simple linear regression per category
        n = len(points)
        sum_x = sum(p[0] for p in points)
        sum_y = sum(p[1] for p in points)
        sum_xy = sum(p[0] * p[1] for p in points)
        sum_x2 = sum(p[0] ** 2 for p in points)

        denom = n * sum_x2 - sum_x ** 2
        if abs(denom) < 1e-10:
            predictions[cat_id] = points[-1][1]
            continue

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        target_day = last_day + days_ahead
        predicted = intercept + slope * target_day
        predictions[cat_id] = round(min(max(predicted, 0.0), 4.0), 2)

    return predictions
