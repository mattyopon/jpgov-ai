# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""金融業ディープガイド.

金融業界固有のAIガバナンス要件を深く掘り下げる。
金融庁「AI利用に関する原則」、FSB報告書、SR 11-7（モデルリスク管理）、
バーゼル規制等との関連を網羅する。

出典:
- 金融庁「金融分野におけるAIの利用についてのディスカッションペーパー」(2024年)
- FSB "Artificial intelligence and machine learning in financial services" (2017)
- OCC SR 11-7 "Supervisory Guidance on Model Risk Management" (2011)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FinancialAIRisk:
    """金融業固有のAIリスクカテゴリ."""

    risk_id: str
    category: str
    title: str
    description: str
    regulatory_source: str
    meti_mapping: list[str] = field(default_factory=list)
    iso_mapping: list[str] = field(default_factory=list)
    specific_actions: list[str] = field(default_factory=list)
    inspection_points: list[str] = field(default_factory=list)
    case_study: str = ""


@dataclass(frozen=True)
class RegulatoryRequirement:
    """金融規制上のAI関連要件."""

    req_id: str
    regulation: str
    title: str
    description: str
    obligation_level: str  # mandatory / guideline / recommendation
    applicable_to: list[str] = field(default_factory=list)  # 銀行/証券/保険/...
    key_points: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FinancialAIUseCase:
    """金融業でのAI利用ユースケースとリスク."""

    use_case_id: str
    name: str
    description: str
    risk_level: str  # high / medium / low
    key_risks: list[str] = field(default_factory=list)
    required_controls: list[str] = field(default_factory=list)
    meti_requirements: list[str] = field(default_factory=list)


# ── 金融業固有のAIリスク ─────────────────────────────────

FINANCIAL_AI_RISKS: list[FinancialAIRisk] = [
    FinancialAIRisk(
        risk_id="FIN-RISK-01",
        category="モデルリスク",
        title="AIモデルの精度劣化・ドリフト",
        description=(
            "市場環境の変化や顧客行動の変化により、AIモデルの予測精度が劣化する。"
            "金融市場の急変時（リーマンショック級イベント等）にモデルが想定外の"
            "挙動を示すリスクがある。"
        ),
        regulatory_source="OCC SR 11-7, 金融庁DP",
        meti_mapping=["C02-R01", "C02-R03"],
        iso_mapping=["ISO-6.1.2", "ISO-8.2"],
        specific_actions=[
            "モデルパフォーマンスの継続的モニタリング体制の構築",
            "KPI閾値を定義し、閾値超過時の自動アラートを設定",
            "バックテスト（過去データでの検証）の定期実施",
            "ストレステスト（極端なシナリオでの検証）の実施",
            "モデル退役基準の定義",
        ],
        inspection_points=[
            "モデルの精度指標の推移データ",
            "閾値超過時のアクション記録",
            "バックテスト・ストレステストの結果",
        ],
        case_study=(
            "事例: 大手銀行のAI与信モデルがCOVID-19パンデミック時に精度が急落。"
            "通常時の学習データに含まれない行動パターン（一斉休業等）により、"
            "デフォルト予測が大幅にずれた。事前にストレステストシナリオに"
            "パンデミックを含めていなかったことが原因。"
        ),
    ),
    FinancialAIRisk(
        risk_id="FIN-RISK-02",
        category="データリスク",
        title="学習データのバイアス・品質劣化",
        description=(
            "歴史的なデータに含まれる差別的パターンをAIが学習してしまうリスク。"
            "例: 過去の融資データに性別・年齢等に基づく偏りがある場合、"
            "AIがその偏りを再現・増幅する。"
        ),
        regulatory_source="金融庁DP, FSB報告書",
        meti_mapping=["C02-R02", "C03-R01"],
        iso_mapping=["ISO-6.1.2", "ISO-8.4"],
        specific_actions=[
            "学習データのバイアス分析（保護属性ごとの分布確認）",
            "データリネージ（データの来歴・加工履歴）の管理",
            "データ品質スコアの定期測定",
            "バイアス緩和手法（再重み付け、合成データ生成等）の適用",
        ],
        inspection_points=[
            "学習データの属性別分布レポート",
            "バイアス評価の定量的結果",
            "データ品質管理プロセスの文書",
        ],
    ),
    FinancialAIRisk(
        risk_id="FIN-RISK-03",
        category="オペレーショナルリスク",
        title="AIシステムの障害・誤作動",
        description=(
            "AIシステムの障害がトレーディング損失、決済遅延、顧客サービス停止等の"
            "オペレーショナルリスクを引き起こす。アルゴリズム取引のフラッシュクラッシュ等。"
        ),
        regulatory_source="バーゼル規制, 金融庁DP",
        meti_mapping=["C02-R03", "C05-R03"],
        iso_mapping=["ISO-8.1", "ISO-10.1"],
        specific_actions=[
            "AIシステムのフォールバック手順の整備",
            "回路遮断機能（サーキットブレーカー）の実装",
            "AI判断の異常検知メカニズムの導入",
            "障害時のマニュアル切替手順の策定と訓練",
            "BCP（事業継続計画）へのAI障害シナリオの組み込み",
        ],
        inspection_points=[
            "フォールバック手順書",
            "障害訓練の実施記録",
            "BCPのAI関連シナリオ",
        ],
    ),
    FinancialAIRisk(
        risk_id="FIN-RISK-04",
        category="コンダクトリスク",
        title="AIによる不公正取引・顧客不利益",
        description=(
            "AIがアルゴリズム取引で市場操作的な行為を行うリスク。"
            "与信判断AIが特定の顧客層を不当に排除するリスク。"
            "保険引受AIが不公正な保険料設定を行うリスク。"
        ),
        regulatory_source="金融商品取引法, 保険業法, 金融庁DP",
        meti_mapping=["C03-R01", "C03-R02", "C03-R03"],
        iso_mapping=["ISO-8.4"],
        specific_actions=[
            "AI判断の公平性監査の定期実施",
            "顧客への不利益がないかの事後検証",
            "不公正取引検知のためのAI取引モニタリング",
            "顧客苦情のAI関連分析",
        ],
        inspection_points=[
            "公平性監査の結果レポート",
            "顧客苦情のAI関連分析結果",
            "不公正取引検知の実績",
        ],
        case_study=(
            "事例: 米国大手銀行のAIクレジットカード審査で、性別による与信限度額の"
            "格差が発覚。学習データに性別情報を直接使わなくても、"
            "配偶者の収入等の代理変数を通じて間接的な差別が生じていた。"
        ),
    ),
    FinancialAIRisk(
        risk_id="FIN-RISK-05",
        category="サイバーリスク",
        title="AI固有のサイバー攻撃",
        description=(
            "敵対的攻撃（Adversarial Attack）によるAI判断の操作、"
            "AIモデル自体の窃取、AIを利用した高度なフィッシング攻撃等。"
        ),
        regulatory_source="金融庁サイバーセキュリティガイドライン, FSB",
        meti_mapping=["C05-R01", "C05-R02"],
        iso_mapping=["ISO-8.3"],
        specific_actions=[
            "AI固有の脅威モデリング（STRIDE+AIカスタマイズ）",
            "敵対的攻撃に対するロバスト性テスト",
            "AIモデルの機密性保護（モデル窃取対策）",
            "AI利用のサイバー攻撃（ディープフェイク等）への対策",
            "AI Red Teamingの定期実施",
        ],
        inspection_points=[
            "AI脅威モデリングの結果",
            "ロバスト性テスト記録",
            "Red Teaming実施記録",
        ],
    ),
]


