# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""AI推進法（2025年6月施行）要件定義.

「AI推進基本法」（正式名称: 人工知能関連技術の研究開発及び活用の推進に関する法律）
2025年6月施行。AI活用の推進と安全性確保の両立を目指す日本の基本法。

本ファイルはAI推進法の主要な義務・努力義務項目と、
METI AI事業者ガイドライン及びISO 42001とのクロスマッピングを定義する。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActRequirement:
    """AI推進法の個別要件."""

    req_id: str  # e.g., "APA-01"
    article: str  # 条文番号
    title: str
    description: str
    obligation_type: str = "effort"  # "mandatory" / "effort" (義務/努力義務)
    meti_mapping: list[str] = field(default_factory=list)
    iso_mapping: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ActChapter:
    """AI推進法の章."""

    chapter_id: str
    title: str
    description: str
    requirements: list[ActRequirement] = field(default_factory=list)


# ---------------------------------------------------------------------------
# AI推進法 要件定義
# ---------------------------------------------------------------------------

ACT_CHAPTERS: list[ActChapter] = [
    # ── 第1章: 総則 ──
    ActChapter(
        chapter_id="CH1",
        title="総則",
        description="法律の目的、基本理念、定義等。",
        requirements=[
            ActRequirement(
                req_id="APA-01",
                article="第3条",
                title="基本理念の遵守",
                description="AI関連技術の研究開発・活用にあたり、人間の尊厳の尊重、多様性の確保、持続可能な社会の実現等の基本理念を遵守すること。",
                obligation_type="mandatory",
                meti_mapping=["C01-R01"],
                iso_mapping=["ISO-5.2"],
            ),
        ],
    ),

    # ── 第2章: AI推進基本方針 ──
    ActChapter(
        chapter_id="CH2",
        title="AI推進基本方針",
        description="政府によるAI推進基本方針の策定。事業者の役割と責務。",
        requirements=[
            ActRequirement(
                req_id="APA-02",
                article="第10条",
                title="事業者の責務（安全性確保）",
                description="AI事業者は、AIシステムの安全性を確保するために必要な措置を講じるよう努めること。",
                obligation_type="effort",
                meti_mapping=["C02-R01", "C02-R03"],
                iso_mapping=["ISO-6.1", "ISO-8.3"],
            ),
            ActRequirement(
                req_id="APA-03",
                article="第10条",
                title="事業者の責務（透明性確保）",
                description="AIの利用に関する透明性を確保し、利害関係者に対して適切な情報提供を行うよう努めること。",
                obligation_type="effort",
                meti_mapping=["C06-R01", "C06-R02"],
                iso_mapping=["ISO-7.4"],
            ),
            ActRequirement(
                req_id="APA-04",
                article="第10条",
                title="事業者の責務（公平性確保）",
                description="AIの利用に際し、不当な差別が生じないよう配慮すること。",
                obligation_type="effort",
                meti_mapping=["C03-R01", "C03-R02"],
                iso_mapping=["ISO-8.4"],
            ),
        ],
    ),

    # ── 第3章: 安全・安心の確保 ──
    ActChapter(
        chapter_id="CH3",
        title="安全・安心の確保",
        description="高リスクAIに対する安全性の確保措置。",
        requirements=[
            ActRequirement(
                req_id="APA-05",
                article="第15条",
                title="リスク管理体制の整備",
                description="特定AI（高リスクAI）を取り扱う事業者は、リスク管理体制を整備し、定期的にリスク評価を行うこと。",
                obligation_type="mandatory",
                meti_mapping=["C02-R01", "C02-R02"],
                iso_mapping=["ISO-6.1.2", "ISO-8.2"],
            ),
            ActRequirement(
                req_id="APA-06",
                article="第16条",
                title="個人情報等の適正な取扱い",
                description="AI利用における個人情報の取扱いについて、個人情報保護法に加え、AI固有のリスクに対応する措置を講じること。",
                obligation_type="mandatory",
                meti_mapping=["C04-R01", "C04-R02", "C04-R03"],
                iso_mapping=["ISO-8.4"],
            ),
            ActRequirement(
                req_id="APA-07",
                article="第17条",
                title="セキュリティ対策の実施",
                description="AIシステムに対するサイバーセキュリティ対策を実施し、脆弱性の管理とインシデント対応体制を整備すること。",
                obligation_type="mandatory",
                meti_mapping=["C05-R01", "C05-R02", "C05-R03"],
                iso_mapping=["ISO-8.3"],
            ),
            ActRequirement(
                req_id="APA-08",
                article="第18条",
                title="インシデント報告義務",
                description="重大なAIインシデントが発生した場合、所管大臣に報告すること。",
                obligation_type="mandatory",
                meti_mapping=["C05-R03"],
                iso_mapping=["ISO-10.1"],
            ),
        ],
    ),

    # ── 第4章: 人材育成・リテラシー ──
    ActChapter(
        chapter_id="CH4",
        title="人材育成・リテラシー",
        description="AI人材の育成とAIリテラシーの向上。",
        requirements=[
            ActRequirement(
                req_id="APA-09",
                article="第22条",
                title="AI人材の育成",
                description="従業員に対してAIの適切な利用に関する教育・研修を実施すること。",
                obligation_type="effort",
                meti_mapping=["C08-R01"],
                iso_mapping=["ISO-7.2", "ISO-7.3"],
            ),
            ActRequirement(
                req_id="APA-10",
                article="第23条",
                title="AIリテラシーの向上",
                description="AIサービスの利用者に対して、適切な利用方法等の情報提供を行うこと。",
                obligation_type="effort",
                meti_mapping=["C08-R02"],
                iso_mapping=["ISO-7.3"],
            ),
        ],
    ),

    # ── 第5章: ガバナンス ──
    ActChapter(
        chapter_id="CH5",
        title="ガバナンス",
        description="AI利活用に関するガバナンス体制の整備。",
        requirements=[
            ActRequirement(
                req_id="APA-11",
                article="第28条",
                title="AIガバナンス体制の整備",
                description="AIの開発・提供・利用に関するガバナンス体制を整備し、内部統制を確保すること。",
                obligation_type="effort",
                meti_mapping=["C07-R01", "C07-R02"],
                iso_mapping=["ISO-5.1", "ISO-5.3"],
            ),
            ActRequirement(
                req_id="APA-12",
                article="第29条",
                title="記録の保持・監査対応",
                description="AIシステムの運用記録を適切に保持し、監査に対応できる体制を整備すること。",
                obligation_type="effort",
                meti_mapping=["C07-R04"],
                iso_mapping=["ISO-7.5", "ISO-9.2"],
            ),
        ],
    ),

    # ── 第6章: イノベーション推進 ──
    ActChapter(
        chapter_id="CH6",
        title="イノベーション推進",
        description="AI技術の研究開発及び活用の推進。",
        requirements=[
            ActRequirement(
                req_id="APA-13",
                article="第32条",
                title="知的財産権の保護",
                description="AI開発・利用における知的財産権の保護に配慮すること。",
                obligation_type="effort",
                meti_mapping=["C09-R02"],
                iso_mapping=[],
            ),
            ActRequirement(
                req_id="APA-14",
                article="第33条",
                title="公正競争の確保",
                description="AI利活用における公正な競争環境の維持に努めること。",
                obligation_type="effort",
                meti_mapping=["C09-R01"],
                iso_mapping=[],
            ),
            ActRequirement(
                req_id="APA-15",
                article="第35条",
                title="国際連携・相互運用性",
                description="国際的なAIガバナンスの枠組みとの整合性を確保し、相互運用性に配慮すること。",
                obligation_type="effort",
                meti_mapping=["C10-R02"],
                iso_mapping=[],
            ),
        ],
    ),
]


