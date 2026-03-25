# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""監査パッケージ自動生成サービス.

外部監査・認証審査に必要な文書をワンクリックで生成する。
ISO 42001 Stage 1 審査用文書パッケージ、内部監査チェックリスト、
マネジメントレビュー議事録テンプレート、是正措置記録テンプレート等。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models import (
    GapAnalysisResult,
    ISOCheckResult,
)
from app.services.evidence import list_evidence
from app.services.gap_analysis import get_gap_analysis
from app.services.iso_check import run_iso_check


# ── Data Models ──────────────────────────────────────────

class AuditSection:
    """監査パッケージのセクション."""

    def __init__(
        self,
        requirement_id: str,
        requirement_title: str,
        compliance_status: str,
        evidence_list: list[dict[str, Any]] | None = None,
        gap_description: str = "",
        improvement_actions: list[str] | None = None,
    ) -> None:
        self.requirement_id = requirement_id
        self.requirement_title = requirement_title
        self.compliance_status = compliance_status
        self.evidence_list = evidence_list or []
        self.gap_description = gap_description
        self.improvement_actions = improvement_actions or []

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "requirement_id": self.requirement_id,
            "requirement_title": self.requirement_title,
            "compliance_status": self.compliance_status,
            "evidence_list": self.evidence_list,
            "gap_description": self.gap_description,
            "improvement_actions": self.improvement_actions,
        }


class AuditPackage:
    """監査パッケージ."""

    def __init__(
        self,
        organization_id: str,
        audit_type: str,
        target_framework: str,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.organization_id = organization_id
        self.audit_type = audit_type
        self.target_framework = target_framework
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.sections: list[AuditSection] = []
        self.documents: dict[str, str] = {}  # filename -> content

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "audit_type": self.audit_type,
            "target_framework": self.target_framework,
            "generated_at": self.generated_at,
            "sections": [s.to_dict() for s in self.sections],
            "document_count": len(self.documents),
            "document_names": list(self.documents.keys()),
        }


# ── Package Generators ───────────────────────────────────

def generate_iso42001_stage1_package(
    organization_id: str,
    gap_analysis_id: str,
    organization_name: str = "",
) -> AuditPackage:
    """ISO 42001 Stage 1 審査用文書パッケージを生成.

    Stage 1審査で必要な文書一式を自動生成する。

    Args:
        organization_id: 組織ID
        gap_analysis_id: ギャップ分析ID
        organization_name: 組織名

    Returns:
        AuditPackage: 生成されたパッケージ
    """
    package = AuditPackage(
        organization_id=organization_id,
        audit_type="iso42001_stage1",
        target_framework="ISO/IEC 42001:2023",
    )

    org_name = organization_name or "貴組織"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1. AIMS適用範囲文書
    package.documents["01_aims_scope.md"] = _generate_aims_scope(org_name, now)

    # 2. AI方針
    package.documents["02_ai_policy.md"] = _generate_ai_policy(org_name, now)

    # 3. リスクアセスメント結果サマリー
    gap = get_gap_analysis(gap_analysis_id)
    if gap:
        package.documents["03_risk_assessment_summary.md"] = (
            _generate_risk_assessment_summary(org_name, gap, now)
        )

        # ISO check
        iso_result = run_iso_check(gap)
        package.documents["04_iso42001_compliance_status.md"] = (
            _generate_iso_compliance_status(org_name, iso_result, now)
        )

        # Sections from gap analysis
        evidence_list = list_evidence(organization_id)
        evidence_map: dict[str, list[dict[str, Any]]] = {}
        for e in evidence_list:
            if e.requirement_id not in evidence_map:
                evidence_map[e.requirement_id] = []
            evidence_map[e.requirement_id].append({
                "filename": e.filename,
                "description": e.description,
                "file_type": e.file_type,
            })

        for g in gap.gaps:
            section = AuditSection(
                requirement_id=g.req_id,
                requirement_title=g.title,
                compliance_status=g.status.value if hasattr(g.status, "value") else str(g.status),
                evidence_list=evidence_map.get(g.req_id, []),
                gap_description=g.gap_description,
                improvement_actions=g.improvement_actions,
            )
            package.sections.append(section)

    # 4. 利害関係者分析テンプレート
    package.documents["05_stakeholder_analysis.md"] = (
        _generate_stakeholder_analysis_template(org_name, now)
    )

    # 5. 内部監査チェックリスト
    package.documents["06_internal_audit_checklist.md"] = (
        _generate_internal_audit_checklist(now)
    )

    return package


