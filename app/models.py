# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

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
    VENDOR_MANAGEMENT = "vendor_management"
    MODEL_MANAGEMENT = "model_management"
    TRANSPARENCY = "transparency"
    FAIRNESS = "fairness"
    AUDIT = "audit"


class ExportFormat(str, Enum):
    """エクスポートフォーマット."""

    CSV = "csv"
    JSON = "json"


class UserRole(str, Enum):
    """組織内ユーザーロール."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class ApprovalStatus(str, Enum):
    """承認ステータス."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"  # 差し戻し


class IncidentType(str, Enum):
    """AIインシデント種別."""

    HALLUCINATION = "hallucination"
    BIAS = "bias"
    DATA_LEAK = "data_leak"
    SERVICE_OUTAGE = "service_outage"
    SECURITY_BREACH = "security_breach"
    PRIVACY_VIOLATION = "privacy_violation"
    SAFETY = "safety"
    QUALITY = "quality"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    """インシデント重大度."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    """インシデント対応状況."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IndustryType(str, Enum):
    """業界分類."""

    IT = "IT・通信"
    FINANCE = "金融・保険"
    MANUFACTURING = "製造"
    HEALTHCARE = "医療・ヘルスケア"
    RETAIL = "小売・EC"
    PUBLIC = "公共・行政"
    EDUCATION = "教育"
    OTHER = "その他"


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


# ── Team / Organization Member ───────────────────────────────────

class OrganizationMember(BaseModel):
    """組織メンバー."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    user_id: str
    email: str = ""
    display_name: str = ""
    role: UserRole = UserRole.MEMBER
    invited_by: str = ""
    joined_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class OrganizationMemberInvite(BaseModel):
    """メンバー招待リクエスト."""

    organization_id: str
    email: str
    role: UserRole = UserRole.MEMBER


class OrganizationMemberUpdate(BaseModel):
    """メンバー更新リクエスト."""

    role: UserRole | None = None


class TeamSummary(BaseModel):
    """チームサマリー."""

    organization_id: str
    organization_name: str
    member_count: int
    members: list[OrganizationMember] = Field(default_factory=list)


# ── Role Permissions ─────────────────────────────────────────────

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "owner": [
        "org.manage", "org.delete", "member.invite", "member.remove",
        "member.change_role", "assessment.run", "assessment.view",
        "gap.run", "gap.view", "policy.create", "policy.approve",
        "task.manage", "evidence.manage", "report.generate",
        "audit.view", "benchmark.view", "review.manage",
        "approval.approve", "approval.create",
    ],
    "admin": [
        "org.manage", "member.invite", "member.remove",
        "member.change_role", "assessment.run", "assessment.view",
        "gap.run", "gap.view", "policy.create", "policy.approve",
        "task.manage", "evidence.manage", "report.generate",
        "audit.view", "benchmark.view", "review.manage",
        "approval.approve", "approval.create",
    ],
    "member": [
        "assessment.run", "assessment.view",
        "gap.run", "gap.view", "policy.create",
        "task.manage", "evidence.manage", "report.generate",
        "benchmark.view", "review.manage",
        "approval.create",
    ],
    "auditor": [
        "assessment.view", "gap.view", "audit.view",
        "evidence.manage", "report.generate",
        "benchmark.view", "approval.approve",
    ],
    "viewer": [
        "assessment.view", "gap.view", "benchmark.view",
    ],
}


# ── Assessment Snapshot / Timeline ───────────────────────────────

class AssessmentSnapshot(BaseModel):
    """診断結果のスナップショット（時系列用）."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    assessment_id: str
    overall_score: float
    maturity_level: int
    category_scores: dict[str, float] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TimelineEntry(BaseModel):
    """時系列のエントリ."""

    assessment_id: str
    timestamp: str
    overall_score: float
    maturity_level: int
    category_scores: dict[str, float] = Field(default_factory=dict)
    delta_from_previous: float = 0.0


class TimelineResponse(BaseModel):
    """時系列レスポンス."""

    organization_id: str
    entries: list[TimelineEntry] = Field(default_factory=list)
    trend: str = ""  # "improving" / "stable" / "declining"
    predicted_level3_date: str = ""