# ── 金融規制上のAI関連要件 ────────────────────────────────

FINANCIAL_REGULATORY_REQUIREMENTS: list[RegulatoryRequirement] = [
    RegulatoryRequirement(
        req_id="REG-FSA-01",
        regulation="金融庁「AI利用に関する原則」",
        title="AIガバナンス体制の整備",
        description="経営層の関与の下、AI利用に関するガバナンス体制を整備すること。",
        obligation_level="guideline",
        applicable_to=["銀行", "証券", "保険", "ノンバンク"],
        key_points=[
            "経営層のAIリスクへの理解と責任",
            "AIガバナンス委員会等の設置",
            "三線防御体制（1線: 開発、2線: リスク管理、3線: 内部監査）の構築",
        ],
    ),
    RegulatoryRequirement(
        req_id="REG-FSA-02",
        regulation="金融庁「AI利用に関する原則」",
        title="モデルリスク管理",
        description="AIモデルのリスクを適切に管理するための態勢を整備すること。",
        obligation_level="guideline",
        applicable_to=["銀行", "証券", "保険"],
        key_points=[
            "モデルインベントリ（台帳）の整備",
            "モデルバリデーション（独立した検証）の実施",
            "モデルの継続的モニタリング",
            "モデル変更管理プロセス",
        ],
    ),
    RegulatoryRequirement(
        req_id="REG-FSA-03",
        regulation="金融庁「AI利用に関する原則」",
        title="顧客保護・説明責任",
        description="AIによる判断が顧客に影響する場合の説明責任を果たすこと。",
        obligation_level="guideline",
        applicable_to=["銀行", "証券", "保険", "ノンバンク"],
        key_points=[
            "AI判断の根拠の説明可能性",
            "不利益を被った顧客への救済措置",
            "AIの限界についての顧客への情報提供",
        ],
    ),
    RegulatoryRequirement(
        req_id="REG-SR117-01",
        regulation="OCC SR 11-7 (米国)",
        title="モデルリスク管理フレームワーク",
        description=(
            "金融機関が使用する全モデル（AIモデルを含む）について、"
            "包括的なモデルリスク管理フレームワークを構築すること。"
        ),
        obligation_level="mandatory",
        applicable_to=["銀行（米国で事業展開する場合）"],
        key_points=[
            "モデルの開発・実装・利用・廃止の全ライフサイクル管理",
            "独立したモデルバリデーション",
            "モデルの利用制限・条件の管理",
            "モデルリスクの集約と経営層への報告",
        ],
    ),
    RegulatoryRequirement(
        req_id="REG-BASEL-01",
        regulation="バーゼル規制",
        title="AI利用時のオペレーショナルリスク管理",
        description=(
            "AIシステムの障害・誤作動に起因するオペレーショナルリスクを"
            "バーゼルIIIのオペレーショナルリスク枠組みに含めて管理すること。"
        ),
        obligation_level="mandatory",
        applicable_to=["銀行"],
        key_points=[
            "AI障害シナリオの損失見積もり",
            "AIに起因するオペレーショナルロスの記録",
            "リスク資本の適切な配賦",
        ],
    ),
    RegulatoryRequirement(
        req_id="REG-FSB-01",
        regulation="FSB「AI/MLの金融サービスにおける利用」",
        title="AI/MLの金融安定性への影響管理",
        description=(
            "AI/MLの利用が金融システムの安定性に影響を与えるリスクを"
            "認識し管理すること。"
        ),
        obligation_level="recommendation",
        applicable_to=["銀行", "証券", "保険"],
        key_points=[
            "AI/MLによる市場の同質化リスク",
            "AIの相互接続リスク",
            "AI利用の集中リスク（少数のAIベンダーへの依存）",
        ],
    ),
]


