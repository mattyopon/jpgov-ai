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


class RiskLevel(str, Enum):
    """EU AI Act準拠のリスクレベル."""

    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class RiskCategory(str, Enum):
    """リスクカテゴリ."""

    BIOMETRIC = "biometric_identification"
    INFRASTRUCTURE = "critical_infrastructure"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    FINANCIAL = "financial"
    LAW_ENFORCEMENT = "law_enforcement"
    HEALTHCARE = "healthcare"
    EMOTION = "emotion_recognition"
    CONTENT_GENERATION = "content_generation"
    CHATBOT = "chatbot"


class TaskStatus(str, Enum):
    """タスクステータス."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class PolicyType(str, Enum):
    """ポリシー種別."""

    AI_USAGE = "ai_usage"
    RISK_MANAGEMENT = "risk_management"
    ETHICS = "ethics"
    DATA_MANAGEMENT = "data_management"
    INCIDENT_RESPONSE = "incident_response"


class ExportFormat(str, Enum):
    """エクスポートフォーマット."""

    CSV = "csv"
    JSON = "json"


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


# ── ISO 42001 Check ──────────────────────────────────────────────

class ISOCheckItem(BaseModel):
    """ISO 42001個別要求事項のチェック結果."""

    req_id: str
    clause: str
    title: str
    description: str
    status: ComplianceStatus
    score: float
    meti_mapping: list[str] = Field(default_factory=list)
    meti_mapping_titles: list[str] = Field(default_factory=list)


class ISOClauseSummary(BaseModel):
    """ISO 42001条項サマリー."""

    clause_id: str
    title: str
    total_requirements: int
    compliant_count: int
    avg_score: float
    status: ComplianceStatus


class ISOCheckResult(BaseModel):
    """ISO 42001チェック結果."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    gap_analysis_id: str
    total_requirements: int
    compliant_count: int
    partial_count: int
    non_compliant_count: int
    not_assessed_count: int = 0
    overall_score: float
    items: list[ISOCheckItem] = Field(default_factory=list)
    clause_summaries: list[ISOClauseSummary] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Risk Assessment ──────────────────────────────────────────────

class RiskAssessmentItem(BaseModel):
    """リスクアセスメント個別項目."""

    question_key: str
    question: str
    answer: bool
    risk_level: RiskLevel
    category: RiskCategory


class RiskAssessmentResult(BaseModel):
    """リスクアセスメント結果."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    system_name: str
    system_description: str = ""
    overall_risk_level: RiskLevel
    items: list[RiskAssessmentItem] = Field(default_factory=list)
    additional_requirements: list[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RiskAssessmentRequest(BaseModel):
    """リスクアセスメントリクエスト."""

    organization_id: str
    system_name: str
    system_description: str = ""
    answers: dict[str, bool]


# ── Task Management ──────────────────────────────────────────────

class ActionTask(BaseModel):
    """改善アクションタスク."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    gap_req_id: str = ""
    title: str
    description: str = ""
    assignee: str = ""
    due_date: str = ""
    priority: str = "medium"
    status: TaskStatus = TaskStatus.TODO
    notes: list[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ActionTaskCreate(BaseModel):
    """タスク作成リクエスト."""

    organization_id: str
    gap_req_id: str = ""
    title: str
    description: str = ""
    assignee: str = ""
    due_date: str = ""
    priority: str = "medium"


class ActionTaskUpdate(BaseModel):
    """タスク更新リクエスト."""

    status: TaskStatus | None = None
    assignee: str | None = None
    due_date: str | None = None
    priority: str | None = None
    note: str | None = None


class TaskBoardSummary(BaseModel):
    """カンバンボードサマリー."""

    organization_id: str
    total: int
    todo_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int = 0
    todo_tasks: list[ActionTask] = Field(default_factory=list)
    in_progress_tasks: list[ActionTask] = Field(default_factory=list)
    done_tasks: list[ActionTask] = Field(default_factory=list)


# ── Policy Generator ─────────────────────────────────────────────

class PolicyDocument(BaseModel):
    """生成されたポリシー文書."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    policy_type: PolicyType
    title: str
    sections: list[dict[str, str]] = Field(default_factory=list)
    full_text: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PolicyGenerateRequest(BaseModel):
    """ポリシー生成リクエスト."""

    organization_id: str
    organization_name: str
    policy_type: PolicyType


# ── Export ────────────────────────────────────────────────────────

class ExportPackage(BaseModel):
    """エクスポートパッケージ."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    package_type: str
    files: dict[str, str] = Field(default_factory=dict)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Multi-Regulation Dashboard ───────────────────────────────────

class RegulationStatus(BaseModel):
    """個別規制の準拠状況."""

    regulation_name: str
    total_requirements: int
    compliant_count: int
    partial_count: int
    non_compliant_count: int
    compliance_rate: float
    overall_score: float


class MultiRegulationDashboard(BaseModel):
    """マルチ規制ダッシュボード."""

    organization_id: str
    meti_status: RegulationStatus | None = None
    iso_status: RegulationStatus | None = None
    act_status: RegulationStatus | None = None
    overall_compliance_rate: float = 0.0
    priority_actions: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