# ── Review Cycle ─────────────────────────────────────────────────

class ReviewCycle(BaseModel):
    """定期レビューサイクル."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    cycle_type: str = "quarterly"  # quarterly / semi_annual / annual
    start_date: str = ""
    next_review_date: str = ""
    created_by: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ReviewCycleCreate(BaseModel):
    """レビューサイクル作成リクエスト."""

    organization_id: str
    cycle_type: str = "quarterly"
    start_date: str = ""


class ReviewRecord(BaseModel):
    """レビュー実施記録."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    cycle_id: str
    review_date: str = ""
    assessment_id: str = ""
    reviewer: str = ""
    notes: str = ""
    delta_report: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ReviewRecordCreate(BaseModel):
    """レビュー記録作成リクエスト."""

    organization_id: str
    cycle_id: str
    review_date: str = ""
    assessment_id: str = ""
    reviewer: str = ""
    notes: str = ""


# ── Industry Benchmark ───────────────────────────────────────────

class CategoryBenchmark(BaseModel):
    """カテゴリ別ベンチマーク."""

    category_id: str
    avg_score: float
    sample_count: int


class IndustryBenchmark(BaseModel):
    """業界ベンチマーク."""

    industry: str
    size_bucket: str = ""  # small / medium / large / enterprise / all
    sample_count: int = 0
    avg_overall_score: float = 0.0
    avg_maturity_level: float = 0.0
    category_benchmarks: dict[str, CategoryBenchmark] = Field(default_factory=dict)
    percentile_thresholds: dict[str, float] = Field(default_factory=dict)
    top_improvement_areas: list[str] = Field(default_factory=list)
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MyBenchmarkPosition(BaseModel):
    """自社のベンチマーク内ポジション."""

    organization_id: str
    industry: str
    my_score: float
    industry_avg: float
    percentile: float = 0.0  # 上位何%か
    gap_areas: list[dict[str, Any]] = Field(default_factory=list)


# ── Approval Workflow ────────────────────────────────────────────

class ApprovalRequest(BaseModel):
    """承認リクエスト."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    request_type: str = ""  # policy_change / review_completion / etc.
    title: str = ""
    description: str = ""
    resource_type: str = ""
    resource_id: str = ""
    requested_by: str = ""
    approver_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    comment: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ApprovalRequestCreate(BaseModel):
    """承認リクエスト作成."""

    organization_id: str
    request_type: str = ""
    title: str = ""
    description: str = ""
    resource_type: str = ""
    resource_id: str = ""
    approver_id: str = ""


class ApprovalAction(BaseModel):
    """承認/却下/差し戻しアクション."""

    action: ApprovalStatus  # approved / rejected / returned
    comment: str = ""


# ── Incident Management ─────────────────────────────────────────

class Incident(BaseModel):
    """AIインシデントレコード."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    title: str
    description: str = ""
    incident_type: IncidentType = IncidentType.OTHER
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    affected_system: str = ""
    impact_description: str = ""
    status: IncidentStatus = IncidentStatus.OPEN
    detected_by: str = ""
    detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str = ""
    related_requirements: list[str] = Field(default_factory=list)
    regulatory_report_required: bool = False
    regulatory_report_sent: bool = False
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class IncidentCreate(BaseModel):
    """インシデント作成リクエスト."""

    organization_id: str
    title: str
    description: str = ""
    incident_type: IncidentType = IncidentType.OTHER
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    affected_system: str = ""
    impact_description: str = ""
    detected_by: str = ""
    related_requirements: list[str] = Field(default_factory=list)
    regulatory_report_required: bool = False


class IncidentUpdate(BaseModel):
    """インシデント更新リクエスト."""

    status: IncidentStatus | None = None
    severity: IncidentSeverity | None = None
    impact_description: str | None = None
    resolved_at: str | None = None
    regulatory_report_sent: bool | None = None