# ── 金融業でのAI利用ユースケース ─────────────────────────

FINANCIAL_AI_USE_CASES: list[FinancialAIUseCase] = [
    FinancialAIUseCase(
        use_case_id="FIN-UC-01",
        name="AI与信判断",
        description="個人・法人の与信審査にAIを利用。スコアリングモデル、デフォルト予測等。",
        risk_level="high",
        key_risks=[
            "差別的与信判断のリスク",
            "説明可能性の欠如",
            "データバイアスの影響",
            "モデルドリフトによる精度劣化",
        ],
        required_controls=[
            "公平性評価（保護属性ごとの承認率分析）",
            "説明可能なAI手法の採用またはXAI補助ツール",
            "独立したモデルバリデーション",
            "月次の精度モニタリング",
            "顧客への審査結果の説明プロセス",
        ],
        meti_requirements=["C02-R01", "C03-R01", "C06-R02"],
    ),
    FinancialAIUseCase(
        use_case_id="FIN-UC-02",
        name="アルゴリズム取引",
        description="AIを用いた自動売買。HFT、マーケットメイキング等。",
        risk_level="high",
        key_risks=[
            "フラッシュクラッシュの誘発",
            "市場操作と誤認されるリスク",
            "想定外の大量損失",
            "規制違反（金融商品取引法）",
        ],
        required_controls=[
            "取引量・損失のリアルタイム監視",
            "サーキットブレーカーの実装",
            "取引ロジックの事前審査",
            "バックテスト・ストレステスト",
            "監視部門による独立したモニタリング",
        ],
        meti_requirements=["C02-R01", "C02-R03", "C05-R01"],
    ),
    FinancialAIUseCase(
        use_case_id="FIN-UC-03",
        name="不正検知AI",
        description="マネーロンダリング、不正取引、保険金不正請求の検知にAIを利用。",
        risk_level="high",
        key_risks=[
            "偽陽性（正常取引の誤検知）による顧客不便",
            "偽陰性（不正取引の見逃し）による規制違反",
            "攻撃者によるAI回避手法",
        ],
        required_controls=[
            "検知精度のKPI（精度、再現率、F1スコア）の継続的モニタリング",
            "閾値の定期見直し",
            "人間の調査員によるレビュー体制",
            "新たな不正手口への対応（モデル更新プロセス）",
        ],
        meti_requirements=["C02-R01", "C05-R01", "C01-R02"],
    ),
    FinancialAIUseCase(
        use_case_id="FIN-UC-04",
        name="顧客対応チャットボット",
        description="顧客からの問い合わせにAIチャットボットが自動応答。",
        risk_level="medium",
        key_risks=[
            "ハルシネーション（虚偽情報の提供）",
            "不適切なアドバイス（投資助言に該当するリスク）",
            "個人情報の不適切な取扱い",
        ],
        required_controls=[
            "投資助言に該当しないよう回答範囲の制限",
            "事実確認メカニズム（RAG等）の導入",
            "個人情報入力の制限・マスキング",
            "エスカレーションルール（人間対応への切替）",
        ],
        meti_requirements=["C01-R03", "C04-R01", "C06-R01"],
    ),
    FinancialAIUseCase(
        use_case_id="FIN-UC-05",
        name="保険引受AI",
        description="保険の引受可否判断や保険料算出にAIを利用。",
        risk_level="high",
        key_risks=[
            "差別的な保険料設定",
            "説明不能な引受拒否",
            "過剰な保険料請求",
        ],
        required_controls=[
            "保護属性に基づく差別がないかの公平性監査",
            "引受拒否理由の説明可能性",
            "アクチュアリーによる独立検証",
            "保険料算出ロジックの透明性確保",
        ],
        meti_requirements=["C03-R01", "C06-R02"],
    ),
]