def generate_internal_audit_checklist() -> dict[str, str]:
    """内部監査チェックリストを生成.

    Returns:
        dict: {filename: content}
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "internal_audit_checklist.md": _generate_internal_audit_checklist(now),
    }


def generate_management_review_template(
    organization_name: str = "",
) -> dict[str, str]:
    """マネジメントレビュー議事録テンプレートを生成.

    Returns:
        dict: {filename: content}
    """
    org_name = organization_name or "貴組織"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "management_review_template.md": _generate_management_review_template(
            org_name, now
        ),
    }


def generate_corrective_action_template() -> dict[str, str]:
    """是正措置記録テンプレートを生成.

    Returns:
        dict: {filename: content}
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "corrective_action_template.md": _generate_corrective_action_template(now),
    }


# ── Template Generators ──────────────────────────────────

def _generate_aims_scope(org_name: str, date: str) -> str:
    return f"""# AIマネジメントシステム（AIMS）適用範囲

**組織名**: {org_name}
**作成日**: {date}
**文書番号**: AIMS-SCOPE-001
**版数**: 1.0

## 1. 適用範囲

本AIマネジメントシステム（AIMS）は、{org_name}における
AIシステムの開発・提供・利用に関する全ての活動に適用する。

## 2. 対象AIシステム

| No | AIシステム名 | 用途 | リスクレベル | 備考 |
|----|------------|------|------------|------|
| 1  | [記入] | [記入] | [高/中/低] | |
| 2  | [記入] | [記入] | [高/中/低] | |

## 3. 適用除外

以下はAIMSの適用範囲から除外する:
- [適用除外がある場合に記入。除外の正当性も記載]

## 4. 組織の状況

### 4.1 外部の状況
- 規制環境: METI AI事業者ガイドラインv1.1、AI推進法、ISO 42001
- 業界の状況: [記入]
- 技術動向: [記入]

### 4.2 内部の状況
- 組織構造: [記入]
- AIの利用状況: [記入]
- 既存のマネジメントシステム: [記入]

## 承認

| 役職 | 氏名 | 日付 | 署名 |
|------|------|------|------|
| [経営責任者] | | | |
| [AIガバナンス責任者] | | | |
"""


def _generate_ai_policy(org_name: str, date: str) -> str:
    return f"""# AI方針（AIポリシー）

**組織名**: {org_name}
**制定日**: {date}
**文書番号**: AIMS-POL-001
**版数**: 1.0

## 1. 目的

本方針は、{org_name}におけるAIシステムの開発・提供・利用に関する
基本的な方針を定めるものである。

## 2. 基本原則

{org_name}は、以下の原則に基づきAIを活用する:

1. **人間中心**: AIの判断において人間の尊厳と自律を尊重する
2. **安全性**: AIシステムの安全な運用を確保する
3. **公平性**: 不当な差別が生じないよう配慮する
4. **プライバシー**: 個人情報・プライバシーを保護する
5. **セキュリティ**: AI固有のセキュリティリスクに対処する
6. **透明性**: AIの利用を適切に開示し、説明責任を果たす
7. **アカウンタビリティ**: 責任の所在を明確にする

## 3. 適用範囲

本方針は、{org_name}の全てのAI関連活動に適用される。

## 4. 責任体制

- **経営層**: 本方針の承認と資源配分
- **AIガバナンス責任者**: 方針の実施と監視
- **各部門長**: 部門内のAI活用における方針遵守
- **全従業員**: 方針に従ったAIの適切な利用

## 5. レビュー

本方針は、少なくとも年1回レビューし、必要に応じて改定する。

## 承認

| 役職 | 氏名 | 日付 | 署名 |
|------|------|------|------|
| [代表取締役] | | | |
"""


