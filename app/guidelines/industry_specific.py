# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""業種別AIガバナンスガイドライン定義.

業種ごとに追加で準拠すべきガイドラインと要件を定義する。

| 業種   | 追加ガイドライン |
|--------|----------------|
| 金融   | 金融庁「AI利用に関する原則」、FSB AI/ML報告書 |
| 医療   | PMDA「AI活用の考え方」、FDA AI/ML-SaMD |
| 自動車 | 自動運転AI安全ガイドライン |
| 人事   | 厚労省「AI等を活用した採用活動に関する留意事項」|
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IndustryRequirement:
    """業種別要件."""

    req_id: str
    title: str
    description: str
    source: str  # 出典ガイドライン名
    obligation_type: str = "guideline"  # "mandatory" / "guideline" / "recommendation"
    meti_mapping: list[str] = field(default_factory=list)
    iso_mapping: list[str] = field(default_factory=list)
    check_questions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IndustryGuideline:
    """業種別ガイドライン."""

    guideline_id: str
    industry: str
    title: str
    issuer: str  # 発行機関
    description: str
    reference_url: str = ""
    requirements: list[IndustryRequirement] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 金融業界
# ---------------------------------------------------------------------------

FINANCIAL_GUIDELINES: list[IndustryGuideline] = [
    IndustryGuideline(
        guideline_id="FIN-FSA",
        industry="financial",
        title="AI利用に関する原則",
        issuer="金融庁",
        description="金融機関によるAI利用に関する原則。リスク管理、説明可能性、公平性等を定める。",
        reference_url="https://www.fsa.go.jp/",
        requirements=[
            IndustryRequirement(
                req_id="FIN-01",
                title="AI利用のガバナンス体制",
                description="金融機関のAI利用に関するガバナンス体制を整備し、経営層の関与を確保すること。",
                source="金融庁 AI利用に関する原則",
                obligation_type="guideline",
                meti_mapping=["C07-R01", "C07-R02"],
                iso_mapping=["ISO-5.1", "ISO-5.3"],
                check_questions=[
                    "AI利用に関するガバナンス委員会等の体制は整備されていますか？",
                    "AIリスクに関する経営層への定期報告体制がありますか？",
                ],
            ),
            IndustryRequirement(
                req_id="FIN-02",
                title="AI利用のリスク管理",
                description="AI利用に関するリスクを特定・評価・管理するためのリスク管理体制を整備すること。モデルリスク管理を含む。",
                source="金融庁 AI利用に関する原則",
                obligation_type="guideline",
                meti_mapping=["C02-R01", "C02-R03"],
                iso_mapping=["ISO-6.1", "ISO-6.1.2"],
                check_questions=[
                    "AI/MLモデルのリスク管理ポリシーは策定されていますか？",
                    "モデルバリデーション（独立した検証）のプロセスがありますか？",
                    "モデルインベントリ（台帳）は整備されていますか？",
                ],
            ),
            IndustryRequirement(
                req_id="FIN-03",
                title="顧客への説明責任",
                description="AIを用いた判断（与信、保険引受等）について、顧客に対して適切に説明できる体制を整備すること。",
                source="金融庁 AI利用に関する原則",
                obligation_type="guideline",
                meti_mapping=["C06-R01", "C06-R02"],
                iso_mapping=["ISO-7.4"],
                check_questions=[
                    "AI判断の根拠を顧客に説明できる仕組みがありますか？",
                    "説明の粒度は顧客の理解度に合わせて調整されていますか？",
                ],
            ),
            IndustryRequirement(
                req_id="FIN-04",
                title="公平性・非差別",
                description="AIを用いた審査・判定において、不当な差別が生じないよう管理すること。",
                source="金融庁 AI利用に関する原則",
                obligation_type="guideline",
                meti_mapping=["C03-R01", "C03-R02"],
                iso_mapping=["ISO-8.4"],
                check_questions=[
                    "与信・保険引受等でのAI判断にバイアス評価を実施していますか？",
                    "保護属性（性別、年齢、人種等）に基づく不当な差別がないか検証していますか？",
                ],
            ),
            IndustryRequirement(
                req_id="FIN-05",
                title="不正利用対策",
                description="AIシステムが金融犯罪（マネーロンダリング、不正取引等）の防止に寄与し、また悪用されないよう対策を講じること。",
                source="金融庁 AI利用に関する原則",
                obligation_type="guideline",
                meti_mapping=["C05-R01"],
                iso_mapping=["ISO-8.3"],
                check_questions=[
                    "AI利用による不正取引検知の精度をモニタリングしていますか？",
                    "AIシステム自体の悪用リスクを評価していますか？",
                ],
            ),
        ],
    ),
    IndustryGuideline(
        guideline_id="FIN-FSB",
        industry="financial",
        title="AI/MLに関する報告書",
        issuer="FSB (Financial Stability Board)",
        description="金融安定理事会によるAI/MLの金融サービスにおける利用に関するレポート。規制上の考慮事項を含む。",
        reference_url="https://www.fsb.org/",
        requirements=[
            IndustryRequirement(
                req_id="FIN-FSB-01",
                title="モデルリスク管理の強化",
                description="AI/MLモデルの検証可能性を確保し、モデルリスク管理フレームワークを強化すること。",
                source="FSB AI/ML報告書",
                obligation_type="recommendation",
                meti_mapping=["C02-R01"],
                iso_mapping=["ISO-6.1.2"],
                check_questions=[
                    "AI/MLモデルのモデルリスク管理フレームワークはありますか？",
                    "モデルの説明可能性の限界を認識し対応していますか？",
                ],
            ),
            IndustryRequirement(
                req_id="FIN-FSB-02",
                title="データ品質とバイアス管理",
                description="学習データの品質を確保し、バイアスの検出・軽減を行うこと。",
                source="FSB AI/ML報告書",
                obligation_type="recommendation",
                meti_mapping=["C02-R02", "C03-R01"],
                iso_mapping=["ISO-6.1.2"],
            ),
        ],
    ),
]

