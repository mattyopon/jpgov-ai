# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""NIST AI Risk Management Framework (AI RMF) 1.0 要件定義.

米国NISTのAIリスク管理フレームワーク。4つのコア機能
（Govern / Map / Measure / Manage）とサブカテゴリを定義。

グローバル展開企業は本フレームワークへの対応が求められる。
METI AI事業者ガイドライン及びISO 42001とのクロスマッピングを含む。

参考:
- NIST AI 100-1: Artificial Intelligence Risk Management Framework (AI RMF 1.0)
  https://www.nist.gov/artificial-intelligence/executive-order-safe-secure-and-trustworthy-artificial-intelligence
- NIST AI RMF Playbook
  https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NISTSubcategory:
    """NIST AI RMF サブカテゴリ."""

    subcategory_id: str  # e.g., "GOVERN-1.1"
    title: str
    description: str
    suggested_actions: list[str] = field(default_factory=list)
    meti_mapping: list[str] = field(default_factory=list)
    iso_mapping: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NISTCategory:
    """NIST AI RMF カテゴリ."""

    category_id: str  # e.g., "GOVERN-1"
    title: str
    description: str
    subcategories: list[NISTSubcategory] = field(default_factory=list)


@dataclass(frozen=True)
class NISTFunction:
    """NIST AI RMF コア機能."""

    function_id: str  # "GOVERN", "MAP", "MEASURE", "MANAGE"
    title: str
    description: str
    categories: list[NISTCategory] = field(default_factory=list)


# ---------------------------------------------------------------------------
# NIST AI RMF 1.0 定義
# ---------------------------------------------------------------------------

