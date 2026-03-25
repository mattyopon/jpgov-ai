# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""ISO 42001認証取得の実務手順ガイド.

ISO/IEC 42001:2023 AIマネジメントシステム（AIMS）の認証を
実際に取得するための実務手順を構造化データとして保持する。

認証プロセス、必要文書、審査機関情報、よくある不適合等を網羅する。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CertificationPhase:
    """認証取得プロセスの各フェーズ."""

    phase: int
    name: str
    duration: str
    description: str
    tasks: list[str] = field(default_factory=list)
    required_documents: list[str] = field(default_factory=list)
    jpgovai_value: str = ""


@dataclass(frozen=True)
class CommonNonconformity:
    """審査でよく指摘される不適合."""

    rank: int
    title: str
    description: str
    clause: str  # ISO 42001 条項
    prevention: str
    evidence_needed: str


@dataclass(frozen=True)
class CertificationBody:
    """認証機関情報."""

    name: str
    code: str
    accredited_since: str
    website: str
    focus_areas: str
    typical_cost_range: str
    notes: str = ""


@dataclass(frozen=True)
class CertificationTimeline:
    """企業規模別の認証取得期間目安."""

    size: str
    size_description: str
    total_months_min: int
    total_months_max: int
    notes: str = ""


@dataclass(frozen=True)
class MaintenanceAudit:
    """認証維持（サーベイランス審査）情報."""

    audit_type: str
    frequency: str
    scope: str
    typical_duration: str
    cost_factor: str


# ── 認証プロセス ─────────────────────────────────────────

CERTIFICATION_PHASES: list[CertificationPhase] = [
    CertificationPhase(
        phase=1,
        name="ギャップ分析と計画策定",
        duration="1-2ヶ月",
        description=(
            "現状のAIガバナンス体制をISO 42001の全要求事項と照合し、"
            "ギャップを特定する。認証取得に向けたロードマップを策定する。"
        ),
        tasks=[
            "現状のAIガバナンス体制の棚卸し",
            "ISO 42001の全要求事項とのギャップ特定",
            "是正計画の策定と優先順位付け",
            "プロジェクト体制の構築（AIガバナンス委員会の設立）",
            "経営層のコミットメント取得（マネジメントレビュー予定の確定）",
            "認証審査機関の選定と見積もり取得",
        ],
        required_documents=[
            "ギャップ分析報告書",
            "認証取得プロジェクト計画書",
            "プロジェクト体制図",
        ],
        jpgovai_value=(
            "ギャップ分析を自動実行。手動では2-4週間かかる作業を30分に短縮。"
            "全26要件に対する現状スコアと改善アクションを自動提案。"
        ),
    ),
    CertificationPhase(
        phase=2,
        name="AIMS（AIマネジメントシステム）の構築",
        duration="3-6ヶ月",
        description=(
            "ISO 42001の要求事項に適合するAIMS文書体系を構築し、"
            "必要なプロセス・手順を整備する。"
        ),
        tasks=[
            "AIマネジメントシステム適用範囲の決定",
            "AIポリシー（AI方針）の策定",
            "AI利害関係者分析の実施",
            "AIリスクアセスメント手順の確立と初回実施",
            "AIシステムインベントリ（台帳）の作成",
            "AI影響評価プロセスの設計",
            "インシデント対応手順の整備",
            "教育訓練プログラムの策定と初回実施",
            "文書管理手順の確立",
            "内部監査計画の策定",
            "是正措置プロセスの確立",
        ],
        required_documents=[
            "AIMS適用範囲文書",
            "AI方針（AIポリシー）",
            "利害関係者要求事項一覧",
            "AIリスクアセスメント手順書",
            "AIリスクアセスメント結果",
            "AIシステムインベントリ",
            "AI影響評価手順書",
            "インシデント対応手順書",
            "教育訓練計画書・実施記録",
            "文書管理手順書",
            "内部監査計画書",
            "是正措置手順書",
        ],
        jpgovai_value=(
            "ポリシーテンプレート自動生成で文書作成工数を50%削減。"
            "エビデンス管理で文書を体系的に管理。"
            "リスクアセスメント機能で初回評価を効率化。"
        ),
    ),
    CertificationPhase(
        phase=3,
        name="運用と内部監査",
        duration="3ヶ月以上",
        description=(
            "構築したAIMSを実際に運用し、内部監査で有効性を検証する。"
            "ISO 42001認証審査では「最低3ヶ月の運用実績」が求められることが多い。"
        ),
        tasks=[
            "AIMSの運用開始",
            "定期レビューサイクルの実行（最低1回）",
            "内部監査の実施（最低1回、認証範囲全体をカバー）",
            "マネジメントレビューの実施（最低1回）",
            "是正措置の実施と有効性確認",
            "AIリスクアセスメントの定期更新",
            "運用記録の蓄積（審査エビデンス用）",
        ],
        required_documents=[
            "内部監査報告書",
            "マネジメントレビュー議事録",
            "是正措置記録",
            "定期レビュー記録",
            "AIリスクアセスメント更新記録",
            "運用記録（監査証跡）",
        ],
        jpgovai_value=(
            "定期レビューサイクルが運用の証跡に。"
            "監査証跡（SHA-256ハッシュチェーン）が改竄防止で信頼性を確保。"
            "内部監査チェックリストの自動生成で監査工数を削減。"
        ),
    ),
    CertificationPhase(
        phase=4,
        name="認証審査",
        duration="2-4週間",
        description=(
            "認証機関による審査。Stage 1（文書審査）とStage 2（実地審査）の"
            "2段階で行われる。"
        ),
        tasks=[
            "Stage 1審査（文書審査）: 文書体系の適合性確認",
            "Stage 1指摘事項の是正",
            "Stage 2審査（実地審査）: 運用の実効性確認",
            "不適合指摘事項の是正（あれば、通常30-90日以内）",
            "認証登録",
        ],
        required_documents=[
            "Stage 1用: 全AIMS文書一式",
            "Stage 2用: 運用記録・エビデンス一式",
            "是正措置報告書（不適合があれば）",
        ],
        jpgovai_value=(
            "監査パッケージ自動生成で審査対応コストを80%削減。"
            "審査員の質問にボタン一つで関連エビデンスを提示。"
        ),
    ),
]


