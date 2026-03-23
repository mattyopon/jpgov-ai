"""ギャップ分析サービス.

診断結果を元にMETI AI事業者ガイドラインの各要件に対するギャップを特定し、
AIによる改善アクション提案を生成する。
"""

from __future__ import annotations

import os
from collections import defaultdict

from app.db.database import GapAnalysisRow, get_db
from app.guidelines.meti_v1_1 import (
    ASSESSMENT_QUESTIONS,
    all_requirements,
)
from app.models import (
    AssessmentResult,
    ComplianceStatus,
    GapAnalysisResult,
    RequirementGap,
)


def _determine_status(score: float) -> ComplianceStatus:
    """スコアから充足状態を判定."""
    if score >= 3.0:
        return ComplianceStatus.COMPLIANT
    elif score >= 1.5:
        return ComplianceStatus.PARTIAL
    else:
        return ComplianceStatus.NON_COMPLIANT


def _determine_priority(status: ComplianceStatus, category_id: str) -> str:
    """優先度を判定."""
    # 安全性・セキュリティ・プライバシーは高優先
    high_priority_cats = {"C02", "C04", "C05"}
    if status == ComplianceStatus.NON_COMPLIANT:
        return "high" if category_id in high_priority_cats else "high"
    elif status == ComplianceStatus.PARTIAL:
        return "high" if category_id in high_priority_cats else "medium"
    return "low"


def _generate_default_actions(req_id: str, status: ComplianceStatus) -> list[str]:
    """AIを使わないフォールバック: 要件に基づくデフォルト改善アクション."""
    actions_map: dict[str, list[str]] = {
        "C01-R01": [
            "AIガバナンス基本方針に人間中心の原則を明記する",
            "全従業員への方針周知・研修を実施する",
        ],
        "C01-R02": [
            "高リスクAIシステムの判断に人間の最終承認プロセスを導入する",
            "Human-in-the-Loopの仕組みを設計・実装する",
        ],
        "C01-R03": [
            "AI生成コンテンツのファクトチェックプロセスを整備する",
            "誤情報検出・フィルタリングの仕組みを導入する",
        ],
        "C02-R01": [
            "AI固有のリスクアセスメントフレームワークを策定する",
            "定期的なリスク評価スケジュールを確立する",
        ],
        "C02-R02": [
            "学習データの品質基準を定義する",
            "データ品質の定期監査プロセスを導入する",
        ],
        "C02-R03": [
            "AIシステムの異常検知・安全停止手順書を作成する",
            "フォールバック手段の設計と定期的な訓練を実施する",
        ],
        "C03-R01": [
            "バイアス評価のための定量的指標を定義する",
            "定期的なバイアスオーディットを実施する",
        ],
        "C03-R02": [
            "利用文脈に応じた公平性基準を策定する",
            "公平性モニタリングダッシュボードを構築する",
        ],
        "C03-R03": [
            "バイアス検出時の是正手順と責任者を明確にする",
            "是正実施後の効果検証プロセスを整備する",
        ],
        "C04-R01": [
            "AI固有の個人情報取扱方針を策定・公表する",
            "方針の定期見直しスケジュールを設定する",
        ],
        "C04-R02": [
            "AI導入前のPIA（プライバシー影響評価）テンプレートを作成する",
            "全AIシステムでPIAを実施する",
        ],
        "C04-R03": [
            "データ最小化の原則をAIデータ設計に組み込む",
            "目的外利用を防止する技術的・組織的措置を講じる",
        ],
        "C05-R01": [
            "AI固有の脅威（敵対的攻撃等）に対するセキュリティ対策を実装する",
            "定期的なペネトレーションテストを実施する",
        ],
        "C05-R02": [
            "AIシステムの脆弱性管理プロセスを確立する",
            "脆弱性スキャンの自動化と修正追跡を行う",
        ],
        "C05-R03": [
            "AIセキュリティインシデント対応計画を策定する",
            "対応手順の定期訓練を実施する",
        ],
        "C06-R01": [
            "AIの利用を利害関係者に明示するポリシーを策定する",
            "サービス画面・ドキュメントでのAI利用表示を実装する",
        ],
        "C06-R02": [
            "AI判断の説明生成機能を設計・実装する",
            "利用者向けの判断根拠説明テンプレートを作成する",
        ],
        "C06-R03": [
            "モデルカード等の標準フォーマットで技術文書を整備する",
            "バージョン管理と変更履歴の体制を構築する",
        ],
        "C07-R01": [
            "AIガバナンス責任者を正式に任命する",
            "責任者の権限・責任を組織内文書で明確にする",
        ],
        "C07-R02": [
            "AIガバナンス方針を策定し、実施体制を整備する",
            "定期的な方針レビューと改善サイクルを確立する",
        ],
        "C07-R03": [
            "AI関連契約の標準テンプレートを作成する",
            "責任分界・品質保証条項を明確にする",
        ],
        "C07-R04": [
            "ガバナンス記録の統一管理システムを導入する",
            "改竄防止付きの監査証跡を実装する",
        ],
        "C08-R01": [
            "役割別のAI教育プログラムを設計・実施する",
            "教育効果の測定と改善サイクルを確立する",
        ],
        "C08-R02": [
            "AIシステム利用者向けガイドラインを作成する",
            "FAQとサポート体制を整備する",
        ],
        "C09-R01": [
            "AI利用における公正競争方針を策定する",
            "競争法コンプライアンスのレビュー体制を構築する",
        ],
        "C09-R02": [
            "AI学習・利用における知的財産権チェックリストを作成する",
            "知的財産権侵害リスクの評価プロセスを導入する",
        ],
        "C10-R01": [
            "AIイノベーション推進のロードマップを策定する",
            "社外連携・オープンイノベーションの機会を探索する",
        ],
        "C10-R02": [
            "相互運用性を考慮したAI技術選定基準を策定する",
            "オープン標準への準拠方針を定める",
        ],
    }
    default = [
        "当該要件の現状を詳細に調査する",
        "改善計画を策定し、責任者と期限を設定する",
    ]
    if status == ComplianceStatus.COMPLIANT:
        return ["現状維持＋定期的な見直しを継続する"]
    return actions_map.get(req_id, default)