def _generate_risk_assessment_summary(
    org_name: str,
    gap: GapAnalysisResult,
    date: str,
) -> str:
    lines = [
        "# AIリスクアセスメント結果サマリー\n",
        f"**組織名**: {org_name}",
        f"**実施日**: {date}",
        "**文書番号**: AIMS-RA-001\n",
        "## 1. 概要\n",
        f"- 評価対象要件数: {gap.total_requirements}",
        f"- 充足: {gap.compliant_count}",
        f"- 部分充足: {gap.partial_count}",
        f"- 未充足: {gap.non_compliant_count}\n",
        "## 2. 要件別評価結果\n",
        "| 要件ID | タイトル | ステータス | スコア | 優先度 |",
        "|--------|---------|----------|--------|--------|",
    ]

    for g in gap.gaps:
        status_val = g.status.value if hasattr(g.status, "value") else str(g.status)
        lines.append(
            f"| {g.req_id} | {g.title} | {status_val} | "
            f"{g.current_score:.2f} | {g.priority} |"
        )

    lines.extend([
        "\n## 3. 高リスク項目\n",
        "以下の項目は優先的に対処が必要:\n",
    ])

    high_gaps = [g for g in gap.gaps if g.priority == "high"]
    for g in high_gaps:
        lines.append(f"### {g.req_id}: {g.title}")
        lines.append(f"- **現状**: {g.gap_description}")
        if g.improvement_actions:
            lines.append("- **改善アクション**:")
            for a in g.improvement_actions:
                lines.append(f"  - {a}")
        lines.append("")

    return "\n".join(lines)


def _generate_iso_compliance_status(
    org_name: str,
    iso_result: ISOCheckResult,
    date: str,
) -> str:
    lines = [
        "# ISO 42001 準拠状況レポート\n",
        f"**組織名**: {org_name}",
        f"**評価日**: {date}",
        "**文書番号**: AIMS-ISO-001\n",
        "## 1. 概要\n",
        f"- 総合スコア: {iso_result.overall_score:.2f}",
        f"- 全要求事項数: {iso_result.total_requirements}",
        f"- 充足: {iso_result.compliant_count}",
        f"- 部分充足: {iso_result.partial_count}",
        f"- 未充足: {iso_result.non_compliant_count}\n",
        "## 2. 条項別サマリー\n",
        "| 条項 | タイトル | 充足率 | スコア | ステータス |",
        "|------|---------|--------|--------|----------|",
    ]

    for cs in iso_result.clause_summaries:
        rate = (
            f"{cs.compliant_count}/{cs.total_requirements}"
            if cs.total_requirements > 0
            else "N/A"
        )
        status_val = cs.status.value if hasattr(cs.status, "value") else str(cs.status)
        lines.append(
            f"| {cs.clause_id} | {cs.title} | {rate} | "
            f"{cs.avg_score:.2f} | {status_val} |"
        )

    return "\n".join(lines)


def _generate_stakeholder_analysis_template(org_name: str, date: str) -> str:
    return f"""# 利害関係者分析

**組織名**: {org_name}
**作成日**: {date}
**文書番号**: AIMS-SH-001

## 利害関係者マッピング

| No | 利害関係者 | 種別 | AIに対する要求・期待 | コミュニケーション方法 |
|----|-----------|------|-------------------|---------------------|
| 1  | 経営層 | 内部 | ビジネス価値の最大化、リスク管理 | マネジメントレビュー |
| 2  | 従業員 | 内部 | AIリテラシー向上、業務効率化 | 教育訓練、社内通知 |
| 3  | 顧客 | 外部 | AI利用の透明性、公平な取扱い | 利用規約、通知 |
| 4  | 規制当局 | 外部 | 法令遵守、報告義務の履行 | 報告書、監査対応 |
| 5  | [追記] | | | |

## 要求事項一覧

| 利害関係者 | 要求事項 | 対応策 | 担当 | 期限 |
|-----------|---------|--------|------|------|
| [記入] | [記入] | [記入] | [記入] | [記入] |
"""


