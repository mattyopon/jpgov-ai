# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""ISO/IEC 42001:2023 (AIMS) 要求事項定義.

ISO/IEC 42001はAIマネジメントシステム(AIMS)の国際標準規格。
本ファイルはISO 42001の主要な要求事項と、METI AI事業者ガイドラインとの
クロスマッピングを定義する。

参考:
- ISO/IEC 42001:2023 Information technology - Artificial intelligence - Management system
- JIS規格化は審議中
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ISORequirement:
    """ISO 42001の個別要求事項."""

    req_id: str  # e.g., "ISO-4.1"
    clause: str  # ISO条項番号 e.g., "4.1"
    title: str
    description: str
    meti_mapping: list[str] = field(default_factory=list)  # 対応するMETI要件ID


@dataclass(frozen=True)
class ISOClause:
    """ISO 42001の条項."""

    clause_id: str
    title: str
    description: str
    requirements: list[ISORequirement] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ISO/IEC 42001:2023 要求事項
# ---------------------------------------------------------------------------

ISO_CLAUSES: list[ISOClause] = [
    # ── 4. 組織の状況 ──
    ISOClause(
        clause_id="4",
        title="組織の状況（Context of the Organization）",
        description="AIマネジメントシステムに関連する組織の状況を理解し、利害関係者のニーズと期待を特定する。",
        requirements=[
            ISORequirement(
                req_id="ISO-4.1",
                clause="4.1",
                title="組織とその状況の理解",
                description="AIマネジメントシステムの目的に関連する外部・内部の課題を決定すること。",
                meti_mapping=["C07-R02"],
            ),
            ISORequirement(
                req_id="ISO-4.2",
                clause="4.2",
                title="利害関係者のニーズ及び期待の理解",
                description="AIマネジメントシステムに関連する利害関係者と、その要求事項を特定すること。",
                meti_mapping=["C01-R01", "C06-R01"],
            ),
            ISORequirement(
                req_id="ISO-4.3",
                clause="4.3",
                title="AIマネジメントシステムの適用範囲の決定",
                description="AIMSの適用範囲を決定し、文書化すること。",
                meti_mapping=["C07-R02"],
            ),
            ISORequirement(
                req_id="ISO-4.4",
                clause="4.4",
                title="AIマネジメントシステム",
                description="ISO 42001の要求事項に従い、AIMSを確立・実施・維持・継続的に改善すること。",
                meti_mapping=["C07-R02", "C07-R04"],
            ),
        ],
    ),

    # ── 5. リーダーシップ ──
    ISOClause(
        clause_id="5",
        title="リーダーシップ（Leadership）",
        description="トップマネジメントがAIMSに対するリーダーシップとコミットメントを示す。",
        requirements=[
            ISORequirement(
                req_id="ISO-5.1",
                clause="5.1",
                title="リーダーシップ及びコミットメント",
                description="トップマネジメントがAIMSに対するリーダーシップ及びコミットメントを実証すること。",
                meti_mapping=["C07-R01", "C07-R02"],
            ),
            ISORequirement(
                req_id="ISO-5.2",
                clause="5.2",
                title="AI方針",
                description="AIに関する方針を確立し、伝達し、利用可能な状態にすること。",
                meti_mapping=["C01-R01", "C07-R02"],
            ),
            ISORequirement(
                req_id="ISO-5.3",
                clause="5.3",
                title="組織の役割、責任及び権限",
                description="AIMS関連の役割に対して責任及び権限を割り当て、伝達すること。",
                meti_mapping=["C07-R01"],
            ),
        ],
    ),

    # ── 6. 計画 ──
    ISOClause(
        clause_id="6",
        title="計画（Planning）",
        description="AIMSのリスク及び機会への取組み、AI目的の設定とその達成計画。",
        requirements=[
            ISORequirement(
                req_id="ISO-6.1",
                clause="6.1",
                title="リスク及び機会への取組み",
                description="AIに関連するリスク及び機会を特定し、それらに対処するための計画を策定すること。",
                meti_mapping=["C02-R01"],
            ),
            ISORequirement(
                req_id="ISO-6.1.2",
                clause="6.1.2",
                title="AIリスクアセスメント",
                description="AIシステムに関するリスクアセスメントのプロセスを定義し、実施すること。",
                meti_mapping=["C02-R01", "C02-R02"],
            ),
            ISORequirement(
                req_id="ISO-6.1.3",
                clause="6.1.3",
                title="AIリスク対応",
                description="リスクアセスメントの結果に基づき、リスク対応の選択肢を選び、実施すること。",
                meti_mapping=["C02-R01", "C02-R03"],
            ),
            ISORequirement(
                req_id="ISO-6.2",
                clause="6.2",
                title="AI目的及びそれを達成するための計画策定",
                description="AIに関する測定可能な目的を設定し、達成計画を策定すること。",
                meti_mapping=["C10-R01"],
            ),
        ],
    ),

    # ── 7. 支援 ──
    ISOClause(
        clause_id="7",
        title="支援（Support）",
        description="AIMSの確立・実施・維持・改善に必要な資源、力量、認識、コミュニケーション、文書化。",
        requirements=[
            ISORequirement(
                req_id="ISO-7.1",
                clause="7.1",
                title="資源",
                description="AIMSに必要な資源を決定し、提供すること。",
                meti_mapping=["C07-R02"],
            ),
            ISORequirement(
                req_id="ISO-7.2",
                clause="7.2",
                title="力量",
                description="AIMS関連の業務を行う人々に必要な力量を決定し、確保すること。",
                meti_mapping=["C08-R01"],
            ),
            ISORequirement(
                req_id="ISO-7.3",
                clause="7.3",
                title="認識",
                description="関連する人々がAI方針、自らの貢献、不適合の影響を認識すること。",
                meti_mapping=["C08-R01", "C08-R02"],
            ),
            ISORequirement(
                req_id="ISO-7.4",
                clause="7.4",
                title="コミュニケーション",
                description="AIMSに関する内部及び外部のコミュニケーションを計画すること。",
                meti_mapping=["C06-R01"],
            ),
            ISORequirement(
                req_id="ISO-7.5",
                clause="7.5",
                title="文書化した情報",
                description="AIMSで必要な文書化した情報を作成・更新・管理すること。",
                meti_mapping=["C06-R03", "C07-R04"],
            ),
        ],
    ),

    # ── 8. 運用 ──
    ISOClause(
        clause_id="8",
        title="運用（Operation）",
        description="AIMSの要求事項を満たすために必要なプロセスの計画・実施・管理。",
        requirements=[
            ISORequirement(
                req_id="ISO-8.1",
                clause="8.1",
                title="運用の計画及び管理",
                description="AIMSの要求事項を満たすために必要なプロセスを計画・実施・管理すること。",
                meti_mapping=["C07-R02"],
            ),
            ISORequirement(
                req_id="ISO-8.2",
                clause="8.2",
                title="AIリスクアセスメント（実施）",
                description="計画した間隔またはリスクの変化が生じた場合にAIリスクアセスメントを実施すること。",
                meti_mapping=["C02-R01"],
            ),
            ISORequirement(
                req_id="ISO-8.3",
                clause="8.3",
                title="AIリスク対応（実施）",
                description="AIリスク対応計画を実施すること。",
                meti_mapping=["C02-R03", "C05-R01"],
            ),
            ISORequirement(
                req_id="ISO-8.4",
                clause="8.4",
                title="AIシステム影響評価",
                description="AIシステムが個人、グループ、社会に与える影響を評価すること。",
                meti_mapping=["C01-R01", "C03-R01", "C04-R02"],
            ),
        ],
    ),

    # ── 9. パフォーマンス評価 ──
    ISOClause(
        clause_id="9",
        title="パフォーマンス評価（Performance Evaluation）",
        description="AIMSのパフォーマンス及び有効性の監視・測定・分析・評価。",
        requirements=[
            ISORequirement(
                req_id="ISO-9.1",
                clause="9.1",
                title="監視、測定、分析及び評価",
                description="AIMSのパフォーマンスを監視・測定・分析・評価すること。",
                meti_mapping=["C03-R02", "C07-R04"],
            ),
            ISORequirement(
                req_id="ISO-9.2",
                clause="9.2",
                title="内部監査",
                description="計画した間隔でAIMSの内部監査を実施すること。",
                meti_mapping=["C07-R04"],
            ),
            ISORequirement(
                req_id="ISO-9.3",
                clause="9.3",
                title="マネジメントレビュー",
                description="計画した間隔でAIMSのマネジメントレビューを実施すること。",
                meti_mapping=["C07-R02"],
            ),
        ],
    ),

    # ── 10. 改善 ──
    ISOClause(
        clause_id="10",
        title="改善（Improvement）",
        description="不適合への対処と継続的改善。",
        requirements=[
            ISORequirement(
                req_id="ISO-10.1",
                clause="10.1",
                title="不適合及び是正処置",
                description="不適合が発生した場合、是正処置を講じること。",
                meti_mapping=["C03-R03", "C05-R03"],
            ),
            ISORequirement(
                req_id="ISO-10.2",
                clause="10.2",
                title="継続的改善",
                description="AIMSの適切性、妥当性及び有効性を継続的に改善すること。",
                meti_mapping=["C10-R01"],
            ),
        ],
    ),
]


