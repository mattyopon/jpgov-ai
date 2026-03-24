# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""経済産業省・総務省「AI事業者ガイドライン（第1.0版）」要件定義.

本ファイルは2024年4月19日公開の「AI事業者ガイドライン（第1.0版）」に基づく。
ガイドラインはAI開発者・AI提供者・AI利用者の3事業者類型に共通する
10の基本原則と、各原則に紐づく具体的要件を定義する。

出典:
- https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/20240419_report.html
- https://www.meti.go.jp/press/2024/04/20240419004/20240419004.html
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Requirement:
    """ガイドラインの個別要件."""

    req_id: str
    category_id: str
    title: str
    description: str
    target_roles: list[str] = field(default_factory=lambda: ["developer", "provider", "user"])
    risk_level: str = "all"  # all / high / limited


@dataclass(frozen=True)
class Category:
    """ガイドラインの原則カテゴリ."""

    category_id: str
    title: str
    description: str
    requirements: list[Requirement] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 10原則と具体的要件
# ---------------------------------------------------------------------------

CATEGORIES: list[Category] = [
    # ── 1. 人間中心 ──────────────────────────────────────────────────
    Category(
        category_id="C01",
        title="人間中心（Human-Centric）",
        description=(
            "AIシステム・サービスの開発・提供・利用において、"
            "人間の尊厳と個人の自律を尊重し、人間が意思決定の主体であることを確保する。"
        ),
        requirements=[
            Requirement(
                req_id="C01-R01",
                category_id="C01",
                title="人間の尊厳・自律の尊重",
                description="AIの判断が人間の尊厳を損なわないよう、人間中心の原則を方針として定め、組織内に周知すること。",
            ),
            Requirement(
                req_id="C01-R02",
                category_id="C01",
                title="意思決定における人間の関与",
                description="AIの判断結果を最終的に人間が確認・判断できるプロセスを整備すること。特に高リスク領域では人間の介在を必須とすること。",
                risk_level="high",
            ),
            Requirement(
                req_id="C01-R03",
                category_id="C01",
                title="誤情報・偽情報への対処",
                description="AIが生成する情報の正確性を確認する仕組みを設け、誤情報・偽情報の拡散防止策を講じること。",
            ),
        ],
    ),

    # ── 2. 安全性 ──────────────────────────────────────────────────
    Category(
        category_id="C02",
        title="安全性（Safety）",
        description=(
            "AIシステムが利害関係者の生命・身体・財産に危害を及ぼさないよう、"
            "適切な学習データの選定と安全な運用を確保する。"
        ),
        requirements=[
            Requirement(
                req_id="C02-R01",
                category_id="C02",
                title="リスクアセスメントの実施",
                description="AIシステムのリスクを特定・評価・軽減するためのリスクアセスメントを定期的に実施すること。",
            ),
            Requirement(
                req_id="C02-R02",
                category_id="C02",
                title="学習データの品質管理",
                description="学習データの品質（正確性・網羅性・偏りの有無）を管理し、不適切なデータによる危害を防止すること。",
                target_roles=["developer"],
            ),
            Requirement(
                req_id="C02-R03",
                category_id="C02",
                title="安全な運用・停止手順",
                description="AIシステムに異常が発生した場合の安全な停止手順、フォールバック手段を事前に定めること。",
            ),
        ],
    ),

    # ── 3. 公平性 ──────────────────────────────────────────────────
    Category(
        category_id="C03",
        title="公平性（Fairness）",
        description=(
            "AIシステムが特定の集団に対して不当な差別を行わないよう配慮し、"
            "バイアスの評価と是正に努める。"
        ),
        requirements=[
            Requirement(
                req_id="C03-R01",
                category_id="C03",
                title="バイアス評価の実施",
                description="AIシステムの出力が特定の属性（性別・人種・年齢等）に基づく不当な差別を含まないか評価すること。",
            ),
            Requirement(
                req_id="C03-R02",
                category_id="C03",
                title="公平性基準の策定",
                description="利用文脈に応じた公平性の基準を定め、定期的にモニタリングすること。",
            ),
            Requirement(
                req_id="C03-R03",
                category_id="C03",
                title="差別的影響の是正措置",
                description="バイアスが検出された場合の是正手順を事前に定め、速やかに対応すること。",
            ),
        ],
    ),

    # ── 4. プライバシー保護 ────────────────────────────────────────
    Category(
        category_id="C04",
        title="プライバシー保護（Privacy Protection）",
        description=(
            "AIシステムの開発・提供・利用において、"
            "個人情報・プライバシーの保護に努める。"
        ),
        requirements=[
            Requirement(
                req_id="C04-R01",
                category_id="C04",
                title="個人情報取扱方針の策定",
                description="AIに関する個人情報の取得・利用・提供・保管・削除に関する方針を策定し、公表すること。",
            ),
            Requirement(
                req_id="C04-R02",
                category_id="C04",
                title="プライバシー影響評価",
                description="AIシステムの導入前にプライバシー影響評価（PIA）を実施し、リスクを特定・軽減すること。",
            ),
            Requirement(
                req_id="C04-R03",
                category_id="C04",
                title="データ最小化・目的外利用禁止",
                description="必要最小限のデータのみを取り扱い、当初の目的以外での利用を行わないこと。",
            ),
        ],
    ),

    # ── 5. セキュリティ確保 ────────────────────────────────────────
    Category(
        category_id="C05",
        title="セキュリティ確保（Security）",
        description=(
            "AIシステムに対する不正な操作・アクセスによって意図しない動作変更や"
            "停止が生じないよう、セキュリティを確保する。"
        ),
        requirements=[
            Requirement(
                req_id="C05-R01",
                category_id="C05",
                title="セキュリティ対策の実施",
                description="AIシステムに対する攻撃（敵対的攻撃、データポイズニング等）への防御策を講じること。",
            ),
            Requirement(
                req_id="C05-R02",
                category_id="C05",
                title="脆弱性管理",
                description="AIシステムの脆弱性を定期的に評価し、発見された脆弱性に速やかに対処すること。",
            ),
            Requirement(
                req_id="C05-R03",
                category_id="C05",
                title="インシデント対応体制",
                description="セキュリティインシデント発生時の対応手順・連絡体制を事前に整備すること。",
            ),
        ],
    ),

    # ── 6. 透明性 ──────────────────────────────────────────────────
    Category(
        category_id="C06",
        title="透明性（Transparency）",
        description=(
            "利害関係者に対して、技術的に可能な範囲で合理的な情報提供を行い、"
            "AIサービスの検証可能性を確保する。"
        ),
        requirements=[
            Requirement(
                req_id="C06-R01",
                category_id="C06",
                title="AI利用の明示",
                description="AIを利用していることを利害関係者に適切に開示すること。",
            ),
            Requirement(
                req_id="C06-R02",
                category_id="C06",
                title="判断根拠の説明",
                description="AIの判断結果について、技術的に可能な範囲で根拠を説明できるようにすること。",
            ),
            Requirement(
                req_id="C06-R03",
                category_id="C06",
                title="技術情報の文書化",
                description="AIシステムの技術仕様・学習データ・性能指標等を文書化し、必要に応じて開示できるようにすること。",
                target_roles=["developer", "provider"],
            ),
        ],
    ),

    # ── 7. アカウンタビリティ ──────────────────────────────────────
    Category(
        category_id="C07",
        title="アカウンタビリティ（Accountability）",
        description=(
            "AIシステムに関する責任の所在を明確にし、"
            "事実上・法律上の責任を果たす体制を整備する。"
        ),
        requirements=[
            Requirement(
                req_id="C07-R01",
                category_id="C07",
                title="責任者の指定",
                description="AIガバナンスに関する責任者を指定し、その権限と責任を明確にすること。",
            ),
            Requirement(
                req_id="C07-R02",
                category_id="C07",
                title="ガバナンス方針・体制の整備",
                description="AIの開発・提供・利用に関するガバナンス方針を策定し、実施体制を整備すること。",
            ),
            Requirement(
                req_id="C07-R03",
                category_id="C07",
                title="契約・SLAの整備",
                description="AI関連の取引において、責任分界・品質保証・免責等を契約やSLAで明確にすること。",
            ),
            Requirement(
                req_id="C07-R04",
                category_id="C07",
                title="ガバナンス記録の保持",
                description="ガバナンスに関する決定事項・実施記録を適切に保持し、監査可能な状態にすること。",
            ),
        ],
    ),

    # ── 8. 教育・リテラシー ────────────────────────────────────────
    Category(
        category_id="C08",
        title="教育・リテラシー（Education & Literacy）",
        description=(
            "AIシステムの正しい理解と適切な利用のために、"
            "必要な教育を提供する。"
        ),
        requirements=[
            Requirement(
                req_id="C08-R01",
                category_id="C08",
                title="従業員教育の実施",
                description="AIを扱う従業員に対して、AIの特性・限界・リスクに関する教育を定期的に実施すること。",
            ),
            Requirement(
                req_id="C08-R02",
                category_id="C08",
                title="利用者への情報提供",
                description="AIシステムの利用者に対して、適切な利用方法・注意事項を提供すること。",
                target_roles=["provider", "user"],
            ),
        ],
    ),

    # ── 9. 公正競争の確保 ──────────────────────────────────────────
    Category(
        category_id="C09",
        title="公正競争の確保（Fair Competition）",
        description=(
            "AIを取り巻く公正な競争環境の維持に努める。"
        ),
        requirements=[
            Requirement(
                req_id="C09-R01",
                category_id="C09",
                title="公正競争への配慮",
                description="AIの開発・提供・利用において、不当な競争制限行為を行わないこと。",
            ),
            Requirement(
                req_id="C09-R02",
                category_id="C09",
                title="知的財産の尊重",
                description="AIの学習・利用において、他者の知的財産権を尊重すること。",
            ),
        ],
    ),

    # ── 10. イノベーション ─────────────────────────────────────────
    Category(
        category_id="C10",
        title="イノベーション（Innovation）",
        description=(
            "社会全体のイノベーション促進に貢献するよう努める。"
        ),
        requirements=[
            Requirement(
                req_id="C10-R01",
                category_id="C10",
                title="イノベーション促進への貢献",
                description="AIの研究・開発・利用を通じて、社会課題の解決やイノベーション促進に貢献すること。",
            ),
            Requirement(
                req_id="C10-R02",
                category_id="C10",
                title="相互運用性・オープン性の確保",
                description="技術的な囲い込みを避け、相互運用性やオープン性の確保に努めること。",
            ),
        ],
    ),
]