# ── 金融庁検査で問われるポイント ──────────────────────────

INSPECTION_FOCUS_AREAS: list[dict[str, str]] = [
    {
        "area": "AIガバナンス態勢",
        "key_question": "AIの利用に関するガバナンス方針は策定されているか。経営層は関与しているか。",
        "expected_evidence": "AI方針書（経営層承認済み）、AIガバナンス委員会の議事録",
    },
    {
        "area": "モデルリスク管理",
        "key_question": "AIモデルのインベントリは整備されているか。独立したモデルバリデーションは実施されているか。",
        "expected_evidence": "モデル台帳、バリデーション報告書、モデル監視レポート",
    },
    {
        "area": "公平性・非差別",
        "key_question": "AI判断に不当な差別がないか検証しているか。バイアス評価を定期的に実施しているか。",
        "expected_evidence": "バイアス評価結果、公平性監査レポート、是正措置記録",
    },
    {
        "area": "説明可能性",
        "key_question": "顧客に対してAI判断の根拠を説明できるか。説明の仕組みは整備されているか。",
        "expected_evidence": "説明可能性の方針書、顧客向け説明資料のサンプル、説明要求への対応記録",
    },
    {
        "area": "データ管理",
        "key_question": "学習データの品質管理は適切か。データの来歴・加工履歴は追跡可能か。",
        "expected_evidence": "データ品質管理手順書、データリネージ、品質チェック結果",
    },
    {
        "area": "インシデント対応",
        "key_question": "AI関連のインシデント対応手順は整備されているか。過去のインシデントの対応は適切だったか。",
        "expected_evidence": "インシデント対応手順書、インシデント対応記録、RCA（根本原因分析）",
    },
    {
        "area": "外部委託管理",
        "key_question": "外部AIベンダーの管理は適切か。ベンダーリスクを評価しているか。",
        "expected_evidence": "ベンダー評価シート、契約書のAI関連条項、SLA監視記録",
    },
]


# ── ユーティリティ ────────────────────────────────────────

def get_financial_risks() -> list[FinancialAIRisk]:
    """金融業固有のAIリスク一覧を取得."""
    return list(FINANCIAL_AI_RISKS)


def get_financial_risk(risk_id: str) -> FinancialAIRisk | None:
    """リスクIDからリスクを取得."""
    for r in FINANCIAL_AI_RISKS:
        if r.risk_id == risk_id:
            return r
    return None


def get_financial_regulatory_requirements() -> list[RegulatoryRequirement]:
    """金融規制上のAI関連要件を取得."""
    return list(FINANCIAL_REGULATORY_REQUIREMENTS)


def get_financial_use_cases() -> list[FinancialAIUseCase]:
    """金融業でのAI利用ユースケースを取得."""
    return list(FINANCIAL_AI_USE_CASES)


def get_inspection_focus_areas() -> list[dict[str, str]]:
    """金融庁検査の重点ポイントを取得."""
    return list(INSPECTION_FOCUS_AREAS)


def get_requirement_deep_guide(meti_req_id: str) -> dict[str, list[str]] | None:
    """METI要件IDに対する金融業固有のディープガイドを取得.

    Args:
        meti_req_id: METI要件ID (例: "C02-R01")

    Returns:
        関連するリスク、規制要件、ユースケースのサマリー。なければNone。
    """
    risks = [r for r in FINANCIAL_AI_RISKS if meti_req_id in r.meti_mapping]
    regs = [r for r in FINANCIAL_REGULATORY_REQUIREMENTS
            for kp in r.key_points if meti_req_id in "".join(r.key_points)]
    use_cases = [u for u in FINANCIAL_AI_USE_CASES if meti_req_id in u.meti_requirements]

    if not risks and not use_cases:
        return None

    return {
        "related_risks": [f"{r.risk_id}: {r.title}" for r in risks],
        "specific_actions": [a for r in risks for a in r.specific_actions],
        "inspection_points": [p for r in risks for p in r.inspection_points],
        "related_use_cases": [f"{u.use_case_id}: {u.name} ({u.risk_level})" for u in use_cases],
    }
