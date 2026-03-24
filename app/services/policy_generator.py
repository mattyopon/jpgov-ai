# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""ポリシーテンプレート自動生成サービス.

企業がガバナンスに必要な方針文書をテンプレートベースで自動生成する。
- AI利用ポリシー
- AIリスク管理方針
- AI倫理方針
- データ管理方針
- インシデント対応手順書
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models import PolicyDocument, PolicyType


# ── テンプレート定義 ──

POLICY_TEMPLATES: dict[PolicyType, dict] = {
    PolicyType.AI_USAGE: {
        "title": "AI利用ポリシー",
        "description": "組織におけるAIの利用に関する基本方針を定めた文書",
        "sections": [
            {
                "heading": "1. 目的",
                "content": (
                    "本ポリシーは、{org_name}（以下「当社」）におけるAI（人工知能）の"
                    "利用に関する基本方針を定め、安全かつ責任あるAI活用を推進することを目的とする。"
                ),
            },
            {
                "heading": "2. 適用範囲",
                "content": (
                    "本ポリシーは、当社の全部門・全従業員が業務で利用するAIシステム・サービスに適用される。\n"
                    "対象には以下を含む：\n"
                    "- 社内開発のAIシステム\n"
                    "- 外部から導入したAIサービス・API\n"
                    "- 生成AI（ChatGPT、Claude等）の業務利用"
                ),
            },
            {
                "heading": "3. 基本原則",
                "content": (
                    "当社のAI利用は以下の原則に基づく：\n"
                    "3.1 人間中心: AIの判断に対する最終的な責任は人間が負う\n"
                    "3.2 安全性: AIシステムの安全な運用を確保する\n"
                    "3.3 公平性: 不当な差別を行わないよう配慮する\n"
                    "3.4 透明性: AI利用を利害関係者に適切に開示する\n"
                    "3.5 プライバシー: 個人情報の保護を徹底する"
                ),
            },
            {
                "heading": "4. 利用ルール",
                "content": (
                    "4.1 業務利用の承認: 新たなAIシステムの導入には所属長の承認を得ること\n"
                    "4.2 データ入力制限: 機密情報・個人情報を外部AIサービスに入力しないこと\n"
                    "4.3 出力検証: AIの出力は必ず人間が確認・検証すること\n"
                    "4.4 記録保持: AI利用の記録を適切に保持すること"
                ),
            },
            {
                "heading": "5. 禁止事項",
                "content": (
                    "以下のAI利用を禁止する：\n"
                    "- 法令に違反する目的での利用\n"
                    "- 他者の権利を侵害する利用\n"
                    "- 承認されていないAIサービスの業務利用\n"
                    "- AI出力を検証なしで最終成果物として使用すること"
                ),
            },
            {
                "heading": "6. 責任体制",
                "content": (
                    "6.1 AIガバナンス責任者: [役職名]がAI利用全般を統括する\n"
                    "6.2 各部門責任者: 部門内のAI利用の管理・監督を行う\n"
                    "6.3 全従業員: 本ポリシーを遵守し、問題を発見した場合は速やかに報告する"
                ),
            },
            {
                "heading": "7. 改定",
                "content": "本ポリシーは年1回以上見直し、必要に応じて改定する。",
            },
        ],
    },

    PolicyType.RISK_MANAGEMENT: {
        "title": "AIリスク管理方針",
        "description": "AIシステムのリスクを特定・評価・軽減するための方針",
        "sections": [
            {
                "heading": "1. 目的",
                "content": (
                    "本方針は、{org_name}が開発・提供・利用するAIシステムに関するリスクを"
                    "体系的に管理し、安全性を確保することを目的とする。"
                ),
            },
            {
                "heading": "2. リスク分類",
                "content": (
                    "AIシステムのリスクを以下の4段階に分類する：\n"
                    "- 許容不可リスク: 法令・倫理に違反するリスク → 使用禁止\n"
                    "- 高リスク: 人の生命・安全・権利に影響 → 厳格な管理措置\n"
                    "- 限定的リスク: 透明性の確保が必要 → 情報開示義務\n"
                    "- 最小リスク: 特段の規制なし → 自主的対応"
                ),
            },
            {
                "heading": "3. リスクアセスメントプロセス",
                "content": (
                    "3.1 リスク特定: AIシステムの用途・データ・影響範囲からリスクを特定\n"
                    "3.2 リスク評価: 影響度×発生確率でリスクレベルを評価\n"
                    "3.3 リスク対応: 回避・軽減・移転・受容の選択肢から対応を決定\n"
                    "3.4 モニタリング: 継続的なリスク監視と定期的な再評価"
                ),
            },
            {
                "heading": "4. 実施体制",
                "content": (
                    "4.1 リスク管理責任者: [役職名]\n"
                    "4.2 リスク評価実施頻度: 四半期ごと、および重大変更時\n"
                    "4.3 報告: リスク評価結果は経営層に報告する"
                ),
            },
            {
                "heading": "5. インシデント対応",
                "content": (
                    "リスクが顕在化した場合の対応は「インシデント対応手順書」に従う。"
                ),
            },
        ],
    },

    PolicyType.ETHICS: {
        "title": "AI倫理方針",
        "description": "AI開発・利用における倫理的な指針",
        "sections": [
            {
                "heading": "1. 基本理念",
                "content": (
                    "{org_name}は、AIが人類の福祉に貢献する技術であることを信じ、"
                    "以下の倫理原則に基づきAIの開発・利用を行う。"
                ),
            },
            {
                "heading": "2. 倫理原則",
                "content": (
                    "2.1 人間の尊厳の尊重: AIは人間の尊厳を損なう目的で使用しない\n"
                    "2.2 公平性・非差別: AIによる不当な差別を防止する\n"
                    "2.3 透明性・説明可能性: AIの判断根拠を可能な限り説明する\n"
                    "2.4 プライバシーの尊重: 個人の情報とプライバシーを保護する\n"
                    "2.5 安全性・信頼性: AIシステムの安全な運用を確保する\n"
                    "2.6 アカウンタビリティ: AIに関する説明責任を果たす"
                ),
            },
            {
                "heading": "3. 倫理審査",
                "content": (
                    "3.1 高リスクAIシステムの導入・変更時には倫理審査を実施する\n"
                    "3.2 倫理審査委員会: [委員構成を記載]\n"
                    "3.3 審査基準: 本方針の倫理原則への適合性を評価する"
                ),
            },
            {
                "heading": "4. ステークホルダーとの対話",
                "content": (
                    "AIの利用に関して利害関係者との対話の機会を設け、"
                    "懸念や要望を把握し、方針に反映する。"
                ),
            },
        ],
    },

    PolicyType.DATA_MANAGEMENT: {
        "title": "データ管理方針",
        "description": "AI開発・運用に使用するデータの管理に関する方針",
        "sections": [
            {
                "heading": "1. 目的",
                "content": (
                    "本方針は、{org_name}がAI開発・運用に使用するデータの品質・安全性・"
                    "プライバシーを確保するための管理基準を定める。"
                ),
            },
            {
                "heading": "2. データ分類",
                "content": (
                    "2.1 公開データ: 一般公開されている情報\n"
                    "2.2 社内データ: 業務で生成された非公開情報\n"
                    "2.3 個人情報: 個人を特定できる情報\n"
                    "2.4 要配慮個人情報: 医療・信用情報等のセンシティブデータ"
                ),
            },
            {
                "heading": "3. データ品質管理",
                "content": (
                    "3.1 学習データの品質基準を定め、定期的に評価する\n"
                    "3.2 データの正確性・完全性・鮮度を維持する\n"
                    "3.3 バイアスの検出と是正を継続的に行う"
                ),
            },
            {
                "heading": "4. プライバシー保護",
                "content": (
                    "4.1 データ最小化の原則を遵守する\n"
                    "4.2 目的外利用を禁止する\n"
                    "4.3 適切な匿名化・仮名化措置を講じる\n"
                    "4.4 プライバシー影響評価（PIA）を実施する"
                ),
            },
            {
                "heading": "5. データセキュリティ",
                "content": (
                    "5.1 データの暗号化（保存時・転送時）\n"
                    "5.2 アクセス制御（最小権限の原則）\n"
                    "5.3 監査ログの記録\n"
                    "5.4 データ廃棄手順の整備"
                ),
            },
        ],
    },

    PolicyType.INCIDENT_RESPONSE: {
        "title": "AIインシデント対応手順書",
        "description": "AIシステムに関するインシデント発生時の対応手順",
        "sections": [
            {
                "heading": "1. 目的",
                "content": (
                    "本手順書は、{org_name}が運用するAIシステムに関するインシデント発生時の"
                    "対応手順を定め、被害の最小化と迅速な復旧を図ることを目的とする。"
                ),
            },
            {
                "heading": "2. インシデントの定義と分類",
                "content": (
                    "2.1 重大インシデント: 人の生命・安全・権利に影響するもの\n"
                    "2.2 セキュリティインシデント: データ漏洩、不正アクセス等\n"
                    "2.3 品質インシデント: AI出力の品質低下、バイアス検出等\n"
                    "2.4 運用インシデント: システム障害、性能劣化等"
                ),
            },
            {
                "heading": "3. 対応フロー",
                "content": (
                    "3.1 検知・報告: インシデントを検知した者は直ちに責任者に報告\n"
                    "3.2 初動対応: 被害拡大防止措置（AIシステムの停止を含む）\n"
                    "3.3 影響調査: 影響範囲と原因の調査\n"
                    "3.4 是正措置: 原因の除去と再発防止策の実施\n"
                    "3.5 報告: 経営層・関係者・当局への報告（必要に応じて）\n"
                    "3.6 記録: インシデント対応の全過程を記録・保存"
                ),
            },
            {
                "heading": "4. 連絡体制",
                "content": (
                    "4.1 インシデント対応責任者: [役職名・連絡先]\n"
                    "4.2 エスカレーションルール: [基準を記載]\n"
                    "4.3 外部連絡先: 監督官庁、セキュリティベンダー等"
                ),
            },
            {
                "heading": "5. 訓練・演習",
                "content": (
                    "5.1 年1回以上のインシデント対応訓練を実施する\n"
                    "5.2 訓練結果を評価し、手順書の改善に反映する"
                ),
            },
        ],
    },
}