async def generate_ai_recommendations(
    gaps: list[RequirementGap],
    organization_id: str,
) -> str:
    """Anthropic APIを使ってギャップに対するAI改善提案を生成.

    API keyがない場合はフォールバックメッセージを返す。
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-ant-xxx"):
        return _generate_fallback_recommendations(gaps)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        non_compliant = [g for g in gaps if g.status != ComplianceStatus.COMPLIANT]
        if not non_compliant:
            return "全要件が充足しています。現状のガバナンス体制を維持してください。"

        gap_summary = "\n".join(
            f"- [{g.req_id}] {g.title}: {g.status.value} (スコア: {g.current_score})"
            for g in non_compliant[:15]
        )

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "あなたはAIガバナンスの専門家です。\n"
                        "以下はある企業のMETI AI事業者ガイドライン準拠状況のギャップ分析結果です。\n\n"
                        f"## 未充足・部分充足の要件:\n{gap_summary}\n\n"
                        "## タスク:\n"
                        "1. 最も優先度の高い改善アクションを5つ挙げてください\n"
                        "2. 各アクションの具体的な実施手順を簡潔に記述してください\n"
                        "3. 想定される期間と必要リソースの目安を示してください\n\n"
                        "日本語で回答してください。"
                    ),
                }
            ],
        )
        return message.content[0].text
    except Exception:
        return _generate_fallback_recommendations(gaps)


def _generate_fallback_recommendations(gaps: list[RequirementGap]) -> str:
    """AI APIが利用不可の場合のフォールバック提案."""
    non_compliant = [g for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT]
    partial = [g for g in gaps if g.status == ComplianceStatus.PARTIAL]

    lines = ["## AI改善提案（自動生成）\n"]

    if non_compliant:
        lines.append("### 優先度: 高（未充足）")
        for g in non_compliant[:5]:
            lines.append(f"\n**{g.req_id}: {g.title}**")
            for action in g.improvement_actions:
                lines.append(f"  - {action}")

    if partial:
        lines.append("\n### 優先度: 中（部分充足）")
        for g in partial[:5]:
            lines.append(f"\n**{g.req_id}: {g.title}**")
            for action in g.improvement_actions:
                lines.append(f"  - {action}")

    lines.append("\n### 推奨ロードマップ")
    lines.append("1. **Phase 1 (1-3ヶ月)**: 高リスク要件（安全性・セキュリティ・プライバシー）の対応")
    lines.append("2. **Phase 2 (3-6ヶ月)**: ガバナンス体制・アカウンタビリティの整備")
    lines.append("3. **Phase 3 (6-12ヶ月)**: 全要件の充足と継続的改善体制の構築")

    return "\n".join(lines)


async def run_gap_analysis(
    assessment: AssessmentResult,
) -> GapAnalysisResult:
    """診断結果を元にギャップ分析を実行.

    Args:
        assessment: 診断結果

    Returns:
        GapAnalysisResult: ギャップ分析結果
    """
    # カテゴリ別スコアマップ
    cat_score_map = {cs.category_id: cs.score for cs in assessment.category_scores}

    # 質問と要件の紐づけからスコアを推定
    req_scores: dict[str, list[float]] = defaultdict(list)
    for q in ASSESSMENT_QUESTIONS:
        cat_score = cat_score_map.get(q.category_id, 0.0)
        for req_id in q.requirement_ids:
            req_scores[req_id].append(cat_score)

    # ギャップ一覧を生成
    requirements = all_requirements()
    gaps: list[RequirementGap] = []

    for req in requirements:
        scores = req_scores.get(req.req_id, [])
        avg_score = sum(scores) / len(scores) if scores else 0.0
        status = _determine_status(avg_score)
        priority = _determine_priority(status, req.category_id)
        actions = _generate_default_actions(req.req_id, status)

        gap_desc = ""
        if status == ComplianceStatus.NON_COMPLIANT:
            gap_desc = f"要件「{req.title}」が未充足です。{req.description}"
        elif status == ComplianceStatus.PARTIAL:
            gap_desc = f"要件「{req.title}」が部分的に充足されています。さらなる改善が必要です。"

        gaps.append(
            RequirementGap(
                req_id=req.req_id,
                category_id=req.category_id,
                title=req.title,
                status=status,
                current_score=round(avg_score, 2),
                gap_description=gap_desc,
                improvement_actions=actions,
                priority=priority,
            )
        )

    compliant = sum(1 for g in gaps if g.status == ComplianceStatus.COMPLIANT)
    partial = sum(1 for g in gaps if g.status == ComplianceStatus.PARTIAL)
    non_compliant = sum(1 for g in gaps if g.status == ComplianceStatus.NON_COMPLIANT)

    # AI改善提案を生成
    ai_recs = await generate_ai_recommendations(gaps, assessment.organization_id)

    result = GapAnalysisResult(
        organization_id=assessment.organization_id,
        assessment_id=assessment.id,
        total_requirements=len(gaps),
        compliant_count=compliant,
        partial_count=partial,
        non_compliant_count=non_compliant,
        gaps=gaps,
        ai_recommendations=ai_recs,
    )

    # DB保存
    db = get_db()
    with db.get_session() as session:
        row = GapAnalysisRow(
            id=result.id,
            organization_id=assessment.organization_id,
            assessment_id=assessment.id,
            result_json=result.model_dump_json(),
        )
        session.add(row)
        session.commit()

    return result


def get_gap_analysis(gap_id: str) -> GapAnalysisResult | None:
    """IDからギャップ分析結果を取得."""
    db = get_db()
    with db.get_session() as session:
        row = session.query(GapAnalysisRow).filter_by(id=gap_id).first()
        if row is None:
            return None
        return GapAnalysisResult.model_validate_json(row.result_json)
