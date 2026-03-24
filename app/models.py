# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""Pydantic models for JPGovAI API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────

class ComplianceStatus(str, Enum):
    """要件の充足状態."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class MaturityLevel(int, Enum):
    """AI Governance 成熟度レベル."""

    LEVEL_1 = 1  # 初期 — 場当たり的
    LEVEL_2 = 2  # 反復可能 — 基本プロセスあり
    LEVEL_3 = 3  # 定義済み — 標準化されたプロセス
    LEVEL_4 = 4  # 管理 — 定量的管理
    LEVEL_5 = 5  # 最適化 — 継続的改善


# ── Organization ──────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    """組織作成リクエスト."""

    name: str
    industry: str = ""
    size: str = ""  # small / medium / large / enterprise
    ai_role: str = ""  # developer / provider / user


class OrganizationResponse(BaseModel):
    """組織レスポンス."""

    id: str
    name: str
    industry: str
    size: str
    ai_role: str
    created_at: str


# ── Assessment ────────────────────────────────────────────────────

class AnswerItem(BaseModel):
    """1問分の回答."""

    question_id: str
    selected_index: int  # 選択肢のインデックス (0-4)


class AssessmentRequest(BaseModel):
    """自己診断リクエスト."""

    organization_id: str
    answers: list[AnswerItem]


class CategoryScore(BaseModel):
    """カテゴリ別スコア."""

    category_id: str
    category_title: str
    score: float  # 0.0 - 4.0
    max_score: float = 4.0
    maturity_level: int  # 1-5
    question_count: int


class AssessmentResult(BaseModel):
    """診断結果."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    overall_score: float  # 0.0 - 4.0
    maturity_level: int  # 1-5
    category_scores: list[CategoryScore]
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Gap Analysis ──────────────────────────────────────────────────

class RequirementGap(BaseModel):
    """個別要件のギャップ."""

    req_id: str
    category_id: str
    title: str
    status: ComplianceStatus
    current_score: float
    gap_description: str = ""
    improvement_actions: list[str] = Field(default_factory=list)
    priority: str = "medium"  # high / medium / low


class GapAnalysisResult(BaseModel):
    """ギャップ分析結果."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    assessment_id: str
    total_requirements: int
    compliant_count: int
    partial_count: int
    non_compliant_count: int
    gaps: list[RequirementGap]
    ai_recommendations: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Evidence ──────────────────────────────────────────────────────

class EvidenceUpload(BaseModel):
    """エビデンスアップロードリクエスト."""

    organization_id: str
    requirement_id: str
    filename: str
    description: str = ""
    file_type: str = ""  # policy / test_result / audit_log / training_record / other


class EvidenceRecord(BaseModel):
    """エビデンスレコード."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    requirement_id: str
    filename: str
    description: str
    file_type: str
    file_path: str = ""
    uploaded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EvidenceSummary(BaseModel):
    """エビデンス充足率サマリー."""

    organization_id: str
    total_requirements: int
    requirements_with_evidence: int
    coverage_rate: float  # 0.0 - 1.0
    by_category: dict[str, dict[str, Any]]


# ── Report ────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    """レポート生成リクエスト."""

    organization_id: str
    assessment_id: str
    gap_analysis_id: str
    include_evidence: bool = True


class ReportResponse(BaseModel):
    """レポート生成レスポンス."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    filename: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    content_preview: str = ""


# ── Audit Trail ───────────────────────────────────────────────────

class AuditEventResponse(BaseModel):
    """監査イベントレスポンス."""

    event_id: str
    sequence: int
    timestamp: str
    action: str
    actor: str
    resource_type: str
    resource_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    event_hash: str
    previous_hash: str


class AuditChainStatus(BaseModel):
    """監査チェーンの整合性状態."""

    total_events: int
    chain_valid: bool
    merkle_root: str
    errors: list[str] = Field(default_factory=list)