NIST_FUNCTIONS: list[NISTFunction] = [
    # ══════════════════════════════════════════════════════════════════
    # GOVERN — ガバナンス
    # ══════════════════════════════════════════════════════════════════
    NISTFunction(
        function_id="GOVERN",
        title="GOVERN（統治）",
        description=(
            "AI リスク管理に関する組織文化を育成し、"
            "プロセス、手順、実践が組織全体にわたって実施され、"
            "AIシステムのリスク管理を効果的に行う。"
        ),
        categories=[
            NISTCategory(
                category_id="GOVERN-1",
                title="方針、プロセス、手順、実践",
                description="AIリスク管理のための方針、プロセス、手順を確立し維持する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="GOVERN-1.1",
                        title="AIリスク管理のための法的・規制的要件の特定",
                        description="AIリスク管理に適用される法的・規制的要件を特定し、文書化する。",
                        suggested_actions=[
                            "AIに関連する国内外の法規制を調査・特定する",
                            "規制要件への対応状況をモニタリングする体制を構築する",
                            "法規制の変更を追跡し、影響を評価するプロセスを確立する",
                        ],
                        meti_mapping=["C07-R02"],
                        iso_mapping=["ISO-4.1", "ISO-4.2"],
                    ),
                    NISTSubcategory(
                        subcategory_id="GOVERN-1.2",
                        title="信頼できるAIの特性を組織方針に統合",
                        description="信頼性、公平性、透明性等の特性を組織のAI方針に統合する。",
                        suggested_actions=[
                            "AI倫理原則を組織方針に組み込む",
                            "信頼できるAIの特性に関するKPIを設定する",
                            "方針の実施状況を定期的にレビューする",
                        ],
                        meti_mapping=["C01-R01", "C07-R02"],
                        iso_mapping=["ISO-4.3", "ISO-5.2"],
                    ),
                    NISTSubcategory(
                        subcategory_id="GOVERN-1.3",
                        title="AIリスク管理のリソース確保",
                        description="AIリスク管理に必要な人的・技術的・財務的リソースを確保する。",
                        suggested_actions=[
                            "AIリスク管理に必要なリソースを見積もり、予算化する",
                            "必要な人材の採用・育成計画を策定する",
                            "外部専門家の活用方針を定める",
                        ],
                        meti_mapping=["C07-R01", "C07-R02"],
                        iso_mapping=["ISO-5.1", "ISO-7.1"],
                    ),
                    NISTSubcategory(
                        subcategory_id="GOVERN-1.4",
                        title="AIリスク管理の継続的改善",
                        description="AIリスク管理プロセスを継続的にレビューし改善する。",
                        suggested_actions=[
                            "定期的なAIリスク管理プロセスのレビューを実施する",
                            "インシデントや課題からの学習を体系化する",
                            "内部監査・外部監査の結果を改善に反映する",
                        ],
                        meti_mapping=["C07-R04"],
                        iso_mapping=["ISO-7.5", "ISO-9.2", "ISO-10.2"],
                    ),
                    NISTSubcategory(
                        subcategory_id="GOVERN-1.5",
                        title="ステークホルダーへの情報共有",
                        description="AIリスク管理に関する情報をステークホルダーと共有する。",
                        suggested_actions=[
                            "AIリスク管理の状況を定期的にステークホルダーに報告する",
                            "透明性のある情報開示の仕組みを構築する",
                        ],
                        meti_mapping=["C06-R01", "C06-R02"],
                        iso_mapping=["ISO-7.4"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="GOVERN-2",
                title="役割、責任、アカウンタビリティ",
                description="AIリスク管理に関する役割、責任、アカウンタビリティを定義する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="GOVERN-2.1",
                        title="AIリスク管理の役割・責任の明確化",
                        description="AIリスク管理に関する役割と責任を明確に定義し割り当てる。",
                        suggested_actions=[
                            "AIリスク管理の責任者を任命する",
                            "RACIマトリクスを作成する",
                            "役割・責任を全関係者に周知する",
                        ],
                        meti_mapping=["C07-R01"],
                        iso_mapping=["ISO-5.3", "ISO-7.1"],
                    ),
                    NISTSubcategory(
                        subcategory_id="GOVERN-2.2",
                        title="AI力量と意識の確保",
                        description="AIリスク管理に関わる人員の力量と意識を確保する。",
                        suggested_actions=[
                            "AI倫理・リスクに関する研修を全従業員に提供する",
                            "AIリスク管理の専門家を育成する",
                            "力量評価を定期的に実施する",
                        ],
                        meti_mapping=["C08-R01", "C08-R02"],
                        iso_mapping=["ISO-7.2", "ISO-7.3"],
                    ),
                    NISTSubcategory(
                        subcategory_id="GOVERN-2.3",
                        title="多様な視点の確保",
                        description="AIリスク管理に多様な背景・専門分野の人材を参画させる。",
                        suggested_actions=[
                            "AIガバナンス委員会に多様なバックグラウンドのメンバーを含める",
                            "外部有識者のアドバイスを受ける仕組みを構築する",
                        ],
                        meti_mapping=["C03-R01"],
                        iso_mapping=["ISO-5.3"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="GOVERN-3",
                title="サプライチェーン・サードパーティ",
                description="AIサプライチェーンのリスクを管理する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="GOVERN-3.1",
                        title="サプライチェーンリスク管理",
                        description="AIサプライチェーン（データ提供者、モデル提供者等）のリスクを管理する。",
                        suggested_actions=[
                            "AI関連サプライヤーのデューデリジェンスを実施する",
                            "契約にAI品質・倫理要件を含める",
                            "サプライヤーのリスク評価を定期的に実施する",
                        ],
                        meti_mapping=["C07-R03"],
                        iso_mapping=["ISO-8.1"],
                    ),
                ],
            ),
        ],
    ),

    # ══════════════════════════════════════════════════════════════════
    # MAP — マッピング
    # ══════════════════════════════════════════════════════════════════
    NISTFunction(
        function_id="MAP",
        title="MAP（マッピング）",
        description=(
            "AIシステムの利用コンテキストを理解し、"
            "AIシステムに関するリスクを特定する。"
        ),
        categories=[
            NISTCategory(
                category_id="MAP-1",
                title="利用コンテキストの理解",
                description="AIシステムが使用されるコンテキストと利害関係者を理解する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MAP-1.1",
                        title="AIシステムの意図された用途の定義",
                        description="AIシステムの意図された用途と利害関係者を特定する。",
                        suggested_actions=[
                            "AIシステムの目的・用途を明確に文書化する",
                            "想定されるユーザーと影響を受ける人々を特定する",
                            "意図されない用途のリスクを評価する",
                        ],
                        meti_mapping=["C01-R01", "C06-R01"],
                        iso_mapping=["ISO-4.2", "ISO-6.1"],
                    ),
                    NISTSubcategory(
                        subcategory_id="MAP-1.2",
                        title="AIシステムの運用環境の特性",
                        description="AIシステムが運用される環境の特性を把握する。",
                        suggested_actions=[
                            "運用環境の技術的・社会的条件を分析する",
                            "環境の変化がAIシステムに与える影響を評価する",
                        ],
                        meti_mapping=["C02-R01"],
                        iso_mapping=["ISO-6.1"],
                    ),
                    NISTSubcategory(
                        subcategory_id="MAP-1.5",
                        title="AIシステムの限界の特定",
                        description="AIシステムの技術的限界と、それに伴うリスクを特定する。",
                        suggested_actions=[
                            "AIモデルの技術的限界を文書化する",
                            "限界に関する情報をユーザーに提供する",
                            "限界を超えた場合のフォールバック手順を定義する",
                        ],
                        meti_mapping=["C06-R02", "C06-R03"],
                        iso_mapping=["ISO-7.4"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MAP-2",
                title="リスクの特定",
                description="AIシステムに関するリスクを体系的に特定する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MAP-2.1",
                        title="AI固有のリスクの特定",
                        description="バイアス、ドリフト、敵対的攻撃等のAI固有のリスクを特定する。",
                        suggested_actions=[
                            "AI固有のリスクカテゴリ（バイアス、ドリフト、hallucination等）を定義する",
                            "各カテゴリのリスクシナリオを作成する",
                        ],
                        meti_mapping=["C02-R01", "C03-R01"],
                        iso_mapping=["ISO-6.1.2", "ISO-8.4"],
                    ),
                    NISTSubcategory(
                        subcategory_id="MAP-2.2",
                        title="プライバシー・セキュリティリスクの特定",
                        description="AIに関連するプライバシー・セキュリティリスクを特定する。",
                        suggested_actions=[
                            "個人情報の取扱いに関するリスクを評価する",
                            "敵対的攻撃、データポイズニング等のセキュリティリスクを分析する",
                        ],
                        meti_mapping=["C04-R02", "C05-R01"],
                        iso_mapping=["ISO-6.1.2"],
                    ),
                    NISTSubcategory(
                        subcategory_id="MAP-2.3",
                        title="社会的・倫理的リスクの特定",
                        description="AIの利用に関する社会的・倫理的リスクを特定する。",
                        suggested_actions=[
                            "人権への影響を評価する",
                            "雇用・社会的格差への影響を分析する",
                        ],
                        meti_mapping=["C01-R01", "C03-R01"],
                        iso_mapping=["ISO-8.4"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MAP-3",
                title="データ・入力の評価",
                description="AIシステムに使用されるデータと入力の品質を評価する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MAP-3.1",
                        title="学習データの品質評価",
                        description="学習データの代表性、バイアス、品質を評価する。",
                        suggested_actions=[
                            "データの出所・収集方法を文書化する",
                            "データの代表性・バイアスを評価する",
                            "データ品質指標を定義し測定する",
                        ],
                        meti_mapping=["C02-R02"],
                        iso_mapping=["ISO-6.1.2"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MAP-5",
                title="影響評価",
                description="AIシステムの影響を評価する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MAP-5.1",
                        title="影響のスコーピングと評価",
                        description="AIシステムの直接的・間接的影響を評価する。",
                        suggested_actions=[
                            "AIシステムの影響範囲を定義する",
                            "正の影響と負の影響の両方を評価する",
                            "影響評価結果をリスク管理に反映する",
                        ],
                        meti_mapping=["C01-R01", "C04-R02"],
                        iso_mapping=["ISO-8.4"],
                    ),
                ],
            ),
        ],
    ),

    # ══════════════════════════════════════════════════════════════════
    # MEASURE — 測定
    # ══════════════════════════════════════════════════════════════════
    NISTFunction(
        function_id="MEASURE",
        title="MEASURE（測定）",
        description=(
            "AIリスクを定量的・定性的に分析し、"
            "AIシステムの信頼性に関する情報を提供する。"
        ),
        categories=[
            NISTCategory(
                category_id="MEASURE-1",
                title="リスク測定アプローチ",
                description="AIリスクを測定するためのアプローチを確立する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MEASURE-1.1",
                        title="リスク測定の方法論",
                        description="AIリスクを測定するための定量的・定性的手法を確立する。",
                        suggested_actions=[
                            "AIリスクの定量的指標（精度、公平性メトリクス等）を定義する",
                            "リスク測定の方法論を文書化する",
                            "測定結果の解釈基準を設定する",
                        ],
                        meti_mapping=["C02-R01", "C03-R02"],
                        iso_mapping=["ISO-6.1", "ISO-8.2"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MEASURE-2",
                title="信頼性評価",
                description="AIシステムの信頼性に関する特性を評価する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MEASURE-2.1",
                        title="公平性の測定",
                        description="AIシステムの公平性に関する指標を測定する。",
                        suggested_actions=[
                            "公平性指標（統計的パリティ、均等機会等）を計算する",
                            "保護属性ごとの性能差を分析する",
                            "バイアス検出ツールを導入する",
                        ],
                        meti_mapping=["C03-R01", "C03-R02"],
                        iso_mapping=["ISO-6.1.2"],
                    ),
                    NISTSubcategory(
                        subcategory_id="MEASURE-2.2",
                        title="説明可能性・透明性の評価",
                        description="AIシステムの判断の説明可能性と透明性を評価する。",
                        suggested_actions=[
                            "説明可能AI（XAI）技術の適用可能性を評価する",
                            "利用者向けの説明の適切性をテストする",
                        ],
                        meti_mapping=["C06-R02"],
                        iso_mapping=[],
                    ),
                    NISTSubcategory(
                        subcategory_id="MEASURE-2.3",
                        title="セキュリティ・堅牢性の評価",
                        description="AIシステムのセキュリティと堅牢性を評価する。",
                        suggested_actions=[
                            "敵対的攻撃に対する堅牢性をテストする",
                            "入力の摂動に対するモデルの安定性を評価する",
                            "セキュリティ脆弱性スキャンを実施する",
                        ],
                        meti_mapping=["C05-R01", "C05-R02"],
                        iso_mapping=[],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MEASURE-3",
                title="モニタリング",
                description="AIシステムのパフォーマンスと信頼性を継続的にモニタリングする。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MEASURE-3.1",
                        title="継続的モニタリング",
                        description="AIシステムのパフォーマンスを継続的にモニタリングする。",
                        suggested_actions=[
                            "パフォーマンス指標のダッシュボードを構築する",
                            "データドリフト・概念ドリフトの検出機能を導入する",
                            "アラート閾値を設定し、異常時に通知する",
                        ],
                        meti_mapping=["C03-R02", "C07-R04"],
                        iso_mapping=["ISO-9.1", "ISO-9.2"],
                    ),
                ],
            ),
        ],
    ),

    # ══════════════════════════════════════════════════════════════════
    # MANAGE — 管理
    # ══════════════════════════════════════════════════════════════════
    NISTFunction(
        function_id="MANAGE",
        title="MANAGE（管理）",
        description=(
            "AIリスクに対する対応策を計画・実施し、"
            "リスクを許容可能なレベルに管理する。"
        ),
        categories=[
            NISTCategory(
                category_id="MANAGE-1",
                title="リスク対応の計画",
                description="AIリスクに対する対応策を計画する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MANAGE-1.1",
                        title="リスク対応の優先順位付け",
                        description="特定されたリスクに対する対応策の優先順位を決定する。",
                        suggested_actions=[
                            "リスクの影響度と発生確率に基づいて優先順位を付ける",
                            "リソースの制約を考慮した対応スケジュールを策定する",
                        ],
                        meti_mapping=["C02-R01"],
                        iso_mapping=["ISO-6.1", "ISO-8.1"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MANAGE-2",
                title="リスク対応の実施",
                description="AIリスクに対する対応策を実施する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MANAGE-2.1",
                        title="軽減策の実装",
                        description="AIリスクの軽減策を設計・実装する。",
                        suggested_actions=[
                            "技術的な軽減策（バイアス軽減、ドリフト対策等）を実装する",
                            "組織的な軽減策（プロセス、教育等）を実施する",
                        ],
                        meti_mapping=["C02-R03"],
                        iso_mapping=["ISO-6.1.3", "ISO-8.3"],
                    ),
                    NISTSubcategory(
                        subcategory_id="MANAGE-2.2",
                        title="インシデント対応計画",
                        description="AIインシデント発生時の対応計画を策定・維持する。",
                        suggested_actions=[
                            "AIインシデント対応計画を策定する",
                            "対応チームを編成し、役割を明確にする",
                            "定期的な訓練・演習を実施する",
                        ],
                        meti_mapping=["C05-R03"],
                        iso_mapping=["ISO-6.1.3"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MANAGE-3",
                title="リスク対応の検証",
                description="リスク対応策の有効性を検証する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MANAGE-3.1",
                        title="有効性の評価",
                        description="実施したリスク対応策の有効性を評価する。",
                        suggested_actions=[
                            "対応策の実施前後でリスクレベルを比較する",
                            "残留リスクを評価し、許容範囲内か確認する",
                        ],
                        meti_mapping=["C02-R01"],
                        iso_mapping=["ISO-10.1"],
                    ),
                ],
            ),
            NISTCategory(
                category_id="MANAGE-4",
                title="組織学習",
                description="AIリスク管理の経験から組織的に学習する。",
                subcategories=[
                    NISTSubcategory(
                        subcategory_id="MANAGE-4.1",
                        title="教訓の文書化と共有",
                        description="AIリスク管理の教訓を文書化し、組織全体で共有する。",
                        suggested_actions=[
                            "インシデント・課題のポストモーテムを実施する",
                            "教訓をナレッジベースに蓄積する",
                            "ベストプラクティスを組織横断で共有する",
                        ],
                        meti_mapping=["C10-R01"],
                        iso_mapping=["ISO-10.1", "ISO-10.2"],
                    ),
                ],
            ),
        ],
    ),
]