# ── よくある不適合 TOP 10 ────────────────────────────────

COMMON_NONCONFORMITIES: list[CommonNonconformity] = [
    CommonNonconformity(
        rank=1,
        title="AIリスクアセスメントの不備",
        description=(
            "リスクアセスメントが実施されていない、AI固有のリスクがカバーされていない、"
            "またはリスク軽減策の有効性が検証されていない。"
        ),
        clause="6.1, 6.1.2",
        prevention=(
            "AI固有のリスクカタログを整備し、全AIシステムに対して"
            "リスクアセスメントを実施する。軽減策の有効性評価まで追跡する。"
        ),
        evidence_needed=(
            "リスクアセスメント記録、リスクマトリクス、"
            "軽減策の実施・有効性確認記録"
        ),
    ),
    CommonNonconformity(
        rank=2,
        title="AI方針の不整合",
        description=(
            "AI方針（ポリシー）が組織の事業目的と整合していない、"
            "または具体性に欠ける。"
        ),
        clause="5.2",
        prevention=(
            "AI方針を経営戦略と紐付けて策定する。"
            "抽象的な原則だけでなく、具体的な行動指針を含める。"
        ),
        evidence_needed="AI方針文書（経営層承認済み）、方針の定期レビュー記録",
    ),
    CommonNonconformity(
        rank=3,
        title="内部監査の独立性不足",
        description=(
            "内部監査が被監査部門の人員によって実施されている、"
            "または監査の客観性が確保されていない。"
        ),
        clause="9.2",
        prevention=(
            "内部監査員を被監査部門とは独立した人員で構成する。"
            "外部の専門家を活用することも有効。"
        ),
        evidence_needed="内部監査員の任命記録（独立性の証跡）、内部監査報告書",
    ),
    CommonNonconformity(
        rank=4,
        title="AI影響評価の未実施",
        description=(
            "AIシステムの社会的影響評価が実施されていない、"
            "または影響評価のプロセスが確立されていない。"
        ),
        clause="Annex B B.3",
        prevention=(
            "AIシステム導入前の影響評価プロセスを確立し、"
            "全AIシステム（リスクレベルに応じた深さで）に適用する。"
        ),
        evidence_needed="AI影響評価手順書、影響評価実施記録",
    ),
    CommonNonconformity(
        rank=5,
        title="利害関係者の特定漏れ",
        description=(
            "AIシステムの利害関係者（影響を受ける人々）の特定が不十分。"
            "特に間接的な利害関係者の見落とし。"
        ),
        clause="4.2",
        prevention=(
            "利害関係者マッピングを実施し、"
            "直接的・間接的な利害関係者を網羅的に特定する。"
        ),
        evidence_needed="利害関係者分析文書、要求事項一覧",
    ),
    CommonNonconformity(
        rank=6,
        title="教育訓練の不足",
        description=(
            "AI関連の教育訓練が未実施、役割に応じた教育になっていない、"
            "または教育の有効性評価がない。"
        ),
        clause="7.2, 7.3",
        prevention=(
            "役割別の教育カリキュラムを策定し、有効性評価（テスト等）を実施する。"
            "教育の年次計画を策定し、実施を記録する。"
        ),
        evidence_needed="教育訓練計画書、実施記録、テスト結果、受講者リスト",
    ),
    CommonNonconformity(
        rank=7,
        title="マネジメントレビューの不備",
        description=(
            "マネジメントレビューが未実施、またはインプット/アウトプットが不十分。"
            "経営層の関与が形骸化している。"
        ),
        clause="9.3",
        prevention=(
            "マネジメントレビューの議題にISO 42001が定める全インプットを含める。"
            "経営層の意思決定と指示事項を明確に記録する。"
        ),
        evidence_needed="マネジメントレビュー議事録（全インプット/アウトプット含む）",
    ),
    CommonNonconformity(
        rank=8,
        title="文書管理の不備",
        description=(
            "文書のバージョン管理、承認プロセス、配布管理が不十分。"
            "最新版でない文書が現場で使用されている。"
        ),
        clause="7.5",
        prevention=(
            "文書管理台帳を整備し、バージョン管理・承認フローを確立する。"
            "電子文書管理システムの導入が望ましい。"
        ),
        evidence_needed="文書管理台帳、文書承認記録、最新版配布の証跡",
    ),
    CommonNonconformity(
        rank=9,
        title="是正措置の有効性未確認",
        description=(
            "不適合に対する是正措置は実施したが、"
            "その有効性の確認（再発していないか）が行われていない。"
        ),
        clause="10.1",
        prevention=(
            "是正措置の完了後、一定期間（1-3ヶ月）経過後に"
            "有効性を確認するプロセスを組み込む。"
        ),
        evidence_needed="是正措置記録（原因分析→対策→有効性確認の全サイクル）",
    ),
    CommonNonconformity(
        rank=10,
        title="AIシステムインベントリの不備",
        description=(
            "組織が利用するAIシステムの台帳が整備されていない、"
            "または不完全（SaaS型AIの利用が漏れている等）。"
        ),
        clause="Annex B B.2",
        prevention=(
            "全AIシステム（自社開発+外部サービス+API利用）を台帳化する。"
            "定期的に棚卸しを行い、シャドーAIの検出にも努める。"
        ),
        evidence_needed="AIシステムインベントリ（全AIの一覧と属性情報）",
    ),
]


