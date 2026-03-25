# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

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


def run_gap_analysis_sync(
    assessment: "AssessmentResult",
) -> GapAnalysisResult:
    """run_gap_analysisの同期版ラッパー. Streamlit等の同期コンテキストから呼ぶ."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Streamlit等で既にイベントループが動いている場合
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, run_gap_analysis(assessment)).result()
        return loop.run_until_complete(run_gap_analysis(assessment))
    except RuntimeError:
        return asyncio.run(run_gap_analysis(assessment))


def get_gap_analysis(gap_id: str) -> GapAnalysisResult | None:
    """IDからギャップ分析結果を取得."""
    db = get_db()
    with db.get_session() as session:
        row = session.query(GapAnalysisRow).filter_by(id=gap_id).first()
        if row is None:
            return None
        return GapAnalysisResult.model_validate_json(row.result_json)


# ---------------------------------------------------------------------------
# マルチフレームワーク ギャップ分析
# ---------------------------------------------------------------------------

def _framework_priority(framework: str) -> int:
    """フレームワークの優先度を返す（値が小さいほど高優先）.

    法的義務（EU AI Act / AI推進法 mandatory）> 認証要件（ISO 42001）
    > ガイドライン（METI）> 推奨（NIST）
    """
    priorities = {
        "eu_ai_act": 1,
        "ai_promotion_act_mandatory": 2,
        "iso42001": 3,
        "meti": 4,
        "ai_promotion_act_effort": 5,
        "nist": 6,
        "industry": 7,
    }
    return priorities.get(framework, 99)


def run_multi_framework_gap_analysis(
    gap_result: GapAnalysisResult,
    *,
    industry: str = "",
    include_nist: bool = True,
    include_eu: bool = True,
    include_industry: bool = True,
) -> list[dict]:
    """マルチフレームワーク対応のギャップ分析を実行.

    METIギャップ分析結果を基に、各Gapに「どのフレームワークの何条に
    違反しているか」を明示する。

    優先順位ロジック:
    法的義務（EU AI Act）> 認証要件（ISO 42001）> ガイドライン（METI）> 推奨（NIST）

    Args:
        gap_result: METIギャップ分析結果
        industry: 業種（"financial", "healthcare", "automotive", "hr"）
        include_nist: NIST AI RMFを含めるか
        include_eu: EU AI Actを含めるか
        include_industry: 業種別ガイドラインを含めるか

    Returns:
        各ギャップに対するマルチフレームワーク分析結果のリスト
    """
    from app.guidelines.cross_mapping import get_frameworks_for_meti_requirement
    from app.guidelines.industry_specific import get_industry_to_meti_mapping

    results: list[dict] = []

    # 業種別マッピングの逆引き（METI → 業種別要件）
    industry_reverse_map: dict[str, list[str]] = {}
    if include_industry and industry:
        industry_mapping = get_industry_to_meti_mapping(industry)
        for ind_id, meti_ids in industry_mapping.items():
            for mid in meti_ids:
                industry_reverse_map.setdefault(mid, []).append(ind_id)

    for gap in gap_result.gaps:
        if gap.status == ComplianceStatus.COMPLIANT:
            continue

        frameworks = get_frameworks_for_meti_requirement(gap.req_id)

        violations: list[dict] = []

        # METI
        violations.append({
            "framework": "meti",
            "framework_name": "METI AI事業者ガイドライン",
            "requirement_ids": [gap.req_id],
            "priority": _framework_priority("meti"),
        })

        # ISO 42001
        if frameworks["iso"]:
            violations.append({
                "framework": "iso42001",
                "framework_name": "ISO/IEC 42001:2023",
                "requirement_ids": frameworks["iso"],
                "priority": _framework_priority("iso42001"),
            })

        # NIST AI RMF
        if include_nist and frameworks["nist"]:
            violations.append({
                "framework": "nist",
                "framework_name": "NIST AI RMF 1.0",
                "requirement_ids": frameworks["nist"],
                "priority": _framework_priority("nist"),
            })

        # EU AI Act
        if include_eu and frameworks["eu_articles"]:
            violations.append({
                "framework": "eu_ai_act",
                "framework_name": "EU AI Act",
                "requirement_ids": frameworks["eu_articles"],
                "priority": _framework_priority("eu_ai_act"),
            })

        # AI推進法
        if frameworks["act"]:
            violations.append({
                "framework": "ai_promotion_act",
                "framework_name": "AI推進法",
                "requirement_ids": frameworks["act"],
                "priority": _framework_priority("ai_promotion_act_mandatory"),
            })

        # 業種別
        if include_industry and gap.req_id in industry_reverse_map:
            violations.append({
                "framework": "industry",
                "framework_name": f"業種別ガイドライン（{industry}）",
                "requirement_ids": industry_reverse_map[gap.req_id],
                "priority": _framework_priority("industry"),
            })

        # 優先順位でソート
        violations.sort(key=lambda v: v["priority"])

        # 最高優先度のフレームワークを取得
        highest_priority_framework = violations[0]["framework_name"] if violations else "METI"

        results.append({
            "req_id": gap.req_id,
            "title": gap.title,
            "status": gap.status.value,
            "current_score": gap.current_score,
            "priority": gap.priority,
            "highest_priority_framework": highest_priority_framework,
            "violations": violations,
            "improvement_actions": gap.improvement_actions,
        })

    # 全体を最高優先度フレームワークでソート（法的義務が上に来る）
    results.sort(key=lambda r: min(v["priority"] for v in r["violations"]) if r["violations"] else 99)

    return results