class IncidentRCA(BaseModel):
    """根本原因分析（RCA）."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    root_cause: str = ""
    contributing_factors: list[str] = Field(default_factory=list)
    corrective_actions: list[str] = Field(default_factory=list)
    preventive_actions: list[str] = Field(default_factory=list)
    lessons_learned: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class IncidentRCACreate(BaseModel):
    """RCA作成リクエスト."""

    incident_id: str
    root_cause: str = ""
    contributing_factors: list[str] = Field(default_factory=list)
    corrective_actions: list[str] = Field(default_factory=list)
    preventive_actions: list[str] = Field(default_factory=list)
    lessons_learned: str = ""


class IncidentStats(BaseModel):
    """インシデント統計."""

    organization_id: str
    total_count: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    avg_resolution_hours: float = 0.0
    open_count: int = 0


# ── Integration Config ──────────────────────────────────────────

class IntegrationConfig(BaseModel):
    """外部連携設定."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    integration_type: str = "slack"  # slack / teams / etc.
    webhook_url: str = ""
    enabled: bool = True
    notify_review_reminder: bool = True
    notify_approval: bool = True
    notify_incident: bool = True
    notify_score_drop: bool = True
    notify_new_gap: bool = True
    language: str = "ja"  # ja / en
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class IntegrationConfigCreate(BaseModel):
    """連携設定作成リクエスト."""

    organization_id: str
    integration_type: str = "slack"
    webhook_url: str = ""
    enabled: bool = True
    language: str = "ja"


class IntegrationConfigUpdate(BaseModel):
    """連携設定更新リクエスト."""

    webhook_url: str | None = None
    enabled: bool | None = None
    notify_review_reminder: bool | None = None
    notify_approval: bool | None = None
    notify_incident: bool | None = None
    notify_score_drop: bool | None = None
    notify_new_gap: bool | None = None
    language: str | None = None


# ── Enhanced Evidence ───────────────────────────────────────────

class EvidenceFile(BaseModel):
    """エビデンスファイル（メタデータ強化版）."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    requirement_id: str
    filename: str
    description: str = ""
    file_type: str = ""
    file_path: str = ""
    file_size: int = 0
    file_hash: str = ""
    uploaded_by: str = ""
    expires_at: str = ""  # 有効期限（空=無期限）
    uploaded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Monthly Report ──────────────────────────────────────────────

class MonthlyReport(BaseModel):
    """月次自動レポート."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    year: int
    month: int
    score_summary: dict[str, Any] = Field(default_factory=dict)
    gap_summary: dict[str, Any] = Field(default_factory=dict)
    incident_summary: dict[str, Any] = Field(default_factory=dict)
    evidence_coverage: float = 0.0
    benchmark_comparison: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Phase 3: Data Flywheel — Pattern Learning ───────────────────

class GapPattern(BaseModel):
    """Gapパターン: 業界×規模×要件IDごとの出現パターン."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    industry: str
    size_bucket: str = ""
    requirement_id: str
    occurrence_count: int = 0
    resolved_count: int = 0
    resolution_rate: float = 0.0  # resolved / occurrence
    typical_actions: list[str] = Field(default_factory=list)
    avg_resolution_days: float = 0.0
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class PatternMatch(BaseModel):
    """パターンマッチング結果: 新規診断時の推奨."""

    requirement_id: str
    requirement_title: str = ""
    industry: str
    occurrence_count: int = 0
    resolution_rate: float = 0.0
    recommended_actions: list[str] = Field(default_factory=list)
    avg_resolution_days: float = 0.0
    priority_suggestion: str = ""  # high / medium / low


class PatternLearningResult(BaseModel):
    """パターン学習の全体結果."""

    organization_id: str = ""
    industry: str
    size_bucket: str = ""
    matches: list[PatternMatch] = Field(default_factory=list)
    total_patterns: int = 0
    message: str = ""


# ── Phase 3: Data Flywheel — Regulatory Monitor ─────────────────

class RegulatoryUpdate(BaseModel):
    """規制変更情報."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    regulation_name: str  # e.g. "METI AI事業者ガイドライン", "ISO 42001", "AI推進法"
    title: str
    description: str = ""
    change_type: str = "amendment"  # amendment / new / repeal
    affected_requirements: list[str] = Field(default_factory=list)
    effective_date: str = ""
    deadline: str = ""
    severity: str = "medium"  # high / medium / low
    created_by: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RegulatoryUpdateCreate(BaseModel):
    """規制変更登録リクエスト."""

    regulation_name: str
    title: str
    description: str = ""
    change_type: str = "amendment"
    affected_requirements: list[str] = Field(default_factory=list)
    effective_date: str = ""
    deadline: str = ""
    severity: str = "medium"
    created_by: str = ""