# ── 認証機関情報 ─────────────────────────────────────────

CERTIFICATION_BODIES: list[CertificationBody] = [
    CertificationBody(
        name="SGSジャパン株式会社",
        code="SGS",
        accredited_since="2024-01",
        website="https://www.sgs.co.jp/",
        focus_areas=(
            "リスクアセスメントの具体性、エビデンスの充足度。"
            "製造業・金融業の審査実績が多い。"
        ),
        typical_cost_range="100万-300万円（初回審査）",
        notes=(
            "JABおよびUKAS認定。日本国内で最も審査実績が多い認証機関の一つ。"
            "多言語対応が可能。"
        ),
    ),
    CertificationBody(
        name="テュフラインランドジャパン株式会社",
        code="TUV",
        accredited_since="2024-03",
        website="https://www.tuv.com/japan/jp/",
        focus_areas=(
            "プロセスの継続性、内部監査の実効性。"
            "特に自動車・製造業向けの審査に強み。"
        ),
        typical_cost_range="120万-350万円（初回審査）",
        notes="ドイツ系認証機関。国際的な認知度が高い。",
    ),
    CertificationBody(
        name="BSIグループジャパン株式会社",
        code="BSI",
        accredited_since="2024-06",
        website="https://www.bsigroup.com/ja-JP/",
        focus_areas=(
            "マネジメントシステムの成熟度、リスクベースの審査アプローチ。"
            "ISO 27001とのインテグレーテッド審査に対応。"
        ),
        typical_cost_range="130万-400万円（初回審査）",
        notes="英国規格協会系。ISO規格策定に関与。統合審査のノウハウが豊富。",
    ),
    CertificationBody(
        name="日本品質保証機構（JQA）",
        code="JQA",
        accredited_since="2024-09",
        website="https://www.jqa.jp/",
        focus_areas=(
            "日本の産業特性を踏まえた審査。"
            "国内法規制との整合性を重視。"
        ),
        typical_cost_range="100万-250万円（初回審査）",
        notes="国内最大の認証機関。日本語での審査対応がスムーズ。",
    ),
]