# ---------------------------------------------------------------------------
# 医療業界
# ---------------------------------------------------------------------------

HEALTHCARE_GUIDELINES: list[IndustryGuideline] = [
    IndustryGuideline(
        guideline_id="MED-PMDA",
        industry="healthcare",
        title="AIを活用した医療機器等に関する考え方",
        issuer="PMDA（独立行政法人 医薬品医療機器総合機構）",
        description="AIを搭載した医療機器のプログラム（SaMD）の規制に関する考え方。継続的学習のリスク管理を含む。",
        reference_url="https://www.pmda.go.jp/",
        requirements=[
            IndustryRequirement(
                req_id="MED-01",
                title="臨床的有効性・安全性の確認",
                description="AIを搭載した医療機器の臨床的有効性と安全性を科学的に確認すること。",
                source="PMDA AIを活用した医療機器等に関する考え方",
                obligation_type="mandatory",
                meti_mapping=["C02-R01"],
                iso_mapping=["ISO-6.1.2"],
                check_questions=[
                    "臨床性能試験の計画と結果は文書化されていますか？",
                    "AIの判断精度（感度・特異度等）は臨床的に許容範囲ですか？",
                ],
            ),
            IndustryRequirement(
                req_id="MED-02",
                title="継続的学習の管理",
                description="AIモデルが市場投入後も継続的に学習する場合、その変更管理プロセスを確立すること。",
                source="PMDA AIを活用した医療機器等に関する考え方",
                obligation_type="mandatory",
                meti_mapping=["C02-R03"],
                iso_mapping=["ISO-8.1"],
                check_questions=[
                    "継続学習によるモデル更新の変更管理プロセスがありますか？",
                    "性能の大幅な変化時に再審査を受ける基準がありますか？",
                ],
            ),
            IndustryRequirement(
                req_id="MED-03",
                title="学習データの品質管理",
                description="医療AIの学習に使用するデータの品質、代表性、偏りを管理すること。",
                source="PMDA AIを活用した医療機器等に関する考え方",
                obligation_type="mandatory",
                meti_mapping=["C02-R02"],
                iso_mapping=["ISO-6.1.2"],
                check_questions=[
                    "学習データの出所・収集方法・品質は文書化されていますか？",
                    "データの人口統計学的代表性は評価されていますか？",
                ],
            ),
            IndustryRequirement(
                req_id="MED-04",
                title="医療従事者への情報提供",
                description="AIの判断根拠、限界、適用範囲を医療従事者に適切に情報提供すること。",
                source="PMDA AIを活用した医療機器等に関する考え方",
                obligation_type="mandatory",
                meti_mapping=["C06-R01", "C06-R02"],
                iso_mapping=["ISO-7.4"],
                check_questions=[
                    "医療従事者向けの添付文書・利用マニュアルにAIの限界が記載されていますか？",
                    "AIの判断を過度に信頼しないよう注意喚起していますか？",
                ],
            ),
        ],
    ),
    IndustryGuideline(
        guideline_id="MED-FDA",
        industry="healthcare",
        title="AI/ML-Based Software as a Medical Device (SaMD)",
        issuer="FDA (米国食品医薬品局)",
        description="AIを活用したSaMDに関する規制の考え方。TPLC（Total Product Lifecycle）アプローチを提唱。",
        reference_url="https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-and-machine-learning-aiml-software-medical-device",
        requirements=[
            IndustryRequirement(
                req_id="MED-FDA-01",
                title="Good Machine Learning Practice (GMLP)",
                description="機械学習のベストプラクティスに基づく開発プロセスを確立すること。",
                source="FDA AI/ML-SaMD",
                obligation_type="guideline",
                meti_mapping=["C02-R02"],
                iso_mapping=["ISO-8.1"],
                check_questions=[
                    "GMLPに基づいた開発プロセスが確立されていますか？",
                ],
            ),
            IndustryRequirement(
                req_id="MED-FDA-02",
                title="TPLC（Total Product Lifecycle）アプローチ",
                description="市場投入前の安全性評価に加え、市場投入後の継続的な性能モニタリングを行うこと。",
                source="FDA AI/ML-SaMD",
                obligation_type="guideline",
                meti_mapping=["C03-R02", "C07-R04"],
                iso_mapping=["ISO-9.1"],
            ),
        ],
    ),
]

