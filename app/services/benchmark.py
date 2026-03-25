# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""業界ベンチマークサービス.

匿名化された診断データの集約、業界別×企業規模別の平均スコア算出、
パーセンタイル計算、k-anonymity (k>=5) を保証する。
"""

from __future__ import annotations

import json

from app.db.database import BenchmarkDataRow, get_db
from app.models import (
    AssessmentResult,
    CategoryBenchmark,
    IndustryBenchmark,
    MyBenchmarkPosition,
)

# k-anonymity threshold
K_ANONYMITY_THRESHOLD = 5


def submit_benchmark_data(
    organization_id: str,
    industry: str,
    size_bucket: str,
    assessment: AssessmentResult,
    opt_in: bool = True,
) -> bool:
    """ベンチマーク用の匿名データを登録.

    Args:
        organization_id: 組織ID
        industry: 業界
        size_bucket: 企業規模
        assessment: 診断結果
        opt_in: オプトインフラグ

    Returns:
        bool: 登録成功かどうか
    """
    cat_scores = {cs.category_id: cs.score for cs in assessment.category_scores}

    db = get_db()
    with db.get_session() as session:
        # 既存データがあれば更新、なければ新規作成
        existing = (
            session.query(BenchmarkDataRow)
            .filter_by(organization_id=organization_id)
            .first()
        )

        if existing:
            existing.industry = industry
            existing.size_bucket = size_bucket
            existing.overall_score = assessment.overall_score
            existing.maturity_level = assessment.maturity_level
            existing.category_scores_json = json.dumps(cat_scores)
            existing.opt_in = 1 if opt_in else 0
        else:
            row = BenchmarkDataRow(
                organization_id=organization_id,
                industry=industry,
                size_bucket=size_bucket,
                overall_score=assessment.overall_score,
                maturity_level=assessment.maturity_level,
                category_scores_json=json.dumps(cat_scores),
                opt_in=1 if opt_in else 0,
            )
            session.add(row)

        session.commit()

    return True


def get_industry_benchmark(
    industry: str,
    size_bucket: str = "",
) -> IndustryBenchmark | None:
    """業界ベンチマークを取得.

    k-anonymity (k>=5) を保証: 5社未満のセグメントはデータを出さない。

    Args:
        industry: 業界
        size_bucket: 企業規模（省略時は業界全体）

    Returns:
        IndustryBenchmark | None: ベンチマーク、またはNone（k未満の場合）
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(BenchmarkDataRow).filter_by(
            industry=industry, opt_in=1
        )
        if size_bucket:
            query = query.filter_by(size_bucket=size_bucket)

        rows = query.all()

    if len(rows) < K_ANONYMITY_THRESHOLD:
        return None  # k-anonymity violation

    scores = [r.overall_score for r in rows]
    maturity_levels = [r.maturity_level for r in rows]

    avg_score = round(sum(scores) / len(scores), 2)
    avg_maturity = round(sum(maturity_levels) / len(maturity_levels), 1)

    # Category benchmarks
    cat_benchmarks = _aggregate_category_benchmarks(rows)

    # Percentile thresholds
    percentiles = _calculate_percentiles(scores)

    # Top improvement areas
    top_areas = _find_top_improvement_areas(rows)

    return IndustryBenchmark(
        industry=industry,
        size_bucket=size_bucket or "all",
        sample_count=len(rows),
        avg_overall_score=avg_score,
        avg_maturity_level=avg_maturity,
        category_benchmarks=cat_benchmarks,
        percentile_thresholds=percentiles,
        top_improvement_areas=top_areas,
    )