# ── 企業規模別 認証取得期間目安 ────────────────────────────

CERTIFICATION_TIMELINES: list[CertificationTimeline] = [
    CertificationTimeline(
        size="small",
        size_description="50人未満、AIシステム1-3個",
        total_months_min=6,
        total_months_max=9,
        notes=(
            "小規模組織は文書量が少なく短期間で取得可能。"
            "ただし専任担当者がいない場合は期間が延びる。"
            "外部コンサルの活用を推奨。"
        ),
    ),
    CertificationTimeline(
        size="medium",
        size_description="50-300人、AIシステム3-10個",
        total_months_min=9,
        total_months_max=12,
        notes=(
            "最も標準的なケース。社内にプロジェクトチームを組成し、"
            "月1-2回の定例会議で進捗管理する。"
            "既存のISO 27001認証があれば統合しやすい。"
        ),
    ),
    CertificationTimeline(
        size="large",
        size_description="300-1000人、AIシステム10-30個",
        total_months_min=12,
        total_months_max=18,
        notes=(
            "部門間の調整に時間がかかる。"
            "フェーズ分割してまず一部門で認証取得し、"
            "段階的に適用範囲を拡大する戦略が有効。"
        ),
    ),
    CertificationTimeline(
        size="enterprise",
        size_description="1000人以上、AIシステム30個以上",
        total_months_min=15,
        total_months_max=24,
        notes=(
            "グローバル拠点がある場合はさらに期間が延びる。"
            "まず日本拠点で認証取得し、他拠点に展開する戦略を推奨。"
            "専任PMの配置が必須。"
        ),
    ),
]


# ── 認証維持 ─────────────────────────────────────────────

MAINTENANCE_AUDITS: list[MaintenanceAudit] = [
    MaintenanceAudit(
        audit_type="サーベイランス審査（維持審査）",
        frequency="年1回（初回認証から1年後、2年後）",
        scope="AIMSの運用状況の抜き取り確認。全要求事項をカバーする必要はない。",
        typical_duration="1-2日",
        cost_factor="初回審査の30-40%",
    ),
    MaintenanceAudit(
        audit_type="更新審査（再認証審査）",
        frequency="3年ごと（認証有効期限の更新）",
        scope="AIMSの全体的な有効性を再評価。全要求事項をカバー。",
        typical_duration="2-4日",
        cost_factor="初回審査の60-80%",
    ),
]


# ── ユーティリティ ────────────────────────────────────────

def get_certification_phases() -> list[CertificationPhase]:
    """認証プロセスの全フェーズを取得."""
    return list(CERTIFICATION_PHASES)


def get_certification_phase(phase_num: int) -> CertificationPhase | None:
    """フェーズ番号から取得."""
    for p in CERTIFICATION_PHASES:
        if p.phase == phase_num:
            return p
    return None


def get_common_nonconformities() -> list[CommonNonconformity]:
    """よくある不適合のリストを取得."""
    return list(COMMON_NONCONFORMITIES)


def get_certification_bodies() -> list[CertificationBody]:
    """認証機関一覧を取得."""
    return list(CERTIFICATION_BODIES)


def get_certification_timelines() -> list[CertificationTimeline]:
    """企業規模別の認証取得期間目安を取得."""
    return list(CERTIFICATION_TIMELINES)


def get_maintenance_audits() -> list[MaintenanceAudit]:
    """認証維持審査情報を取得."""
    return list(MAINTENANCE_AUDITS)


def get_all_required_documents() -> list[str]:
    """認証取得に必要な全文書のリスト（フェーズ横断）."""
    docs: list[str] = []
    seen: set[str] = set()
    for phase in CERTIFICATION_PHASES:
        for doc in phase.required_documents:
            if doc not in seen:
                docs.append(doc)
                seen.add(doc)
    return docs
