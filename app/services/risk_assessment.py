# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""リスクアセスメントサービス（EU AI Act準拠のリスク分類）.

AIシステムのリスクレベルを分類し、リスクに応じた追加要件を提示する。
EU AI Actの分類に準拠しつつ、日本の制度にマッピングする。
"""

from __future__ import annotations


from app.db.database import get_db
from app.models import (
    RiskAssessmentItem,
    RiskAssessmentResult,
    RiskCategory,
    RiskLevel,
)


# ── リスク分類の判定基準 ──

RISK_CRITERIA: dict[str, dict] = {
    "biometric_identification": {
        "question": "リアルタイムの生体認証を行いますか？",
        "high_risk_if_yes": True,
        "category": RiskCategory.BIOMETRIC,
    },
    "critical_infrastructure": {
        "question": "重要インフラ（電力・水道・交通等）の管理に使用しますか？",
        "high_risk_if_yes": True,
        "category": RiskCategory.INFRASTRUCTURE,
    },
    "education_access": {
        "question": "教育機関の入学選考や成績評価に使用しますか？",
        "high_risk_if_yes": True,
        "category": RiskCategory.EDUCATION,
    },
    "employment": {
        "question": "採用・人事評価・解雇の判断に使用しますか？",
        "high_risk_if_yes": True,
        "category": RiskCategory.EMPLOYMENT,
    },
    "credit_scoring": {
        "question": "信用スコアリングや保険の査定に使用しますか？",
        "high_risk_if_yes": True,
        "category": RiskCategory.FINANCIAL,
    },
    "law_enforcement": {
        "question": "法執行・司法判断に使用しますか？",
        "high_risk_if_yes": True,
        "category": RiskCategory.LAW_ENFORCEMENT,
    },
    "healthcare": {
        "question": "医療診断・治療の判断支援に使用しますか？",
        "high_risk_if_yes": True,
        "category": RiskCategory.HEALTHCARE,
    },
    "emotion_recognition": {
        "question": "感情認識を行いますか？",
        "high_risk_if_yes": False,  # limited risk
        "category": RiskCategory.EMOTION,
    },
    "content_generation": {
        "question": "テキスト・画像・音声等のコンテンツを生成しますか？",
        "high_risk_if_yes": False,  # limited risk
        "category": RiskCategory.CONTENT_GENERATION,
    },
    "chatbot": {
        "question": "チャットボットやバーチャルアシスタントとして使用しますか？",
        "high_risk_if_yes": False,  # limited risk, transparency obligation
        "category": RiskCategory.CHATBOT,
    },
}


RISK_QUESTIONS: list[dict] = [
    {
        "question_id": f"RQ-{i+1:02d}",
        "key": key,
        "question": info["question"],
        "category": info["category"].value,
    }
    for i, (key, info) in enumerate(RISK_CRITERIA.items())
]


# ── 追加要件の定義 ──

HIGH_RISK_REQUIREMENTS: list[str] = [
    "リスク管理システムの確立・実施・文書化・維持",
    "学習データのガバナンス（データ品質基準、バイアス検出）",
    "技術文書の作成・維持",
    "ログの自動記録（トレーサビリティ確保）",
    "利用者への透明性確保（適切な情報提供）",
    "人間による監視の措置（Human Oversight）",
    "正確性・ロバスト性・サイバーセキュリティの確保",
    "適合性評価の実施",
    "EU AIデータベースへの登録（EU市場向け）",
    "【日本】AI推進法に基づくリスク管理体制の整備（APA-05）",
    "【日本】METI AI事業者ガイドラインの全要件遵守",
]

LIMITED_RISK_REQUIREMENTS: list[str] = [
    "AIとの対話であることの明示（透明性義務）",
    "AI生成コンテンツであることの表示",
    "ディープフェイク等の不正利用防止措置",
    "【日本】AI推進法に基づく透明性確保（APA-03）",
]

MINIMAL_RISK_REQUIREMENTS: list[str] = [
    "自主的な行動規範への準拠を推奨",
    "【日本】AI推進法の基本理念の遵守（APA-01）",
]


def get_risk_questions() -> list[dict]:
    """リスク分類用の質問一覧を返す."""
    return RISK_QUESTIONS


def classify_risk(answers: dict[str, bool]) -> RiskLevel:
    """回答に基づいてリスクレベルを分類.

    Args:
        answers: 質問キー -> True/False の辞書

    Returns:
        RiskLevel: 分類されたリスクレベル
    """
    has_high_risk = False
    has_limited_risk = False

    for key, info in RISK_CRITERIA.items():
        if answers.get(key, False):
            if info["high_risk_if_yes"]:
                has_high_risk = True
            else:
                has_limited_risk = True

    if has_high_risk:
        return RiskLevel.HIGH
    elif has_limited_risk:
        return RiskLevel.LIMITED
    else:
        return RiskLevel.MINIMAL


def _get_additional_requirements(risk_level: RiskLevel) -> list[str]:
    """リスクレベルに応じた追加要件を返す."""
    if risk_level == RiskLevel.HIGH:
        return HIGH_RISK_REQUIREMENTS
    elif risk_level == RiskLevel.LIMITED:
        return LIMITED_RISK_REQUIREMENTS
    else:
        return MINIMAL_RISK_REQUIREMENTS


def run_risk_assessment(
    organization_id: str,
    system_name: str,
    system_description: str,
    answers: dict[str, bool],
) -> RiskAssessmentResult:
    """リスクアセスメントを実行.

    Args:
        organization_id: 組織ID
        system_name: AIシステム名
        system_description: AIシステムの説明
        answers: 質問キー -> True/False

    Returns:
        RiskAssessmentResult: リスクアセスメント結果
    """
    risk_level = classify_risk(answers)
    additional_requirements = _get_additional_requirements(risk_level)

    # 個別項目の結果
    items: list[RiskAssessmentItem] = []
    for key, info in RISK_CRITERIA.items():
        answered_yes = answers.get(key, False)
        item_risk = RiskLevel.MINIMAL
        if answered_yes:
            if info["high_risk_if_yes"]:
                item_risk = RiskLevel.HIGH
            else:
                item_risk = RiskLevel.LIMITED

        items.append(
            RiskAssessmentItem(
                question_key=key,
                question=info["question"],
                answer=answered_yes,
                risk_level=item_risk,
                category=info["category"],
            )
        )

    result = RiskAssessmentResult(
        organization_id=organization_id,
        system_name=system_name,
        system_description=system_description,
        overall_risk_level=risk_level,
        items=items,
        additional_requirements=additional_requirements,
    )

    # DB保存
    db = get_db()
    with db.get_session() as session:
        from app.db.database import RiskAssessmentRow

        row = RiskAssessmentRow(
            id=result.id,
            organization_id=organization_id,
            system_name=system_name,
            result_json=result.model_dump_json(),
        )
        session.add(row)
        session.commit()

    return result


def get_risk_assessment(assessment_id: str) -> RiskAssessmentResult | None:
    """IDからリスクアセスメント結果を取得."""
    db = get_db()
    with db.get_session() as session:
        from app.db.database import RiskAssessmentRow

        row = session.query(RiskAssessmentRow).filter_by(id=assessment_id).first()
        if row is None:
            return None
        return RiskAssessmentResult.model_validate_json(row.result_json)


def list_risk_assessments(organization_id: str) -> list[RiskAssessmentResult]:
    """組織のリスクアセスメント一覧を取得."""
    db = get_db()
    with db.get_session() as session:
        from app.db.database import RiskAssessmentRow

        rows = (
            session.query(RiskAssessmentRow)
            .filter_by(organization_id=organization_id)
            .all()
        )
        return [
            RiskAssessmentResult.model_validate_json(r.result_json) for r in rows
        ]