def get_my_position(
    organization_id: str,
    industry: str,
    my_score: float,
) -> MyBenchmarkPosition | None:
    """自社の業界内ポジションを取得.

    Args:
        organization_id: 組織ID
        industry: 業界
        my_score: 自社スコア

    Returns:
        MyBenchmarkPosition | None: ポジション情報、またはNone
    """
    benchmark = get_industry_benchmark(industry)
    if benchmark is None:
        return None

    # Calculate percentile
    db = get_db()
    with db.get_session() as session:
        rows = (
            session.query(BenchmarkDataRow)
            .filter_by(industry=industry, opt_in=1)
            .all()
        )

    scores = sorted([r.overall_score for r in rows])
    if not scores:
        return None

    # Count how many scores are below my_score
    below = sum(1 for s in scores if s < my_score)
    percentile = round((below / len(scores)) * 100, 1)

    # Gap areas: categories where my score is most below industry average
    my_data = None
    with db.get_session() as session:
        my_data = (
            session.query(BenchmarkDataRow)
            .filter_by(organization_id=organization_id)
            .first()
        )

    gap_areas = []
    if my_data and benchmark.category_benchmarks:
        my_cats = json.loads(my_data.category_scores_json)
        for cat_id, cat_bench in benchmark.category_benchmarks.items():
            my_cat_score = my_cats.get(cat_id, 0.0)
            gap = round(my_cat_score - cat_bench.avg_score, 2)
            if gap < 0:
                gap_areas.append({
                    "category_id": cat_id,
                    "my_score": my_cat_score,
                    "industry_avg": cat_bench.avg_score,
                    "gap": gap,
                })
        gap_areas.sort(key=lambda x: x["gap"])

    return MyBenchmarkPosition(
        organization_id=organization_id,
        industry=industry,
        my_score=my_score,
        industry_avg=benchmark.avg_overall_score,
        percentile=percentile,
        gap_areas=gap_areas[:5],  # Top 5 gap areas
    )


def _aggregate_category_benchmarks(
    rows: list[BenchmarkDataRow],
) -> dict[str, CategoryBenchmark]:
    """カテゴリ別ベンチマークを集計.

    Args:
        rows: ベンチマークデータ行のリスト

    Returns:
        dict: カテゴリID -> CategoryBenchmark
    """
    cat_totals: dict[str, list[float]] = {}

    for row in rows:
        cats = json.loads(row.category_scores_json)
        for cat_id, score in cats.items():
            if cat_id not in cat_totals:
                cat_totals[cat_id] = []
            cat_totals[cat_id].append(score)

    result = {}
    for cat_id, scores in cat_totals.items():
        if len(scores) >= K_ANONYMITY_THRESHOLD:
            result[cat_id] = CategoryBenchmark(
                category_id=cat_id,
                avg_score=round(sum(scores) / len(scores), 2),
                sample_count=len(scores),
            )

    return result


def _calculate_percentiles(scores: list[float]) -> dict[str, float]:
    """パーセンタイル閾値を計算.

    Args:
        scores: スコアのリスト

    Returns:
        dict: パーセンタイル -> スコア値
    """
    if not scores:
        return {}

    sorted_scores = sorted(scores)
    n = len(sorted_scores)

    result = {}
    for p in [25, 50, 75, 90]:
        idx = int(n * p / 100)
        if idx >= n:
            idx = n - 1
        result[str(p)] = round(sorted_scores[idx], 2)

    return result


def _find_top_improvement_areas(
    rows: list[BenchmarkDataRow],
) -> list[str]:
    """最も改善が多い領域を特定.

    Args:
        rows: ベンチマークデータ行のリスト

    Returns:
        list[str]: 改善が多いカテゴリIDのリスト
    """
    cat_scores: dict[str, list[float]] = {}

    for row in rows:
        cats = json.loads(row.category_scores_json)
        for cat_id, score in cats.items():
            if cat_id not in cat_scores:
                cat_scores[cat_id] = []
            cat_scores[cat_id].append(score)

    # Average score per category, sorted ascending (lowest = most room for improvement)
    cat_avgs = []
    for cat_id, scores in cat_scores.items():
        if scores:
            cat_avgs.append((cat_id, sum(scores) / len(scores)))

    cat_avgs.sort(key=lambda x: x[1])

    return [cat_id for cat_id, _ in cat_avgs[:5]]