# ── ユーティリティ ────────────────────────────────────────────────

_CLAUSE_MAP: dict[str, ISOClause] = {c.clause_id: c for c in ISO_CLAUSES}
_REQ_MAP: dict[str, ISORequirement] = {
    r.req_id: r for c in ISO_CLAUSES for r in c.requirements
}


def get_iso_clause(clause_id: str) -> ISOClause | None:
    """条項IDから条項を取得."""
    return _CLAUSE_MAP.get(clause_id)


def get_iso_requirement(req_id: str) -> ISORequirement | None:
    """要求事項IDから要求事項を取得."""
    return _REQ_MAP.get(req_id)


def all_iso_requirements() -> list[ISORequirement]:
    """全要求事項をフラットなリストで返す."""
    return [r for c in ISO_CLAUSES for r in c.requirements]


def all_iso_requirement_ids() -> list[str]:
    """全要求事項IDのリスト."""
    return [r.req_id for r in all_iso_requirements()]


def get_meti_to_iso_mapping() -> dict[str, list[str]]:
    """METI要件ID -> ISO要求事項IDsのマッピングを返す."""
    mapping: dict[str, list[str]] = {}
    for req in all_iso_requirements():
        for meti_id in req.meti_mapping:
            mapping.setdefault(meti_id, []).append(req.req_id)
    return mapping


def get_iso_to_meti_mapping() -> dict[str, list[str]]:
    """ISO要求事項ID -> METI要件IDsのマッピングを返す."""
    mapping: dict[str, list[str]] = {}
    for req in all_iso_requirements():
        mapping[req.req_id] = list(req.meti_mapping)
    return mapping