def _generate_internal_audit_checklist(date: str) -> str:
    return f"""# ISO 42001 内部監査チェックリスト

**監査日**: {date}
**監査員**: [記入]
**被監査部門**: [記入]

## チェック項目

### 4. 組織の状況
- [ ] AIに関する外部・内部の課題が特定されているか
- [ ] 利害関係者の要求事項が特定されているか
- [ ] AIMSの適用範囲が明確に定義されているか

### 5. リーダーシップ
- [ ] 経営層のAIMSへのコミットメントが示されているか
- [ ] AI方針が策定・承認・周知されているか
- [ ] 役割・責任・権限が明確か

### 6. 計画
- [ ] AIリスクアセスメントが実施されているか
- [ ] リスクに基づく計画が策定されているか
- [ ] AIMSの目標が設定されているか

### 7. 支援
- [ ] 必要な資源が確保されているか
- [ ] AI関連の教育訓練が実施されているか
- [ ] 必要な文書が管理されているか

### 8. 運用
- [ ] AI影響評価が実施されているか
- [ ] AIシステムのライフサイクル管理が行われているか
- [ ] セキュリティ管理が実施されているか

### 9. パフォーマンス評価
- [ ] モニタリング・測定が行われているか
- [ ] 内部監査が計画的に実施されているか
- [ ] マネジメントレビューが実施されているか

### 10. 改善
- [ ] 不適合に対する是正措置が実施されているか
- [ ] 継続的改善が推進されているか

## 監査所見

| No | 所見 | 分類 | 対応要求 |
|----|------|------|---------|
| 1  | [記入] | [適合/軽微不適合/重大不適合/観察事項] | [記入] |

## 監査結論

[記入]

**監査員署名**: _______________  **日付**: {date}
"""


def _generate_management_review_template(org_name: str, date: str) -> str:
    return f"""# マネジメントレビュー議事録

**組織名**: {org_name}
**開催日**: {date}
**出席者**: [記入]
**議長**: [記入]

## インプット

### 1. 前回マネジメントレビューからの処置状況
[記入]

### 2. AIMSに関する外部・内部の課題の変化
[記入]

### 3. AIリスクアセスメントの結果
[記入]

### 4. 監査結果
- 内部監査: [記入]
- 外部監査: [記入]

### 5. AIインシデントの報告
[記入]

### 6. AIシステムの変更
[記入]

### 7. 改善の機会
[記入]

## アウトプット（意思決定事項）

| No | 決定事項 | 担当 | 期限 |
|----|---------|------|------|
| 1  | [記入] | [記入] | [記入] |

## 次回開催予定
[記入]

**議長署名**: _______________  **日付**: {date}
"""


def _generate_corrective_action_template(date: str) -> str:
    return f"""# 是正措置記録

**文書番号**: CAR-[連番]
**発行日**: {date}

## 1. 不適合の内容

**発見日**: [記入]
**発見源**: [内部監査 / 外部監査 / インシデント / マネジメントレビュー / その他]
**関連条項**: [ISO 42001の条項番号]

**不適合の説明**:
[記入]

## 2. 原因分析

**直接原因**:
[記入]

**根本原因**:
[記入]

**分析手法**: [なぜなぜ分析 / 特性要因図 / その他]

## 3. 是正措置

| No | 措置内容 | 担当 | 期限 | 完了日 |
|----|---------|------|------|--------|
| 1  | [記入] | [記入] | [記入] | |

## 4. 有効性確認

**確認日**: [記入]
**確認者**: [記入]
**確認方法**: [記入]
**結果**: [有効 / 追加措置要]

## 承認

| 役職 | 氏名 | 日付 |
|------|------|------|
| 発行者 | | |
| 承認者 | | |
"""