class RegulatoryImpact(BaseModel):
    """規制変更の顧客への影響分析."""

    update_id: str
    organization_id: str
    regulation_name: str
    title: str
    affected_requirements: list[str] = Field(default_factory=list)
    current_scores: dict[str, float] = Field(default_factory=dict)
    estimated_impact: str = ""  # "スコアが2.5→2.0に低下する可能性"
    recommended_actions: list[str] = Field(default_factory=list)
    deadline: str = ""
    severity: str = "medium"


class RegulatoryImpactReport(BaseModel):
    """規制変更影響レポート."""

    organization_id: str
    impacts: list[RegulatoryImpact] = Field(default_factory=list)
    total_updates: int = 0
    high_severity_count: int = 0


# ── Phase 3: Data Flywheel — Action Analytics ───────────────────

class ActionROI(BaseModel):
    """改善アクションのROI."""

    task_id: str
    action_type: str = ""
    requirement_id: str = ""
    score_before: float = 0.0
    score_after: float = 0.0
    score_delta: float = 0.0
    effort_hours: float = 0.0
    roi: float = 0.0  # score_delta / effort_hours (0 if effort=0)


class ActionRanking(BaseModel):
    """改善アクションの効果ランキング."""

    organization_id: str = ""
    rankings: list[ActionROI] = Field(default_factory=list)
    industry_comparison: list[dict[str, Any]] = Field(default_factory=list)
    best_roi_action_type: str = ""
    avg_score_improvement: float = 0.0


class ActionEffectRecord(BaseModel):
    """改善アクション効果記録リクエスト."""

    organization_id: str
    task_id: str
    action_type: str = ""
    requirement_id: str = ""
    score_before: float = 0.0
    score_after: float = 0.0
    effort_hours: float = 0.0


# ── Phase 3: Data Flywheel — Prediction ─────────────────────────

class ScorePrediction(BaseModel):
    """スコア予測結果."""

    organization_id: str
    current_score: float = 0.0
    predicted_score: float = 0.0
    prediction_date: str = ""  # いつ時点の予測か
    days_to_level3: int = 0  # Level 3到達まであと何日（0=既に達成 or 予測不能）
    days_to_target: int = 0
    target_score: float = 2.4  # Level 3
    trend: str = "stable"  # improving / stable / declining
    confidence: str = "low"  # low / medium / high
    monthly_rate: float = 0.0  # 月あたり改善速度
    required_actions: int = 0  # 目標到達に必要な推定アクション数
    regulatory_impact_adjustment: float = 0.0  # 規制変更による調整
    category_predictions: dict[str, float] = Field(default_factory=dict)


# ── AutoFix ────────────────────────────────────────────────────────

class DocumentStatus(str, Enum):
    """生成文書のステータス."""

    DRAFT = "draft"
    APPROVED = "approved"


class GeneratedDocument(BaseModel):
    """AutoFixで生成された文書."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    doc_type: str  # policy / checklist / template / procedure
    status: DocumentStatus = DocumentStatus.DRAFT


class ChecklistItem(BaseModel):
    """チェックリスト項目."""

    text: str
    checked: bool = False


class AutoFixTask(BaseModel):
    """AutoFix生成タスク."""

    title: str
    description: str = ""
    assignee_role: str = ""
    deadline_days: int = 30
    depends_on: list[int] = Field(default_factory=list)


class SelfCheckItem(BaseModel):
    """セルフチェック質問."""

    question: str
    expected_answer: str = "yes"
    answered: bool = False


class AutoFixResult(BaseModel):
    """1要件に対するAutoFix結果."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requirement_id: str
    requirement_title: str = ""
    generated_documents: list[GeneratedDocument] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    tasks: list[AutoFixTask] = Field(default_factory=list)
    self_check_questions: list[SelfCheckItem] = Field(default_factory=list)
    status: str = "generated"  # generated / in_progress / completed
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
