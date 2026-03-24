# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""全フレームワーク間クロスマッピングマトリクス.

METI AI事業者ガイドライン / ISO 42001 / NIST AI RMF / EU AI Act / AI推進法
の5フレームワーク間の相互マッピングを提供する。

「この要件に対応すれば、これらの規制にも同時に対応できる」を可視化する。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CrossMappingEntry:
    """クロスマッピングの1エントリ.

    ある共通テーマに対する各フレームワークの対応要件を記録する。
    """

    theme_id: str
    theme: str  # 共通テーマ名
    description: str
    meti_ids: list[str] = field(default_factory=list)
    iso_ids: list[str] = field(default_factory=list)
    nist_ids: list[str] = field(default_factory=list)
    eu_articles: list[str] = field(default_factory=list)
    act_ids: list[str] = field(default_factory=list)  # AI推進法


# ---------------------------------------------------------------------------
# クロスマッピングマトリクス
# ---------------------------------------------------------------------------

CROSS_MAPPING: list[CrossMappingEntry] = [
    # ── ガバナンス体制 ──
    CrossMappingEntry(
        theme_id="CM-01",
        theme="ガバナンス体制の整備",
        description="AIガバナンスの方針・体制・責任者を確立する。",
        meti_ids=["C07-R01", "C07-R02"],
        iso_ids=["ISO-5.1", "ISO-5.2", "ISO-5.3"],
        nist_ids=["GOVERN-1.1", "GOVERN-1.2", "GOVERN-1.3", "GOVERN-2.1"],
        eu_articles=["Art.9.1", "Art.17"],
        act_ids=["APA-11"],
    ),
    # ── リスク管理 ──
    CrossMappingEntry(
        theme_id="CM-02",
        theme="リスク管理",
        description="AIリスクの特定・評価・対応・モニタリングを行う。",
        meti_ids=["C02-R01", "C02-R03"],
        iso_ids=["ISO-6.1", "ISO-6.1.2", "ISO-6.1.3", "ISO-8.2", "ISO-8.3"],
        nist_ids=["MAP-2.1", "MEASURE-1.1", "MANAGE-1.1", "MANAGE-2.1"],
        eu_articles=["Art.9.2", "Art.9.4", "Art.9.5"],
        act_ids=["APA-02", "APA-05"],
    ),
    # ── データ品質管理 ──
    CrossMappingEntry(
        theme_id="CM-03",
        theme="データ品質管理",
        description="学習データの品質・代表性・バイアスを管理する。",
        meti_ids=["C02-R02"],
        iso_ids=["ISO-6.1.2"],
        nist_ids=["MAP-3.1"],
        eu_articles=["Art.10"],
        act_ids=["APA-05"],
    ),
    # ── 公平性・バイアス ──
    CrossMappingEntry(
        theme_id="CM-04",
        theme="公平性・バイアス対策",
        description="AIによる不当な差別を防止し、公平性を確保する。",
        meti_ids=["C03-R01", "C03-R02", "C03-R03"],
        iso_ids=["ISO-8.4"],
        nist_ids=["MAP-2.1", "MEASURE-2.1"],
        eu_articles=["Art.10.2f"],
        act_ids=["APA-04"],
    ),
    # ── 透明性・説明可能性 ──
    CrossMappingEntry(
        theme_id="CM-05",
        theme="透明性・説明可能性",
        description="AI利用の開示と判断根拠の説明を行う。",
        meti_ids=["C06-R01", "C06-R02", "C06-R03"],
        iso_ids=["ISO-7.4", "ISO-7.5"],
        nist_ids=["GOVERN-1.5", "MAP-1.5", "MEASURE-2.2"],
        eu_articles=["Art.13", "Art.50"],
        act_ids=["APA-03"],
    ),
    # ── プライバシー保護 ──
    CrossMappingEntry(
        theme_id="CM-06",
        theme="プライバシー保護",
        description="個人情報の適正な取扱いとプライバシー影響評価を行う。",
        meti_ids=["C04-R01", "C04-R02", "C04-R03"],
        iso_ids=["ISO-8.4"],
        nist_ids=["MAP-2.2"],
        eu_articles=["Art.10.5"],
        act_ids=["APA-06"],
    ),
    # ── セキュリティ ──
    CrossMappingEntry(
        theme_id="CM-07",
        theme="セキュリティ対策",
        description="AIシステムのサイバーセキュリティと堅牢性を確保する。",
        meti_ids=["C05-R01", "C05-R02"],
        iso_ids=["ISO-8.3"],
        nist_ids=["MEASURE-2.3"],
        eu_articles=["Art.15"],
        act_ids=["APA-07"],
    ),
    # ── インシデント対応 ──
    CrossMappingEntry(
        theme_id="CM-08",
        theme="インシデント対応",
        description="AIインシデントの検出・対応・報告体制を整備する。",
        meti_ids=["C05-R03"],
        iso_ids=["ISO-10.1"],
        nist_ids=["MANAGE-2.2"],
        eu_articles=["Art.73"],
        act_ids=["APA-08"],
    ),
    # ── 人間による監視 ──
    CrossMappingEntry(
        theme_id="CM-09",
        theme="人間による監視（Human Oversight）",
        description="AIの判断に対する人間の最終確認・介入を確保する。",
        meti_ids=["C01-R02"],
        iso_ids=["ISO-8.4"],
        nist_ids=[],
        eu_articles=["Art.14"],
        act_ids=["APA-01"],
    ),
    # ── 文書化・記録管理 ──
    CrossMappingEntry(
        theme_id="CM-10",
        theme="文書化・記録管理",
        description="技術文書、運用記録、監査証跡を適切に管理する。",
        meti_ids=["C06-R03", "C07-R04"],
        iso_ids=["ISO-7.5", "ISO-9.2"],
        nist_ids=["GOVERN-1.4"],
        eu_articles=["Art.11", "Art.12"],
        act_ids=["APA-12"],
    ),
    # ── 教育・リテラシー ──
    CrossMappingEntry(
        theme_id="CM-11",
        theme="教育・リテラシー",
        description="AI関連の教育・訓練を実施し、リテラシーを向上させる。",
        meti_ids=["C08-R01", "C08-R02"],
        iso_ids=["ISO-7.2", "ISO-7.3"],
        nist_ids=["GOVERN-2.2"],
        eu_articles=["Art.4"],
        act_ids=["APA-09", "APA-10"],
    ),
    # ── 影響評価 ──
    CrossMappingEntry(
        theme_id="CM-12",
        theme="影響評価",
        description="AIシステムが個人・社会に与える影響を評価する。",
        meti_ids=["C01-R01", "C04-R02"],
        iso_ids=["ISO-8.4"],
        nist_ids=["MAP-5.1"],
        eu_articles=["Art.27"],
        act_ids=["APA-04"],
    ),
    # ── 継続的改善 ──
    CrossMappingEntry(
        theme_id="CM-13",
        theme="継続的改善・モニタリング",
        description="AIガバナンスの継続的な改善とパフォーマンスモニタリングを行う。",
        meti_ids=["C10-R01"],
        iso_ids=["ISO-9.1", "ISO-10.2"],
        nist_ids=["MEASURE-3.1", "MANAGE-4.1"],
        eu_articles=["Art.72"],
        act_ids=[],
    ),
    # ── サプライチェーン管理 ──
    CrossMappingEntry(
        theme_id="CM-14",
        theme="サプライチェーン・ベンダー管理",
        description="AIに関するサードパーティ・サプライチェーンのリスクを管理する。",
        meti_ids=["C07-R03"],
        iso_ids=["ISO-8.1"],
        nist_ids=["GOVERN-3.1"],
        eu_articles=["Art.22"],
        act_ids=[],
    ),
    # ── 安全停止 ──
    CrossMappingEntry(
        theme_id="CM-15",
        theme="安全な運用・停止手順",
        description="AIシステムの異常時の安全停止・フォールバック手順を整備する。",
        meti_ids=["C02-R03"],
        iso_ids=["ISO-8.3"],
        nist_ids=["MANAGE-2.1"],
        eu_articles=["Art.9.4"],
        act_ids=["APA-02"],
    ),
]