# ── ユーティリティ ────────────────────────────────────────────────

_CHAPTER_MAP: dict[str, ActChapter] = {c.chapter_id: c for c in ACT_CHAPTERS}
_REQ_MAP: dict[str, ActRequirement] = {
    r.req_id: r for c in ACT_CHAPTERS for r in c.requirements
}


def get_act_chapter(chapter_id: str) -> ActChapter | None:
    """章IDから章を取得."""
    return _CHAPTER_MAP.get(chapter_id)


def get_act_requirement(req_id: str) -> ActRequirement | None:
    """要件IDから要件を取得."""
    return _REQ_MAP.get(req_id)


def all_act_requirements() -> list[ActRequirement]:
    """全要件をフラットなリストで返す."""
    return [r for c in ACT_CHAPTERS for r in c.requirements]


def all_act_requirement_ids() -> list[str]:
    """全要件IDのリスト."""
    return [r.req_id for r in all_act_requirements()]


def get_meti_to_act_mapping() -> dict[str, list[str]]:
    """METI要件ID -> AI推進法要件IDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for req in all_act_requirements():
        for meti_id in req.meti_mapping:
            mapping.setdefault(meti_id, []).append(req.req_id)
    return mapping


def get_act_to_iso_mapping() -> dict[str, list[str]]:
    """AI推進法要件ID -> ISO要求事項IDsのマッピング."""
    mapping: dict[str, list[str]] = {}
    for req in all_act_requirements():
        if req.iso_mapping:
            mapping[req.req_id] = list(req.iso_mapping)
    return mapping