# ---------------------------------------------------------------------------
# 自動車業界
# ---------------------------------------------------------------------------

AUTOMOTIVE_GUIDELINES: list[IndustryGuideline] = [
    IndustryGuideline(
        guideline_id="AUTO-MLIT",
        industry="automotive",
        title="自動運転車の安全技術ガイドライン",
        issuer="国土交通省",
        description="自動運転車（レベル3以上）の安全性確保のためのガイドライン。",
        reference_url="https://www.mlit.go.jp/",
        requirements=[
            IndustryRequirement(
                req_id="AUTO-01",
                title="安全性確認プロセス",
                description="自動運転AIの安全性を確認するための体系的なプロセス（シミュレーション、テストコース、公道実証）を実施すること。",
                source="国土交通省 自動運転車の安全技術ガイドライン",
                obligation_type="guideline",
                meti_mapping=["C02-R01", "C02-R03"],
                iso_mapping=["ISO-6.1.2", "ISO-8.3"],
                check_questions=[
                    "シミュレーション・テストコース・公道実証の段階的テスト計画がありますか？",
                    "ODD（Operational Design Domain）は明確に定義されていますか？",
                ],
            ),
            IndustryRequirement(
                req_id="AUTO-02",
                title="サイバーセキュリティ対策",
                description="車載AIシステムに対するサイバーセキュリティ対策を講じること。",
                source="国土交通省 自動運転車の安全技術ガイドライン",
                obligation_type="guideline",
                meti_mapping=["C05-R01", "C05-R02"],
                iso_mapping=["ISO-8.3"],
                check_questions=[
                    "車載AIに対する脅威分析は実施していますか？",
                    "OTA（Over-the-Air）更新のセキュリティは確保されていますか？",
                ],
            ),
            IndustryRequirement(
                req_id="AUTO-03",
                title="データ記録・保存",
                description="事故発生時の原因分析のために、自動運転AIの判断記録を保存すること。",
                source="国土交通省 自動運転車の安全技術ガイドライン",
                obligation_type="guideline",
                meti_mapping=["C07-R04"],
                iso_mapping=["ISO-7.5"],
                check_questions=[
                    "自動運転AIの判断ログ（センサデータ、判断根拠等）は記録・保存されていますか？",
                    "データの保存期間は法令に準拠していますか？",
                ],
            ),
            IndustryRequirement(
                req_id="AUTO-04",
                title="人間への制御権移譲",
                description="自動運転から人間の運転への安全な制御権移譲を確保すること。",
                source="国土交通省 自動運転車の安全技術ガイドライン",
                obligation_type="guideline",
                meti_mapping=["C01-R02"],
                iso_mapping=["ISO-8.4"],
                check_questions=[
                    "Minimum Risk Condition（最小リスク状態）への遷移手順が定義されていますか？",
                    "ドライバーへの制御権移譲の通知・猶予時間は適切ですか？",
                ],
            ),
        ],
    ),
]

# ---------------------------------------------------------------------------
# 人事（HR）業界
# ---------------------------------------------------------------------------