def get_available_policy_types() -> list[dict]:
    """利用可能なポリシータイプ一覧を返す."""
    return [
        {
            "type": pt.value,
            "title": info["title"],
            "description": info["description"],
        }
        for pt, info in POLICY_TEMPLATES.items()
    ]


def generate_policy(
    policy_type: PolicyType,
    organization_name: str,
    organization_id: str = "",
) -> PolicyDocument:
    """ポリシーテンプレートを生成.

    Args:
        policy_type: ポリシー種別
        organization_name: 組織名（テンプレートに埋め込む）
        organization_id: 組織ID

    Returns:
        PolicyDocument: 生成されたポリシー文書
    """
    template = POLICY_TEMPLATES.get(policy_type)
    if template is None:
        raise ValueError(f"Unknown policy type: {policy_type}")

    # テンプレートに組織名を埋め込む
    sections: list[dict] = []
    for section in template["sections"]:
        sections.append({
            "heading": section["heading"],
            "content": section["content"].format(org_name=organization_name),
        })

    # Markdown形式でfull_textを生成
    lines = [f"# {template['title']}", ""]
    lines.append(f"**組織名**: {organization_name}")
    lines.append(f"**作成日**: {datetime.now(timezone.utc).strftime('%Y年%m月%d日')}")
    lines.append(f"**文書ID**: POL-{uuid.uuid4().hex[:8].upper()}")
    lines.append("")

    for section in sections:
        lines.append(f"## {section['heading']}")
        lines.append("")
        lines.append(section["content"])
        lines.append("")

    lines.append("---")
    lines.append("*本文書はJPGovAIにより自動生成されたテンプレートです。組織の実態に合わせて修正してください。*")

    full_text = "\n".join(lines)

    return PolicyDocument(
        organization_id=organization_id,
        policy_type=policy_type,
        title=template["title"],
        sections=sections,
        full_text=full_text,
    )


def generate_all_policies(
    organization_name: str,
    organization_id: str = "",
) -> list[PolicyDocument]:
    """全ポリシーをまとめて生成.

    Args:
        organization_name: 組織名
        organization_id: 組織ID

    Returns:
        list[PolicyDocument]: 全ポリシー文書のリスト
    """
    return [
        generate_policy(pt, organization_name, organization_id)
        for pt in PolicyType
    ]