# ── ユーティリティ ────────────────────────────────────────────────

_CATEGORY_MAP: dict[str, Category] = {c.category_id: c for c in CATEGORIES}
_REQUIREMENT_MAP: dict[str, Requirement] = {
    r.req_id: r for c in CATEGORIES for r in c.requirements
}


def get_category(category_id: str) -> Category | None:
    """カテゴリIDからカテゴリを取得."""
    return _CATEGORY_MAP.get(category_id)


def get_requirement(req_id: str) -> Requirement | None:
    """要件IDから要件を取得."""
    return _REQUIREMENT_MAP.get(req_id)


def all_requirements() -> list[Requirement]:
    """全要件をフラットなリストで返す."""
    return [r for c in CATEGORIES for r in c.requirements]


def all_requirement_ids() -> list[str]:
    """全要件IDのリスト."""
    return [r.req_id for r in all_requirements()]


# ── 質問票定義 ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Question:
    """自己診断質問票の質問."""

    question_id: str
    category_id: str
    text: str
    options: list[str]
    scores: list[int]  # 各選択肢に対応するスコア (0-4)
    requirement_ids: list[str]  # 関連する要件ID


ASSESSMENT_QUESTIONS: list[Question] = [
    # ── C01: 人間中心 ──
    Question(
        question_id="Q01",
        category_id="C01",
        text="AIの判断結果に対する最終的な人間の確認・承認プロセスはありますか？",
        options=[
            "プロセスなし",
            "一部のAIシステムにのみ存在",
            "高リスク領域には存在",
            "全AIシステムに標準化されたプロセスがある",
            "定期的に見直し・改善されている",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C01-R01", "C01-R02"],
    ),
    Question(
        question_id="Q02",
        category_id="C01",
        text="AIが生成する情報の正確性を検証する仕組みはありますか？",
        options=[
            "仕組みなし",
            "担当者が個別に確認",
            "一部のシステムに自動検証あり",
            "全システムに検証プロセスあり",
            "継続的モニタリング＋改善サイクルあり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C01-R03"],
    ),
    # ── C02: 安全性 ──
    Question(
        question_id="Q03",
        category_id="C02",
        text="AIシステムのリスクアセスメントを実施していますか？",
        options=[
            "未実施",
            "導入時のみ実施",
            "年1回実施",
            "四半期ごとに実施",
            "継続的なリスクモニタリング体制あり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C02-R01"],
    ),
    Question(
        question_id="Q04",
        category_id="C02",
        text="学習データの品質管理プロセスはありますか？",
        options=[
            "管理なし",
            "基本的なデータクレンジングのみ",
            "品質基準を策定済み",
            "定期的な品質評価を実施",
            "自動品質チェック＋人手レビュー体制あり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C02-R02"],
    ),
    Question(
        question_id="Q05",
        category_id="C02",
        text="AIシステムの異常時の安全停止手順は定められていますか？",
        options=[
            "未策定",
            "口頭ベースの対応のみ",
            "手順書が存在する",
            "手順書＋定期訓練を実施",
            "自動フォールバック＋手動介入の二重体制",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C02-R03"],
    ),
    # ── C03: 公平性 ──
    Question(
        question_id="Q06",
        category_id="C03",
        text="AIシステムのバイアス評価を実施していますか？",
        options=[
            "未実施",
            "問題指摘時のみ調査",
            "導入時に評価",
            "定期的な評価を実施",
            "継続的モニタリング＋自動アラートあり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C03-R01", "C03-R02"],
    ),
    Question(
        question_id="Q07",
        category_id="C03",
        text="バイアス検出時の是正手順は定められていますか？",
        options=[
            "未策定",
            "個別対応",
            "基本方針がある",
            "詳細な是正手順＋責任者が明確",
            "是正＋再発防止＋報告の体制が確立",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C03-R03"],
    ),
    # ── C04: プライバシー保護 ──
    Question(
        question_id="Q08",
        category_id="C04",
        text="AIに関する個人情報の取扱方針は策定・公表していますか？",
        options=[
            "未策定",
            "一般的なプライバシーポリシーのみ",
            "AI固有の方針を策定中",
            "AI固有の方針を策定・社内周知済み",
            "策定・公表済み＋定期見直し",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C04-R01"],
    ),
    Question(
        question_id="Q09",
        category_id="C04",
        text="AIシステム導入前にプライバシー影響評価（PIA）を実施していますか？",
        options=[
            "未実施",
            "高リスクシステムのみ実施",
            "全システムで簡易評価",
            "全システムで詳細PIA実施",
            "PIA＋継続的プライバシーモニタリング",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C04-R02", "C04-R03"],
    ),
    # ── C05: セキュリティ ──
    Question(
        question_id="Q10",
        category_id="C05",
        text="AIシステムに対するセキュリティ対策（敵対的攻撃対策等）を実施していますか？",
        options=[
            "未実施",
            "一般的なIT対策のみ",
            "AI固有の脅威を考慮した対策あり",
            "敵対的攻撃テスト等を定期実施",
            "Red Team演習＋継続的脆弱性管理",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C05-R01", "C05-R02"],
    ),
    Question(
        question_id="Q11",
        category_id="C05",
        text="AIセキュリティインシデント対応体制は整備されていますか？",
        options=[
            "未整備",
            "一般的なインシデント対応のみ",
            "AI固有のインシデント対応手順あり",
            "手順＋定期訓練を実施",
            "24/7対応体制＋自動検知あり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C05-R03"],
    ),
    # ── C06: 透明性 ──
    Question(
        question_id="Q12",
        category_id="C06",
        text="AIの利用を利害関係者に開示していますか？",
        options=[
            "未開示",
            "問い合わせ時のみ回答",
            "利用規約等に記載",
            "積極的に開示し説明",
            "開示＋フィードバック受付体制あり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C06-R01"],
    ),
    Question(
        question_id="Q13",
        category_id="C06",
        text="AIの判断根拠を説明する仕組みはありますか？",
        options=[
            "説明不可",
            "技術者が個別に説明可能",
            "一般利用者向けの説明ドキュメントあり",
            "システムが自動で根拠を提示",
            "説明可能AI（XAI）技術を導入済み",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C06-R02", "C06-R03"],
    ),
    # ── C07: アカウンタビリティ ──
    Question(
        question_id="Q14",
        category_id="C07",
        text="AIガバナンスの責任者は指定されていますか？",
        options=[
            "未指定",
            "暗黙の担当者がいる",
            "正式に指定済み",
            "責任者＋専門チーム設置",
            "CAIO等のC-suite＋専門委員会あり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C07-R01"],
    ),
    Question(
        question_id="Q15",
        category_id="C07",
        text="AIガバナンス方針・体制は整備されていますか？",
        options=[
            "未整備",
            "検討中",
            "基本方針を策定済み",
            "方針＋実施体制＋監査体制あり",
            "PDCA＋外部監査＋定期報告体制",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C07-R02", "C07-R03", "C07-R04"],
    ),
    # ── C08: 教育・リテラシー ──
    Question(
        question_id="Q16",
        category_id="C08",
        text="AI関連の従業員教育を実施していますか？",
        options=[
            "未実施",
            "希望者のみ受講可",
            "AI関連部署のみ必須",
            "全従業員に年1回以上実施",
            "役割別教育＋効果測定＋継続改善",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C08-R01"],
    ),
    Question(
        question_id="Q17",
        category_id="C08",
        text="AIシステムの利用者に適切な利用方法を提供していますか？",
        options=[
            "未提供",
            "基本的なマニュアルのみ",
            "利用ガイドライン＋FAQ",
            "対話型サポート＋定期研修",
            "パーソナライズされたガイダンス＋フィードバック収集",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C08-R02"],
    ),
    # ── C09: 公正競争 ──
    Question(
        question_id="Q18",
        category_id="C09",
        text="AI利用における公正競争への配慮は行っていますか？",
        options=[
            "配慮なし",
            "法務部門が必要に応じ確認",
            "公正競争方針を策定",
            "方針＋定期レビュー",
            "競争法コンプライアンス体制＋外部監査",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C09-R01", "C09-R02"],
    ),
    # ── C10: イノベーション ──
    Question(
        question_id="Q19",
        category_id="C10",
        text="AIを通じたイノベーション促進への取り組みはありますか？",
        options=[
            "取り組みなし",
            "個別プロジェクトのみ",
            "組織的なAI活用推進",
            "社外連携・オープンイノベーション",
            "エコシステム構築＋社会課題解決への貢献",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C10-R01", "C10-R02"],
    ),
    # ── 横断質問 ──
    Question(
        question_id="Q20",
        category_id="C07",
        text="AIに関するガバナンス記録（意思決定記録・実施記録等）を保持していますか？",
        options=[
            "記録なし",
            "メールや議事録に散在",
            "統一的な記録管理を開始",
            "体系的な記録管理＋検索可能",
            "改竄防止＋監査証跡＋長期保存体制",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C07-R04"],
    ),
    Question(
        question_id="Q21",
        category_id="C02",
        text="貴社のAIの主な用途は何ですか？（最もリスクの高いものを選択）",
        options=[
            "社内業務効率化のみ",
            "コンテンツ生成・クリエイティブ支援",
            "顧客対応・サービス提供",
            "意思決定支援（審査・評価等）",
            "自律的意思決定（自動取引・自動判定等）",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C01-R02", "C02-R01"],
    ),
    Question(
        question_id="Q22",
        category_id="C04",
        text="AIシステムが扱うデータの種類は？（最もセンシティブなものを選択）",
        options=[
            "公開情報のみ",
            "社内業務データ",
            "顧客の非個人情報",
            "個人情報（氏名・連絡先等）",
            "要配慮個人情報（医療・信用情報等）",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C04-R01", "C04-R02", "C04-R03"],
    ),
    Question(
        question_id="Q23",
        category_id="C05",
        text="外部AIサービス（API）のセキュリティ管理はどの程度実施していますか？",
        options=[
            "管理なし",
            "サービス利用規約の確認のみ",
            "データ送信内容の制限ルールあり",
            "API利用のセキュリティガイドライン策定済み",
            "DLP＋モニタリング＋定期監査体制あり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C05-R01", "C05-R02"],
    ),
    Question(
        question_id="Q24",
        category_id="C06",
        text="AIシステムの技術仕様・性能指標の文書化はどの程度行っていますか？",
        options=[
            "文書化なし",
            "開発メモレベル",
            "基本的な技術文書あり",
            "モデルカード等の標準フォーマットで管理",
            "バージョン管理＋変更履歴＋公開体制あり",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C06-R03"],
    ),
    Question(
        question_id="Q25",
        category_id="C07",
        text="AIに関する契約・SLAの整備状況は？",
        options=[
            "未整備",
            "一般的な業務委託契約のみ",
            "AI固有の条項を追加検討中",
            "AI固有の責任分界・品質保証条項あり",
            "標準テンプレート＋法務レビュー＋定期更新",
        ],
        scores=[0, 1, 2, 3, 4],
        requirement_ids=["C07-R03"],
    ),
]