HR_GUIDELINES: list[IndustryGuideline] = [
    IndustryGuideline(
        guideline_id="HR-MHLW",
        industry="hr",
        title="AI等を活用した採用活動に関する留意事項",
        issuer="厚生労働省",
        description="AIを活用した採用選考における公平性確保・プライバシー保護に関する留意事項。",
        reference_url="https://www.mhlw.go.jp/",
        requirements=[
            IndustryRequirement(
                req_id="HR-01",
                title="採用AIの公平性確保",
                description="AIを用いた採用選考において、性別・年齢・障害・国籍等による不当な差別が生じないよう、バイアス評価を実施すること。",
                source="厚労省 AI等を活用した採用活動に関する留意事項",
                obligation_type="guideline",
                meti_mapping=["C03-R01", "C03-R02"],
                iso_mapping=["ISO-8.4"],
                check_questions=[
                    "採用AIにバイアス評価を実施していますか？",
                    "保護属性（性別、年齢、障害等）に基づく差別がないか検証していますか？",
                    "バイアスが検出された場合の是正手順がありますか？",
                ],
            ),
            IndustryRequirement(
                req_id="HR-02",
                title="応募者への情報提供",
                description="AIを採用選考に利用していることを応募者に適切に通知し、AI判断の概要を説明すること。",
                source="厚労省 AI等を活用した採用活動に関する留意事項",
                obligation_type="guideline",
                meti_mapping=["C06-R01", "C06-R02"],
                iso_mapping=["ISO-7.4"],
                check_questions=[
                    "採用プロセスでのAI利用を応募者に通知していますか？",
                    "AI判断に不服がある場合の申立て手段がありますか？",
                ],
            ),
            IndustryRequirement(
                req_id="HR-03",
                title="個人情報の適正な取扱い",
                description="採用AIで収集・利用する個人情報について、職業安定法及び個人情報保護法に基づく適正な取扱いを行うこと。",
                source="厚労省 AI等を活用した採用活動に関する留意事項",
                obligation_type="guideline",
                meti_mapping=["C04-R01", "C04-R02", "C04-R03"],
                iso_mapping=["ISO-8.4"],
                check_questions=[
                    "採用AIで収集するデータの範囲は必要最小限ですか？",
                    "SNS情報等の収集について適法性を確認していますか？",
                    "不採用者のデータ削除ポリシーは策定されていますか？",
                ],
            ),
            IndustryRequirement(
                req_id="HR-04",
                title="最終判断における人間の関与",
                description="AIによる評価結果を参考としつつ、最終的な採否の判断は人間が行うこと。",
                source="厚労省 AI等を活用した採用活動に関する留意事項",
                obligation_type="guideline",
                meti_mapping=["C01-R02"],
                iso_mapping=["ISO-8.4"],
                check_questions=[
                    "採用の最終判断に人間が関与するプロセスがありますか？",
                    "AI判断を覆す権限を持つ担当者が明確ですか？",
                ],
            ),
        ],
    ),
]


# ── 全業種統合 ────────────────────────────────────────────────────

ALL_INDUSTRY_GUIDELINES: list[IndustryGuideline] = (
    FINANCIAL_GUIDELINES + HEALTHCARE_GUIDELINES + AUTOMOTIVE_GUIDELINES + HR_GUIDELINES
)

SUPPORTED_INDUSTRIES: list[str] = ["financial", "healthcare", "automotive", "hr"]


# ── ユーティリティ ────────────────────────────────────────────────

_GUIDELINE_MAP: dict[str, IndustryGuideline] = {
    g.guideline_id: g for g in ALL_INDUSTRY_GUIDELINES
}

_REQ_MAP: dict[str, IndustryRequirement] = {}
for _g in ALL_INDUSTRY_GUIDELINES:
    for _r in _g.requirements:
        _REQ_MAP[_r.req_id] = _r


def get_industry_guidelines(industry: str) -> list[IndustryGuideline]:
    """業種名から該当するガイドライン一覧を取得."""
    return [g for g in ALL_INDUSTRY_GUIDELINES if g.industry == industry]


def get_guideline(guideline_id: str) -> IndustryGuideline | None:
    """ガイドラインIDからガイドラインを取得."""
    return _GUIDELINE_MAP.get(guideline_id)


def get_industry_requirement(req_id: str) -> IndustryRequirement | None:
    """要件IDから業種別要件を取得."""
    return _REQ_MAP.get(req_id)


def all_industry_requirements() -> list[IndustryRequirement]:
    """全業種別要件をフラットなリストで返す."""
    return list(_REQ_MAP.values())


def all_industry_requirement_ids() -> list[str]:
    """全業種別要件IDのリスト."""
    return list(_REQ_MAP.keys())


def get_industry_to_meti_mapping(industry: str) -> dict[str, list[str]]:
    """特定業種の要件ID -> METI要件IDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for g in get_industry_guidelines(industry):
        for r in g.requirements:
            if r.meti_mapping:
                mapping[r.req_id] = list(r.meti_mapping)
    return mapping


def get_industry_check_questions(industry: str) -> list[dict[str, str]]:
    """業種別のチェック質問一覧を取得."""
    result: list[dict[str, str]] = []
    for g in get_industry_guidelines(industry):
        for r in g.requirements:
            for q in r.check_questions:
                result.append({
                    "req_id": r.req_id,
                    "guideline": g.title,
                    "question": q,
                })
    return result