# ── ユーティリティ ────────────────────────────────────────────────

_FUNCTION_MAP: dict[str, NISTFunction] = {f.function_id: f for f in NIST_FUNCTIONS}

_SUBCATEGORY_MAP: dict[str, NISTSubcategory] = {}
for _func in NIST_FUNCTIONS:
    for _cat in _func.categories:
        for _sub in _cat.subcategories:
            _SUBCATEGORY_MAP[_sub.subcategory_id] = _sub


def get_nist_function(function_id: str) -> NISTFunction | None:
    """コア機能IDから機能を取得."""
    return _FUNCTION_MAP.get(function_id)


def get_nist_subcategory(subcategory_id: str) -> NISTSubcategory | None:
    """サブカテゴリIDからサブカテゴリを取得."""
    return _SUBCATEGORY_MAP.get(subcategory_id)


def all_nist_subcategories() -> list[NISTSubcategory]:
    """全サブカテゴリをフラットなリストで返す."""
    return list(_SUBCATEGORY_MAP.values())


def all_nist_subcategory_ids() -> list[str]:
    """全サブカテゴリIDのリスト."""
    return list(_SUBCATEGORY_MAP.keys())


def get_nist_to_meti_mapping() -> dict[str, list[str]]:
    """NISTサブカテゴリID -> METI要件IDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for sub in all_nist_subcategories():
        if sub.meti_mapping:
            mapping[sub.subcategory_id] = list(sub.meti_mapping)
    return mapping


def get_meti_to_nist_mapping() -> dict[str, list[str]]:
    """METI要件ID -> NISTサブカテゴリIDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for sub in all_nist_subcategories():
        for meti_id in sub.meti_mapping:
            mapping.setdefault(meti_id, []).append(sub.subcategory_id)
    return mapping


def get_nist_to_iso_mapping() -> dict[str, list[str]]:
    """NISTサブカテゴリID -> ISO要求事項IDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for sub in all_nist_subcategories():
        if sub.iso_mapping:
            mapping[sub.subcategory_id] = list(sub.iso_mapping)
    return mapping