# ── ユーティリティ ────────────────────────────────────────────────

_MAPPING_MAP: dict[str, CrossMappingEntry] = {e.theme_id: e for e in CROSS_MAPPING}


def get_cross_mapping_entry(theme_id: str) -> CrossMappingEntry | None:
    """テーマIDからクロスマッピングエントリを取得."""
    return _MAPPING_MAP.get(theme_id)


def all_cross_mappings() -> list[CrossMappingEntry]:
    """全クロスマッピングエントリを返す."""
    return list(CROSS_MAPPING)


def get_frameworks_for_meti_requirement(meti_id: str) -> dict[str, list[str]]:
    """METI要件IDに対応する各フレームワークの要件IDsを返す.

    Returns:
        dict with keys: "iso", "nist", "eu_articles", "act"
    """
    result: dict[str, list[str]] = {
        "iso": [],
        "nist": [],
        "eu_articles": [],
        "act": [],
    }
    for entry in CROSS_MAPPING:
        if meti_id in entry.meti_ids:
            result["iso"].extend(entry.iso_ids)
            result["nist"].extend(entry.nist_ids)
            result["eu_articles"].extend(entry.eu_articles)
            result["act"].extend(entry.act_ids)

    # 重複排除
    for key in result:
        result[key] = sorted(set(result[key]))
    return result


def get_compliance_synergies() -> list[dict]:
    """「この要件に対応すれば、他のフレームワークにも対応できる」を可視化.

    各METIの要件IDについて、同時に対応できるフレームワーク数を算出する。
    """
    from app.guidelines.meti_v1_1 import all_requirement_ids

    synergies: list[dict] = []
    for meti_id in all_requirement_ids():
        frameworks = get_frameworks_for_meti_requirement(meti_id)
        count = sum(1 for v in frameworks.values() if v)
        synergies.append({
            "meti_id": meti_id,
            "iso_count": len(frameworks["iso"]),
            "nist_count": len(frameworks["nist"]),
            "eu_count": len(frameworks["eu_articles"]),
            "act_count": len(frameworks["act"]),
            "total_mapped_frameworks": count,
            "details": frameworks,
        })
    return sorted(synergies, key=lambda x: x["total_mapped_frameworks"], reverse=True)


def get_coverage_matrix() -> dict[str, dict[str, list[str]]]:
    """全テーマ × 全フレームワークのカバレッジマトリクスを返す.

    Returns:
        {theme_id: {"meti": [...], "iso": [...], "nist": [...], "eu": [...], "act": [...]}}
    """
    matrix: dict[str, dict[str, list[str]]] = {}
    for entry in CROSS_MAPPING:
        matrix[entry.theme_id] = {
            "theme": [entry.theme],
            "meti": list(entry.meti_ids),
            "iso": list(entry.iso_ids),
            "nist": list(entry.nist_ids),
            "eu": list(entry.eu_articles),
            "act": list(entry.act_ids),
        }
    return matrix
