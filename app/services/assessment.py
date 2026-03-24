# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Self-Assessment診断サービス.

企業のAI利用状況に関する質問票の回答を受け取り、
AI Governance成熟度スコア（1-5段階）を算出する。
"""

from __future__ import annotations

import json
from collections import defaultdict

from app.db.database import AssessmentRow, get_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, CATEGORIES
from app.models import (
    AnswerItem,
    AssessmentResult,
    CategoryScore,
)


def _score_to_maturity(score: float) -> int:
    """スコア(0-4)を成熟度レベル(1-5)に変換."""
    if score < 0.8:
        return 1
    elif score < 1.6:
        return 2
    elif score < 2.4:
        return 3
    elif score < 3.2:
        return 4
    else:
        return 5


def run_assessment(
    organization_id: str,
    answers: list[AnswerItem],
) -> AssessmentResult:
    """質問票の回答を元に成熟度診断を実行.

    Args:
        organization_id: 組織ID
        answers: 各質問への回答リスト

    Returns:
        AssessmentResult: 診断結果（カテゴリ別スコア含む）
    """
    # 質問IDをキーにしたマップ
    question_map = {q.question_id: q for q in ASSESSMENT_QUESTIONS}
    answer_map = {a.question_id: a for a in answers}

    # カテゴリ別にスコアを集計
    cat_scores: dict[str, list[int]] = defaultdict(list)

    for q in ASSESSMENT_QUESTIONS:
        ans = answer_map.get(q.question_id)
        if ans is not None and 0 <= ans.selected_index < len(q.scores):
            score = q.scores[ans.selected_index]
        else:
            score = 0  # 未回答 = 0点
        cat_scores[q.category_id].append(score)

    # カテゴリ別スコアを計算
    category_results: list[CategoryScore] = []
    cat_title_map = {c.category_id: c.title for c in CATEGORIES}

    all_scores: list[float] = []
    for cat_id in sorted(cat_scores.keys()):
        scores = cat_scores[cat_id]
        avg = sum(scores) / len(scores) if scores else 0.0
        all_scores.append(avg)
        category_results.append(
            CategoryScore(
                category_id=cat_id,
                category_title=cat_title_map.get(cat_id, cat_id),
                score=round(avg, 2),
                maturity_level=_score_to_maturity(avg),
                question_count=len(scores),
            )
        )

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

    result = AssessmentResult(
        organization_id=organization_id,
        overall_score=round(overall, 2),
        maturity_level=_score_to_maturity(overall),
        category_scores=category_results,
    )

    # DB保存
    db = get_db()
    with db.get_session() as session:
        row = AssessmentRow(
            id=result.id,
            organization_id=organization_id,
            answers_json=json.dumps([a.model_dump() for a in answers]),
            overall_score=result.overall_score,
            maturity_level=result.maturity_level,
            category_scores_json=json.dumps(
                [cs.model_dump() for cs in category_results]
            ),
        )
        session.add(row)
        session.commit()

    return result


def get_assessment(assessment_id: str) -> AssessmentResult | None:
    """IDから診断結果を取得."""
    db = get_db()
    with db.get_session() as session:
        row = session.query(AssessmentRow).filter_by(id=assessment_id).first()
        if row is None:
            return None
        cat_scores = [
            CategoryScore(**cs) for cs in json.loads(row.category_scores_json)
        ]
        return AssessmentResult(
            id=row.id,
            organization_id=row.organization_id,
            overall_score=row.overall_score,
            maturity_level=row.maturity_level,
            category_scores=cat_scores,
            timestamp=row.created_at,
        )
