# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""FastAPI application for JPGovAI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException

from app.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenPayload,
    authenticate_user,
    create_token,
    get_current_user,
    register_user,
)
from app.db.database import OrganizationRow, get_db
from app.guidelines.ai_promotion_act import ACT_CHAPTERS, all_act_requirements
from app.guidelines.iso42001 import ISO_CLAUSES, all_iso_requirements, get_meti_to_iso_mapping
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, CATEGORIES
from app.models import (
    ActionEffectRecord,  # noqa: F401 (Phase 3: used in endpoint body)
    ActionRanking,  # noqa: F401 (Phase 3: response_model)
    ActionROI,  # noqa: F401 (Phase 3: response_model)
    ActionTask,
    ActionTaskCreate,
    ActionTaskUpdate,
    ApprovalAction,
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalStatus,
    AssessmentRequest,
    AssessmentResult,
    AuditChainStatus,
    AuditEventResponse,
    EvidenceRecord,
    EvidenceSummary,
    EvidenceUpload,
    ExportFormat,
    ExportPackage,
    GapAnalysisResult,
    Incident,
    IncidentCreate,
    IncidentRCA,
    IncidentRCACreate,
    IncidentSeverity,
    IncidentStats,
    IncidentStatus,
    IncidentUpdate,
    IndustryBenchmark,
    IntegrationConfig,
    IntegrationConfigCreate,
    IntegrationConfigUpdate,
    ISOCheckResult,
    MonthlyReport,
    MultiRegulationDashboard,
    MyBenchmarkPosition,
    OrganizationCreate,
    OrganizationMember,
    OrganizationMemberInvite,
    OrganizationMemberUpdate,
    OrganizationResponse,
    PolicyDocument,
    PolicyGenerateRequest,
    RegulatoryUpdateCreate,  # noqa: F401 (Phase 3: used in endpoint body)
    ReportRequest,
    ReportResponse,
    ReviewCycle,
    ReviewCycleCreate,
    ReviewRecord,
    ReviewRecordCreate,
    RiskAssessmentRequest,
    RiskAssessmentResult,
    ScorePrediction,  # noqa: F401 (Phase 3: response_model)
    TaskBoardSummary,
    TeamSummary,
    TimelineResponse,
)
from app.services.assessment import get_assessment, run_assessment
from app.services.audit_trail import get_audit_ledger
from app.services.dashboard import build_multi_regulation_dashboard
from app.services.evidence import get_evidence_summary, list_evidence, upload_evidence
from app.services.export_service import (
    export_assessment,
    export_gap_analysis,
    generate_iso_certification_package,
    generate_meti_report_package,
)
from app.services.gap_analysis import get_gap_analysis, run_gap_analysis
from app.services.iso_check import run_iso_check
from app.services.policy_generator import generate_all_policies, generate_policy, get_available_policy_types
from app.services.report_gen import generate_report
from app.services.risk_assessment import (
    get_risk_assessment,
    get_risk_questions,
    list_risk_assessments,
    run_risk_assessment,
)
from app.services.task_manager import (
    create_task,
    create_tasks_from_gap_analysis,
    get_board_summary,
    get_task,
    list_tasks,
    update_task,
)

app = FastAPI(
    title="JPGovAI",
    description="ISO 42001認証準備 & AIガバナンス管理 SaaS - METI AI事業者ガイドライン v1.1 / ISO 42001 / AI推進法 準拠",
    version="0.2.0",
)


# ── Startup ───────────────────────────────────────────────────────

@app.on_event("startup")
def startup() -> None:
    """DB初期化."""
    get_db()


# ── Auth ─────────────────────────────────────────────────────────

@app.post("/api/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest) -> AuthResponse:
    """ユーザー登録."""
    user = register_user(req.email, req.password, req.display_name)
    token = create_token(user["user_id"], user["email"])
    return AuthResponse(
        access_token=token,
        user_id=user["user_id"],
        email=user["email"],
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(req: LoginRequest) -> AuthResponse:
    """ログイン."""
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["user_id"], user["email"])
    return AuthResponse(
        access_token=token,
        user_id=user["user_id"],
        email=user["email"],
    )


# ── Organizations ─────────────────────────────────────────────────

@app.post("/api/organizations", response_model=OrganizationResponse)
def create_organization(
    org: OrganizationCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> OrganizationResponse:
    """組織を登録."""
    db = get_db()
    org_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with db.get_session() as session:
        row = OrganizationRow(
            id=org_id,
            name=org.name,
            industry=org.industry,
            size=org.size,
            ai_role=org.ai_role,
            created_at=now,
        )
        session.add(row)
        session.commit()

    # 監査ログ
    ledger = get_audit_ledger()
    ledger.append(
        action="organization.create",
        resource_type="organization",
        resource_id=org_id,
        details={"name": org.name},
    )

    return OrganizationResponse(
        id=org_id,
        name=org.name,
        industry=org.industry,
        size=org.size,
        ai_role=org.ai_role,
        created_at=now,
    )


# ── Guidelines ────────────────────────────────────────────────────

@app.get("/api/guidelines/categories")
def get_categories(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """ガイドラインカテゴリ一覧."""
    return [
        {
            "category_id": c.category_id,
            "title": c.title,
            "description": c.description,
            "requirement_count": len(c.requirements),
        }
        for c in CATEGORIES
    ]


@app.get("/api/guidelines/requirements")
def get_requirements(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """全要件一覧."""
    reqs = []
    for c in CATEGORIES:
        for r in c.requirements:
            reqs.append(
                {
                    "req_id": r.req_id,
                    "category_id": r.category_id,
                    "title": r.title,
                    "description": r.description,
                    "target_roles": r.target_roles,
                }
            )
    return reqs


@app.get("/api/guidelines/questions")
def get_questions(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """質問票一覧."""
    return [
        {
            "question_id": q.question_id,
            "category_id": q.category_id,
            "text": q.text,
            "options": q.options,
        }
        for q in ASSESSMENT_QUESTIONS
    ]


# ── ISO 42001 Guidelines ────────────────────────────────────────

@app.get("/api/guidelines/iso42001/clauses")
def get_iso_clauses(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """ISO 42001条項一覧."""
    return [
        {
            "clause_id": c.clause_id,
            "title": c.title,
            "description": c.description,
            "requirement_count": len(c.requirements),
        }
        for c in ISO_CLAUSES
    ]


@app.get("/api/guidelines/iso42001/requirements")
def get_iso_requirements(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """ISO 42001全要求事項一覧."""
    return [
        {
            "req_id": r.req_id,
            "clause": r.clause,
            "title": r.title,
            "description": r.description,
            "meti_mapping": r.meti_mapping,
        }
        for r in all_iso_requirements()
    ]


@app.get("/api/guidelines/iso42001/cross-mapping")
def get_cross_mapping(
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """METI <-> ISO 42001 クロスマッピング."""
    return get_meti_to_iso_mapping()


# ── AI推進法 Guidelines ──────────────────────────────────────────

@app.get("/api/guidelines/ai-promotion-act/chapters")
def get_act_chapters(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """AI推進法 章一覧."""
    return [
        {
            "chapter_id": c.chapter_id,
            "title": c.title,
            "description": c.description,
            "requirement_count": len(c.requirements),
        }
        for c in ACT_CHAPTERS
    ]


@app.get("/api/guidelines/ai-promotion-act/requirements")
def get_act_requirements(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """AI推進法 全要件一覧."""
    return [
        {
            "req_id": r.req_id,
            "article": r.article,
            "title": r.title,
            "description": r.description,
            "obligation_type": r.obligation_type,
            "meti_mapping": r.meti_mapping,
            "iso_mapping": r.iso_mapping,
        }
        for r in all_act_requirements()
    ]


# ── Assessment ────────────────────────────────────────────────────

@app.post("/api/assessment", response_model=AssessmentResult)
def submit_assessment(
    req: AssessmentRequest,
    _user: TokenPayload = Depends(get_current_user),
) -> AssessmentResult:
    """自己診断を実行."""
    result = run_assessment(req.organization_id, req.answers)

    ledger = get_audit_ledger()
    ledger.append(
        action="assessment.submit",
        resource_type="assessment",
        resource_id=result.id,
        details={
            "organization_id": req.organization_id,
            "overall_score": result.overall_score,
            "maturity_level": result.maturity_level,
        },
    )

    return result


@app.get("/api/assessment/{assessment_id}", response_model=AssessmentResult)
def get_assessment_by_id(
    assessment_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> AssessmentResult:
    """診断結果を取得."""
    result = get_assessment(assessment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return result


# ── Gap Analysis ──────────────────────────────────────────────────

@app.post("/api/gap-analysis", response_model=GapAnalysisResult)
async def submit_gap_analysis(
    assessment_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> GapAnalysisResult:
    """ギャップ分析を実行."""
    assessment = get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    result = await run_gap_analysis(assessment)

    ledger = get_audit_ledger()
    ledger.append(
        action="gap_analysis.submit",
        resource_type="gap_analysis",
        resource_id=result.id,
        details={
            "assessment_id": assessment_id,
            "compliant": result.compliant_count,
            "partial": result.partial_count,
            "non_compliant": result.non_compliant_count,
        },
    )

    return result


@app.get("/api/gap-analysis/{gap_id}", response_model=GapAnalysisResult)
def get_gap_analysis_by_id(
    gap_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> GapAnalysisResult:
    """ギャップ分析結果を取得."""
    result = get_gap_analysis(gap_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")
    return result


# ── ISO 42001 Check ──────────────────────────────────────────────

@app.post("/api/iso-check", response_model=ISOCheckResult)
def submit_iso_check(
    gap_analysis_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> ISOCheckResult:
    """ISO 42001準拠チェックを実行."""
    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    result = run_iso_check(gap)

    ledger = get_audit_ledger()
    ledger.append(
        action="iso_check.submit",
        resource_type="iso_check",
        resource_id=result.id,
        details={
            "gap_analysis_id": gap_analysis_id,
            "compliant": result.compliant_count,
            "overall_score": result.overall_score,
        },
    )

    return result


# ── Risk Assessment ──────────────────────────────────────────────

@app.get("/api/risk-assessment/questions")
def get_risk_questions_api(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """リスク分類用の質問一覧."""
    return get_risk_questions()


@app.post("/api/risk-assessment", response_model=RiskAssessmentResult)
def submit_risk_assessment(
    req: RiskAssessmentRequest,
    _user: TokenPayload = Depends(get_current_user),
) -> RiskAssessmentResult:
    """リスクアセスメントを実行."""
    result = run_risk_assessment(
        organization_id=req.organization_id,
        system_name=req.system_name,
        system_description=req.system_description,
        answers=req.answers,
    )

    ledger = get_audit_ledger()
    ledger.append(
        action="risk_assessment.submit",
        resource_type="risk_assessment",
        resource_id=result.id,
        details={
            "system_name": req.system_name,
            "risk_level": result.overall_risk_level.value,
        },
    )

    return result


@app.get("/api/risk-assessment/{assessment_id}", response_model=RiskAssessmentResult)
def get_risk_assessment_by_id(
    assessment_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> RiskAssessmentResult:
    """リスクアセスメント結果を取得."""
    result = get_risk_assessment(assessment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    return result


@app.get("/api/risk-assessments/{organization_id}", response_model=list[RiskAssessmentResult])
def get_risk_assessments(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[RiskAssessmentResult]:
    """組織のリスクアセスメント一覧."""
    return list_risk_assessments(organization_id)


# ── Task Management ──────────────────────────────────────────────

@app.post("/api/tasks", response_model=ActionTask)
def create_task_api(
    task_data: ActionTaskCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> ActionTask:
    """改善タスクを作成."""
    return create_task(task_data)


@app.get("/api/tasks/{task_id}", response_model=ActionTask)
def get_task_api(
    task_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> ActionTask:
    """タスクを取得."""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}", response_model=ActionTask)
def update_task_api(
    task_id: str,
    update: ActionTaskUpdate,
    _user: TokenPayload = Depends(get_current_user),
) -> ActionTask:
    """タスクを更新."""
    task = update_task(task_id, update)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/tasks/org/{organization_id}", response_model=list[ActionTask])
def list_tasks_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
    status: str | None = None,
) -> list[ActionTask]:
    """組織のタスク一覧."""
    from app.models import TaskStatus as TS
    task_status = None
    if status:
        try:
            task_status = TS(status)
        except ValueError:
            pass
    return list_tasks(organization_id, task_status)


@app.get("/api/tasks/board/{organization_id}", response_model=TaskBoardSummary)
def get_board_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> TaskBoardSummary:
    """カンバンボードサマリーを取得."""
    return get_board_summary(organization_id)


@app.post("/api/tasks/from-gap-analysis", response_model=list[ActionTask])
def create_tasks_from_gap_api(
    organization_id: str,
    gap_analysis_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[ActionTask]:
    """ギャップ分析結果から自動的にタスクを生成."""
    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    gaps_dicts = [g.model_dump() for g in gap.gaps]
    tasks = create_tasks_from_gap_analysis(organization_id, gaps_dicts)

    ledger = get_audit_ledger()
    ledger.append(
        action="tasks.auto_create",
        resource_type="task_batch",
        resource_id=gap_analysis_id,
        details={"task_count": len(tasks)},
    )

    return tasks


# ── Policy Generator ─────────────────────────────────────────────

@app.get("/api/policies/types")
def get_policy_types(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """利用可能なポリシータイプ一覧."""
    return get_available_policy_types()


@app.post("/api/policies/generate", response_model=PolicyDocument)
def generate_policy_api(
    req: PolicyGenerateRequest,
    _user: TokenPayload = Depends(get_current_user),
) -> PolicyDocument:
    """ポリシーテンプレートを生成."""
    result = generate_policy(req.policy_type, req.organization_name, req.organization_id)

    ledger = get_audit_ledger()
    ledger.append(
        action="policy.generate",
        resource_type="policy",
        resource_id=result.id,
        details={"policy_type": req.policy_type.value},
    )

    return result


@app.post("/api/policies/generate-all", response_model=list[PolicyDocument])
def generate_all_policies_api(
    organization_id: str,
    organization_name: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[PolicyDocument]:
    """全ポリシーをまとめて生成."""
    return generate_all_policies(organization_name, organization_id)


# ── Multi-Regulation Dashboard ───────────────────────────────────

@app.get("/api/dashboard/{organization_id}", response_model=MultiRegulationDashboard)
def get_dashboard(
    organization_id: str,
    gap_analysis_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> MultiRegulationDashboard:
    """マルチ規制ダッシュボードを取得."""
    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    # ISO チェックも実行
    iso_result = run_iso_check(gap)

    return build_multi_regulation_dashboard(organization_id, gap, iso_result)


# ── Export ────────────────────────────────────────────────────────

@app.get("/api/export/assessment/{assessment_id}")
def export_assessment_api(
    assessment_id: str,
    _user: TokenPayload = Depends(get_current_user),
    fmt: str = "json",
) -> dict:
    """Assessment結果をエクスポート."""
    assessment = get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    export_fmt = ExportFormat.CSV if fmt == "csv" else ExportFormat.JSON
    content = export_assessment(assessment, export_fmt)
    return {"format": fmt, "content": content}


@app.get("/api/export/gap-analysis/{gap_id}")
def export_gap_analysis_api(
    gap_id: str,
    _user: TokenPayload = Depends(get_current_user),
    fmt: str = "json",
) -> dict:
    """ギャップ分析結果をエクスポート."""
    gap = get_gap_analysis(gap_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    export_fmt = ExportFormat.CSV if fmt == "csv" else ExportFormat.JSON
    content = export_gap_analysis(gap, export_fmt)
    return {"format": fmt, "content": content}


@app.post("/api/export/iso-certification-package", response_model=ExportPackage)
def export_iso_package(
    assessment_id: str,
    gap_analysis_id: str,
    _user: TokenPayload = Depends(get_current_user),
    organization_name: str = "",
) -> ExportPackage:
    """ISO 42001認証申請用パッケージを生成."""
    assessment = get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    iso_result = run_iso_check(gap)

    return generate_iso_certification_package(assessment, gap, iso_result, organization_name)


@app.post("/api/export/meti-report-package", response_model=ExportPackage)
def export_meti_package(
    assessment_id: str,
    gap_analysis_id: str,
    _user: TokenPayload = Depends(get_current_user),
    organization_name: str = "",
) -> ExportPackage:
    """METI報告用パッケージを生成."""
    assessment = get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    return generate_meti_report_package(assessment, gap, organization_name)


# ── Evidence ──────────────────────────────────────────────────────

@app.post("/api/evidence", response_model=EvidenceRecord)
def submit_evidence(
    evidence: EvidenceUpload,
    _user: TokenPayload = Depends(get_current_user),
) -> EvidenceRecord:
    """エビデンスをアップロード."""
    record = upload_evidence(evidence)

    ledger = get_audit_ledger()
    ledger.append(
        action="evidence.upload",
        resource_type="evidence",
        resource_id=record.id,
        details={
            "requirement_id": evidence.requirement_id,
            "filename": evidence.filename,
        },
    )

    return record


@app.get("/api/evidence/{organization_id}", response_model=list[EvidenceRecord])
def get_evidence(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
    requirement_id: str | None = None,
) -> list[EvidenceRecord]:
    """エビデンス一覧を取得."""
    return list_evidence(organization_id, requirement_id)


@app.get("/api/evidence-summary/{organization_id}", response_model=EvidenceSummary)
def get_evidence_summary_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> EvidenceSummary:
    """エビデンス充足率サマリー."""
    return get_evidence_summary(organization_id)


# ── Report ────────────────────────────────────────────────────────

@app.post("/api/report", response_model=ReportResponse)
async def generate_report_api(
    req: ReportRequest,
    _user: TokenPayload = Depends(get_current_user),
) -> ReportResponse:
    """レポートを生成."""
    assessment = get_assessment(req.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    gap = get_gap_analysis(req.gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    evidence_summary = None
    if req.include_evidence:
        evidence_summary = get_evidence_summary(req.organization_id)

    result = await generate_report(assessment, gap, evidence_summary)

    ledger = get_audit_ledger()
    ledger.append(
        action="report.generate",
        resource_type="report",
        resource_id=result.id,
        details={"filename": result.filename},
    )

    return result


# ── Audit Trail ───────────────────────────────────────────────────

@app.get("/api/audit/events", response_model=list[AuditEventResponse])
def get_audit_events(
    _user: TokenPayload = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0,
) -> list[AuditEventResponse]:
    """監査イベント一覧."""
    ledger = get_audit_ledger()
    events = ledger.get_events(limit=limit, offset=offset)
    return [
        AuditEventResponse(
            event_id=e.event_id,
            sequence=e.sequence,
            timestamp=e.timestamp,
            action=e.action,
            actor=e.actor,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            details=e.details,
            event_hash=e.event_hash,
            previous_hash=e.previous_hash,
        )
        for e in events
    ]


@app.get("/api/audit/verify", response_model=AuditChainStatus)
def verify_audit_chain(
    _user: TokenPayload = Depends(get_current_user),
) -> AuditChainStatus:
    """監査チェーンの整合性を検証."""
    ledger = get_audit_ledger()
    return ledger.get_status()


# ── Team Management ──────────────────────────────────────────────

@app.post("/api/team/members", response_model=OrganizationMember)
def invite_member(
    invite: OrganizationMemberInvite,
    _user: TokenPayload = Depends(get_current_user),
) -> OrganizationMember:
    """組織にメンバーを招待."""
    from app.services.team import add_member
    member = add_member(
        invite=invite,
        user_id=invite.email,  # Simplified: use email as user_id for now
        display_name="",
        invited_by=_user.user_id,
    )

    ledger = get_audit_ledger()
    ledger.append(
        action="team.member_invite",
        actor=_user.user_id,
        resource_type="organization_member",
        resource_id=member.id,
        details={
            "organization_id": invite.organization_id,
            "email": invite.email,
            "role": invite.role.value,
        },
    )

    return member


@app.delete("/api/team/members/{organization_id}/{user_id}")
def remove_team_member(
    organization_id: str,
    user_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """組織からメンバーを削除."""
    from app.services.team import remove_member
    success = remove_member(organization_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")

    ledger = get_audit_ledger()
    ledger.append(
        action="team.member_remove",
        actor=_user.user_id,
        resource_type="organization_member",
        resource_id=user_id,
        details={"organization_id": organization_id},
    )

    return {"status": "removed"}


@app.put("/api/team/members/{organization_id}/{user_id}", response_model=OrganizationMember)
def update_team_member_role(
    organization_id: str,
    user_id: str,
    update: OrganizationMemberUpdate,
    _user: TokenPayload = Depends(get_current_user),
) -> OrganizationMember:
    """メンバーのロールを更新."""
    from app.services.team import update_member_role
    member = update_member_role(organization_id, user_id, update)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@app.get("/api/team/{organization_id}", response_model=TeamSummary)
def get_team(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> TeamSummary:
    """チームサマリーを取得."""
    from app.services.team import get_team_summary
    summary = get_team_summary(organization_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return summary


@app.get("/api/team/members/{organization_id}", response_model=list[OrganizationMember])
def list_team_members(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[OrganizationMember]:
    """組織のメンバー一覧を取得."""
    from app.services.team import list_members
    return list_members(organization_id)


@app.get("/api/user/organizations")
def get_my_organizations(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """自分が所属する組織の一覧を取得."""
    from app.services.team import get_user_organizations
    return get_user_organizations(_user.user_id)


# ── Timeline ────────────────────────────────────────────────────

@app.get("/api/timeline/{organization_id}", response_model=TimelineResponse)
def get_org_timeline(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> TimelineResponse:
    """成熟度推移データを取得."""
    from app.services.timeline import get_timeline
    return get_timeline(organization_id)


@app.post("/api/timeline/snapshot")
def save_timeline_snapshot(
    organization_id: str,
    assessment_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """診断結果のスナップショットを保存."""
    from app.services.timeline import save_snapshot
    assessment = get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    snapshot = save_snapshot(organization_id, assessment)
    return {"snapshot_id": snapshot.id, "status": "saved"}


# ── Review Cycle ────────────────────────────────────────────────

@app.post("/api/review-cycles", response_model=ReviewCycle)
def create_review_cycle_api(
    data: ReviewCycleCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> ReviewCycle:
    """レビューサイクルを作成."""
    from app.services.review_cycle import create_review_cycle
    cycle = create_review_cycle(data)

    ledger = get_audit_ledger()
    ledger.append(
        action="review_cycle.create",
        actor=_user.user_id,
        resource_type="review_cycle",
        resource_id=cycle.id,
        details={
            "organization_id": data.organization_id,
            "cycle_type": data.cycle_type,
        },
    )

    return cycle


@app.get("/api/review-cycles/{organization_id}", response_model=list[ReviewCycle])
def list_review_cycles_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[ReviewCycle]:
    """レビューサイクル一覧を取得."""
    from app.services.review_cycle import list_review_cycles
    return list_review_cycles(organization_id)


@app.post("/api/review-records", response_model=ReviewRecord)
def create_review_record_api(
    data: ReviewRecordCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> ReviewRecord:
    """レビュー実施記録を作成."""
    from app.services.review_cycle import create_review_record
    record = create_review_record(data)

    ledger = get_audit_ledger()
    ledger.append(
        action="review_record.create",
        actor=_user.user_id,
        resource_type="review_record",
        resource_id=record.id,
        details={
            "organization_id": data.organization_id,
            "cycle_id": data.cycle_id,
        },
    )

    return record


@app.get("/api/review-records/{organization_id}", response_model=list[ReviewRecord])
def list_review_records_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
    cycle_id: str = "",
) -> list[ReviewRecord]:
    """レビュー記録一覧を取得."""
    from app.services.review_cycle import list_review_records
    return list_review_records(organization_id, cycle_id)


@app.get("/api/review-upcoming/{organization_id}")
def get_upcoming_reviews_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """次回レビュー予定を取得."""
    from app.services.review_cycle import get_upcoming_reviews
    return get_upcoming_reviews(organization_id)


# ── Benchmark ───────────────────────────────────────────────────

@app.get("/api/benchmark/{industry}", response_model=IndustryBenchmark | None)
def get_benchmark(
    industry: str,
    _user: TokenPayload = Depends(get_current_user),
    size_bucket: str = "",
) -> IndustryBenchmark | None:
    """業界ベンチマークを取得."""
    from app.services.benchmark import get_industry_benchmark
    result = get_industry_benchmark(industry, size_bucket)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Benchmark not available (insufficient data for k-anonymity)",
        )
    return result


@app.get("/api/benchmark/{industry}/my-position", response_model=MyBenchmarkPosition | None)
def get_my_benchmark_position(
    industry: str,
    organization_id: str,
    my_score: float,
    _user: TokenPayload = Depends(get_current_user),
) -> MyBenchmarkPosition | None:
    """自社の業界内ポジションを取得."""
    from app.services.benchmark import get_my_position
    result = get_my_position(organization_id, industry, my_score)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Position not available (insufficient benchmark data)",
        )
    return result


@app.post("/api/benchmark/submit")
def submit_benchmark(
    organization_id: str,
    industry: str,
    size_bucket: str,
    assessment_id: str,
    _user: TokenPayload = Depends(get_current_user),
    opt_in: bool = True,
) -> dict:
    """ベンチマーク用データを登録."""
    from app.services.benchmark import submit_benchmark_data
    assessment = get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    success = submit_benchmark_data(
        organization_id, industry, size_bucket, assessment, opt_in
    )
    return {"status": "submitted" if success else "failed"}


# ── Approval Workflow ───────────────────────────────────────────

@app.post("/api/approvals", response_model=ApprovalRequest)
def create_approval_api(
    data: ApprovalRequestCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> ApprovalRequest:
    """承認リクエストを作成."""
    from app.services.approval_workflow import create_approval_request
    request = create_approval_request(data, requested_by=_user.user_id)

    ledger = get_audit_ledger()
    ledger.append(
        action="approval.create",
        actor=_user.user_id,
        resource_type="approval_request",
        resource_id=request.id,
        details={
            "organization_id": data.organization_id,
            "title": data.title,
            "request_type": data.request_type,
        },
    )

    return request


@app.get("/api/approvals/{organization_id}", response_model=list[ApprovalRequest])
def list_approvals(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
    status: str = "",
) -> list[ApprovalRequest]:
    """承認リクエスト一覧を取得."""
    from app.services.approval_workflow import list_approval_requests
    approval_status = None
    if status:
        try:
            approval_status = ApprovalStatus(status)
        except ValueError:
            pass
    return list_approval_requests(organization_id, approval_status)


@app.put("/api/approvals/{request_id}", response_model=ApprovalRequest)
def process_approval_api(
    request_id: str,
    action: ApprovalAction,
    _user: TokenPayload = Depends(get_current_user),
) -> ApprovalRequest:
    """承認/却下/差し戻しを処理."""
    from app.services.approval_workflow import process_approval
    result = process_approval(request_id, action, actor_id=_user.user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Approval request not found")

    ledger = get_audit_ledger()
    ledger.append(
        action=f"approval.{action.action.value}",
        actor=_user.user_id,
        resource_type="approval_request",
        resource_id=request_id,
        details={"comment": action.comment},
    )

    return result


@app.get("/api/approvals/pending-count/{organization_id}")
def get_pending_approvals_count(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """承認待ちの件数を取得."""
    from app.services.approval_workflow import get_pending_count
    count = get_pending_count(organization_id)
    return {"organization_id": organization_id, "pending_count": count}


# ── Incident Management ──────────────────────────────────────────

@app.post("/api/incidents", response_model=Incident)
def create_incident_api(
    data: IncidentCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> Incident:
    """AIインシデントを記録."""
    from app.services.incident_management import create_incident
    incident = create_incident(data, actor_id=_user.user_id)

    ledger = get_audit_ledger()
    ledger.append(
        action="incident.create",
        actor=_user.user_id,
        resource_type="incident",
        resource_id=incident.id,
        details={
            "organization_id": data.organization_id,
            "title": data.title,
            "severity": data.severity.value,
            "incident_type": data.incident_type.value,
        },
    )

    # Slack通知
    from app.services.integrations import notify_incident
    notify_incident(
        data.organization_id, data.title,
        data.severity.value, data.incident_type.value,
    )

    return incident


@app.get("/api/incidents/{organization_id}", response_model=list[Incident])
def list_incidents_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
    status: str = "",
    severity: str = "",
) -> list[Incident]:
    """インシデント一覧を取得."""
    from app.services.incident_management import list_incidents
    inc_status = None
    inc_severity = None
    if status:
        try:
            inc_status = IncidentStatus(status)
        except ValueError:
            pass
    if severity:
        try:
            inc_severity = IncidentSeverity(severity)
        except ValueError:
            pass
    return list_incidents(organization_id, status=inc_status, severity=inc_severity)


@app.get("/api/incidents/detail/{incident_id}", response_model=Incident)
def get_incident_api(
    incident_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> Incident:
    """インシデントを取得."""
    from app.services.incident_management import get_incident
    incident = get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.put("/api/incidents/{incident_id}", response_model=Incident)
def update_incident_api(
    incident_id: str,
    update: IncidentUpdate,
    _user: TokenPayload = Depends(get_current_user),
) -> Incident:
    """インシデントを更新."""
    from app.services.incident_management import update_incident
    incident = update_incident(incident_id, update)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    ledger = get_audit_ledger()
    ledger.append(
        action="incident.update",
        actor=_user.user_id,
        resource_type="incident",
        resource_id=incident_id,
        details={"status": incident.status.value},
    )

    return incident


@app.get("/api/incidents/stats/{organization_id}", response_model=IncidentStats)
def get_incident_stats_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> IncidentStats:
    """インシデント統計を取得."""
    from app.services.incident_management import get_incident_stats
    return get_incident_stats(organization_id)


@app.post("/api/incidents/rca", response_model=IncidentRCA)
def create_rca_api(
    data: IncidentRCACreate,
    _user: TokenPayload = Depends(get_current_user),
) -> IncidentRCA:
    """根本原因分析を作成."""
    from app.services.incident_management import create_rca
    rca = create_rca(data)

    ledger = get_audit_ledger()
    ledger.append(
        action="incident.rca_create",
        actor=_user.user_id,
        resource_type="incident_rca",
        resource_id=rca.id,
        details={"incident_id": data.incident_id},
    )

    return rca


@app.get("/api/incidents/rca/{incident_id}", response_model=IncidentRCA | None)
def get_rca_api(
    incident_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> IncidentRCA | None:
    """RCAを取得."""
    from app.services.incident_management import get_rca
    return get_rca(incident_id)


@app.get("/api/incidents/regulatory/{organization_id}", response_model=list[Incident])
def get_regulatory_incidents_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[Incident]:
    """規制当局報告が必要なインシデントを取得."""
    from app.services.incident_management import get_regulatory_reportable_incidents
    return get_regulatory_reportable_incidents(organization_id)


# ── Integration (Slack) ─────────────────────────────────────────

@app.post("/api/integrations", response_model=IntegrationConfig)
def create_integration_api(
    data: IntegrationConfigCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> IntegrationConfig:
    """連携設定を作成."""
    from app.services.integrations import create_integration_config
    config = create_integration_config(data)

    ledger = get_audit_ledger()
    ledger.append(
        action="integration.create",
        actor=_user.user_id,
        resource_type="integration_config",
        resource_id=config.id,
        details={
            "organization_id": data.organization_id,
            "integration_type": data.integration_type,
        },
    )

    return config


@app.get("/api/integrations/{organization_id}", response_model=list[IntegrationConfig])
def list_integrations_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[IntegrationConfig]:
    """連携設定一覧を取得."""
    from app.services.integrations import list_integration_configs
    return list_integration_configs(organization_id)


@app.put("/api/integrations/{organization_id}/{integration_type}", response_model=IntegrationConfig)
def update_integration_api(
    organization_id: str,
    integration_type: str,
    update: IntegrationConfigUpdate,
    _user: TokenPayload = Depends(get_current_user),
) -> IntegrationConfig:
    """連携設定を更新."""
    from app.services.integrations import update_integration_config
    config = update_integration_config(organization_id, integration_type, update)
    if config is None:
        raise HTTPException(status_code=404, detail="Integration config not found")
    return config


# ── Monthly Report ──────────────────────────────────────────────

@app.post("/api/monthly-reports/generate", response_model=MonthlyReport)
def generate_monthly_report_api(
    organization_id: str,
    year: int,
    month: int,
    _user: TokenPayload = Depends(get_current_user),
) -> MonthlyReport:
    """月次レポートを生成."""
    from app.services.auto_report import build_monthly_report_data
    report = build_monthly_report_data(organization_id, year, month)

    ledger = get_audit_ledger()
    ledger.append(
        action="monthly_report.generate",
        actor=_user.user_id,
        resource_type="monthly_report",
        resource_id=report.id,
        details={
            "organization_id": organization_id,
            "year": year,
            "month": month,
        },
    )

    # Slack通知
    from app.services.integrations import notify_monthly_report
    notify_monthly_report(organization_id, year, month)

    return report


@app.get("/api/monthly-reports/{organization_id}", response_model=list[MonthlyReport])
def list_monthly_reports_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[MonthlyReport]:
    """月次レポート一覧を取得."""
    from app.services.auto_report import list_monthly_reports
    return list_monthly_reports(organization_id)


@app.get("/api/monthly-reports/{organization_id}/{year}/{month}", response_model=MonthlyReport)
def get_monthly_report_api(
    organization_id: str,
    year: int,
    month: int,
    _user: TokenPayload = Depends(get_current_user),
) -> MonthlyReport:
    """月次レポートを取得."""
    from app.services.auto_report import get_monthly_report
    report = get_monthly_report(organization_id, year, month)
    if report is None:
        raise HTTPException(status_code=404, detail="Monthly report not found")
    return report


# ── Health ────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check() -> dict:
    """ヘルスチェック."""
    return {"status": "ok", "service": "JPGovAI", "version": "0.5.0"}


# ── Pattern Learning (Phase 3) ──────────────────────────────────

@app.post("/api/patterns/record")
def record_patterns_api(
    organization_id: str,
    industry: str,
    size_bucket: str,
    gap_analysis_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """ギャップ分析結果からパターンを記録."""
    from app.services.pattern_learning import record_gap_patterns
    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    count = record_gap_patterns(industry, size_bucket, gap)
    return {"status": "recorded", "patterns_updated": count}


@app.post("/api/patterns/resolve")
def resolve_pattern_api(
    industry: str,
    size_bucket: str,
    requirement_id: str,
    resolution_days: float = 0.0,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Gapの解決を記録."""
    from app.services.pattern_learning import mark_gap_resolved
    success = mark_gap_resolved(industry, size_bucket, requirement_id, resolution_days)
    if not success:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return {"status": "resolved"}


@app.get("/api/patterns/{industry}")
def get_patterns_api(
    industry: str,
    size_bucket: str = "",
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """業界のGapパターン一覧を取得."""
    from app.services.pattern_learning import get_patterns
    patterns = get_patterns(industry, size_bucket)
    return [p.model_dump() for p in patterns]


@app.get("/api/patterns/match/{industry}")
def get_pattern_matches_api(
    industry: str,
    size_bucket: str,
    gap_analysis_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """パターンマッチングを実行."""
    from app.services.pattern_learning import get_pattern_matches
    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    result = get_pattern_matches(industry, size_bucket, gap)
    return result.model_dump()


# ── Regulatory Monitor (Phase 3) ────────────────────────────────

@app.post("/api/regulatory-updates")
def create_regulatory_update_api(
    data: RegulatoryUpdateCreate,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """規制変更を登録."""
    from app.services.regulatory_monitor import register_update
    update = register_update(data)

    ledger = get_audit_ledger()
    ledger.append(
        action="regulatory_update.create",
        actor=_user.user_id,
        resource_type="regulatory_update",
        resource_id=update.id,
        details={
            "regulation_name": data.regulation_name,
            "title": data.title,
            "severity": data.severity,
        },
    )

    return update.model_dump()


@app.get("/api/regulatory-updates")
def list_regulatory_updates_api(
    regulation_name: str = "",
    severity: str = "",
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """規制変更一覧を取得."""
    from app.services.regulatory_monitor import list_updates
    updates = list_updates(regulation_name, severity)
    return [u.model_dump() for u in updates]


@app.get("/api/regulatory-updates/{update_id}")
def get_regulatory_update_api(
    update_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """規制変更を取得."""
    from app.services.regulatory_monitor import get_update
    update = get_update(update_id)
    if update is None:
        raise HTTPException(status_code=404, detail="Regulatory update not found")
    return update.model_dump()


@app.delete("/api/regulatory-updates/{update_id}")
def delete_regulatory_update_api(
    update_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """規制変更を削除."""
    from app.services.regulatory_monitor import delete_update
    success = delete_update(update_id)
    if not success:
        raise HTTPException(status_code=404, detail="Regulatory update not found")
    return {"status": "deleted"}


@app.get("/api/regulatory-impact/{organization_id}")
def get_regulatory_impact_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """全規制変更の影響を一括分析."""
    from app.services.regulatory_monitor import analyze_all_impacts
    report = analyze_all_impacts(organization_id)
    return report.model_dump()


@app.get("/api/regulatory-impact/{organization_id}/{update_id}")
def get_specific_regulatory_impact_api(
    organization_id: str,
    update_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """特定の規制変更の影響を分析."""
    from app.services.regulatory_monitor import analyze_impact
    impact = analyze_impact(update_id, organization_id)
    if impact is None:
        raise HTTPException(status_code=404, detail="Update not found")
    return impact.model_dump()


# ── Action Analytics (Phase 3) ──────────────────────────────────

@app.post("/api/action-effects", response_model=ActionROI)
def record_action_effect_api(
    data: ActionEffectRecord,
    _user: TokenPayload = Depends(get_current_user),
) -> ActionROI:
    """改善アクションの効果を記録."""
    from app.services.action_analytics import record_action_effect
    roi = record_action_effect(data)

    ledger = get_audit_ledger()
    ledger.append(
        action="action_effect.record",
        actor=_user.user_id,
        resource_type="action_effect",
        resource_id=data.task_id,
        details={
            "organization_id": data.organization_id,
            "action_type": data.action_type,
            "score_delta": roi.score_delta,
        },
    )

    return roi


@app.get("/api/action-rankings/{organization_id}", response_model=ActionRanking)
def get_action_rankings_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> ActionRanking:
    """改善アクション効果ランキングを取得."""
    from app.services.action_analytics import get_action_rankings
    return get_action_rankings(organization_id)


@app.get("/api/action-rankings/{organization_id}/industry-comparison")
def get_industry_comparison_api(
    organization_id: str,
    industry: str,
    size_bucket: str = "",
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """他社の匿名化データとの比較."""
    from app.services.action_analytics import get_industry_comparison
    return get_industry_comparison(organization_id, industry, size_bucket)


@app.get("/api/action-stats/{organization_id}")
def get_action_type_stats_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """アクション種別ごとの統計を取得."""
    from app.services.action_analytics import get_action_type_stats
    return get_action_type_stats(organization_id)


# ── Prediction (Phase 3) ────────────────────────────────────────

@app.get("/api/prediction/{organization_id}", response_model=ScorePrediction)
def get_prediction_api(
    organization_id: str,
    target_date: str = "",
    target_score: float = 2.4,
    _user: TokenPayload = Depends(get_current_user),
) -> ScorePrediction:
    """スコア予測を取得."""
    from app.services.prediction import predict_score
    return predict_score(organization_id, target_date, target_score)


# ── Phase 4: METI Interpretation Guide ───────────────────

@app.get("/api/knowledge/meti-interpretation/{req_id}")
def get_meti_interpretation_api(
    req_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict | None:
    """METI要件の解釈ガイドを取得."""
    from app.guidelines.meti_interpretation import get_interpretation
    interp = get_interpretation(req_id)
    if interp is None:
        raise HTTPException(status_code=404, detail="Interpretation not found")
    return {
        "req_id": interp.req_id,
        "official_text": interp.official_text,
        "interpretation": interp.interpretation,
        "common_misunderstanding": interp.common_misunderstanding,
        "auditor_focus": interp.auditor_focus,
        "best_practice": interp.best_practice,
        "pitfall": interp.pitfall,
        "related_pubcomment": interp.related_pubcomment,
        "iso42001_cross_ref": interp.iso42001_cross_ref,
    }


@app.get("/api/knowledge/meti-interpretations")
def list_meti_interpretations_api(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """全METI解釈ガイドを取得."""
    from app.guidelines.meti_interpretation import all_interpretations
    return [
        {"req_id": i.req_id, "official_text": i.official_text,
         "interpretation": i.interpretation}
        for i in all_interpretations()
    ]


# ── Phase 4: ISO 42001 Certification Guide ───────────────

@app.get("/api/knowledge/certification-guide")
def get_certification_guide_api(
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """ISO 42001認証取得ガイドを取得."""
    from app.knowledge.iso42001_certification_guide import (
        get_all_required_documents,
        get_certification_bodies,
        get_certification_phases,
        get_certification_timelines,
        get_common_nonconformities,
        get_maintenance_audits,
    )
    return {
        "phases": [
            {"phase": p.phase, "name": p.name, "duration": p.duration,
             "tasks": p.tasks, "required_documents": p.required_documents,
             "jpgovai_value": p.jpgovai_value}
            for p in get_certification_phases()
        ],
        "common_nonconformities": [
            {"rank": nc.rank, "title": nc.title, "clause": nc.clause,
             "description": nc.description, "prevention": nc.prevention}
            for nc in get_common_nonconformities()
        ],
        "certification_bodies": [
            {"name": cb.name, "code": cb.code, "focus_areas": cb.focus_areas,
             "typical_cost_range": cb.typical_cost_range}
            for cb in get_certification_bodies()
        ],
        "timelines": [
            {"size": t.size, "size_description": t.size_description,
             "total_months_min": t.total_months_min,
             "total_months_max": t.total_months_max, "notes": t.notes}
            for t in get_certification_timelines()
        ],
        "maintenance_audits": [
            {"audit_type": m.audit_type, "frequency": m.frequency,
             "scope": m.scope, "cost_factor": m.cost_factor}
            for m in get_maintenance_audits()
        ],
        "all_required_documents": get_all_required_documents(),
    }


# ── Phase 4: Finance Deep Guide ──────────────────────────

@app.get("/api/knowledge/finance/risks")
def get_finance_risks_api(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """金融業AIリスク一覧を取得."""
    from app.guidelines.finance_deep_guide import get_financial_risks
    return [
        {"risk_id": r.risk_id, "category": r.category, "title": r.title,
         "description": r.description, "specific_actions": r.specific_actions,
         "meti_mapping": r.meti_mapping}
        for r in get_financial_risks()
    ]


@app.get("/api/knowledge/finance/use-cases")
def get_finance_use_cases_api(
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """金融業AIユースケース一覧を取得."""
    from app.guidelines.finance_deep_guide import get_financial_use_cases
    return [
        {"use_case_id": u.use_case_id, "name": u.name,
         "risk_level": u.risk_level, "key_risks": u.key_risks,
         "required_controls": u.required_controls}
        for u in get_financial_use_cases()
    ]


@app.get("/api/knowledge/finance/deep-guide/{req_id}")
def get_finance_deep_guide_api(
    req_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """METI要件IDに対する金融業ディープガイドを取得."""
    from app.guidelines.finance_deep_guide import get_requirement_deep_guide
    guide = get_requirement_deep_guide(req_id)
    if guide is None:
        raise HTTPException(status_code=404, detail="Guide not found for this requirement")
    return guide


# ── Phase 4: Audit Package ───────────────────────────────

@app.post("/api/audit-package/iso42001-stage1")
def generate_iso_stage1_package_api(
    organization_id: str,
    gap_analysis_id: str,
    organization_name: str = "",
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """ISO 42001 Stage 1 審査用文書パッケージを生成."""
    from app.services.audit_package import generate_iso42001_stage1_package
    package = generate_iso42001_stage1_package(
        organization_id, gap_analysis_id, organization_name,
    )

    ledger = get_audit_ledger()
    ledger.append(
        action="audit_package.generate",
        actor=_user.user_id,
        resource_type="audit_package",
        resource_id=package.id,
        details={
            "audit_type": "iso42001_stage1",
            "document_count": len(package.documents),
        },
    )

    return package.to_dict()


@app.get("/api/audit-package/internal-audit-checklist")
def get_internal_audit_checklist_api(
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """内部監査チェックリストを生成."""
    from app.services.audit_package import generate_internal_audit_checklist
    return generate_internal_audit_checklist()


@app.get("/api/audit-package/management-review-template")
def get_management_review_template_api(
    organization_name: str = "",
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """マネジメントレビュー議事録テンプレートを生成."""
    from app.services.audit_package import generate_management_review_template
    return generate_management_review_template(organization_name)


@app.get("/api/audit-package/corrective-action-template")
def get_corrective_action_template_api(
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """是正措置記録テンプレートを生成."""
    from app.services.audit_package import generate_corrective_action_template
    return generate_corrective_action_template()


# ── Phase 5: Public API (API Key Management) ─────────────

@app.post("/api/v1/api-keys")
def create_api_key_api(
    organization_id: str,
    name: str = "",
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """API Keyを発行."""
    from app.api.public_api import get_api_key_manager
    mgr = get_api_key_manager()
    return mgr.create_key(organization_id, name)


@app.get("/api/v1/api-keys/{organization_id}")
def list_api_keys_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """API Key一覧を取得."""
    from app.api.public_api import get_api_key_manager
    return get_api_key_manager().list_keys(organization_id)


@app.delete("/api/v1/api-keys/{key_id}")
def revoke_api_key_api(
    key_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """API Keyを無効化."""
    from app.api.public_api import get_api_key_manager
    success = get_api_key_manager().revoke_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key not found")
    return {"status": "revoked"}


# ── Phase 5: Webhooks ────────────────────────────────────

@app.post("/api/v1/webhooks")
def register_webhook_api(
    organization_id: str,
    url: str,
    events: str = "*",
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Webhookを登録."""
    from app.api.public_api import get_webhook_manager
    event_list = [e.strip() for e in events.split(",")]
    config = get_webhook_manager().register(organization_id, url, event_list)
    return {
        "id": config.id,
        "url": config.url,
        "events": config.events,
        "secret": config.secret,
    }


@app.get("/api/v1/webhooks/{organization_id}")
def list_webhooks_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """Webhook一覧を取得."""
    from app.api.public_api import get_webhook_manager
    return get_webhook_manager().list_webhooks(organization_id)


@app.delete("/api/v1/webhooks/{webhook_id}")
def unregister_webhook_api(
    webhook_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Webhook登録解除."""
    from app.api.public_api import get_webhook_manager
    success = get_webhook_manager().unregister(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "unregistered"}


# ── Phase 5: Citadel AI Integration ─────────────────────

@app.get("/api/citadel/mapping")
def get_citadel_mapping_api(
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Citadel AI -> JPGovAI要件マッピングを取得."""
    from app.services.citadel_integration import CitadelIntegrationService
    service = CitadelIntegrationService()
    return service.get_requirement_mapping()


# ── AI System Registry ────────────────────────────────────────────

@app.post("/api/ai-registry/systems")
def register_ai_system_api(
    data: dict,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """AIシステムを台帳に登録."""
    from app.services.ai_registry import AISystemCreate, register_ai_system
    system = register_ai_system(AISystemCreate(**data))

    ledger = get_audit_ledger()
    ledger.append(
        action="ai_registry.register",
        actor=_user.user_id,
        resource_type="ai_system",
        resource_id=system.id,
        details={"name": system.name, "risk_level": system.risk_level.value},
    )

    return system.model_dump()


@app.get("/api/ai-registry/systems/{organization_id}")
def list_ai_systems_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
    status: str = "",
    risk_level: str = "",
    department: str = "",
) -> list[dict]:
    """AIシステム一覧を取得."""
    from app.services.ai_registry import (
        AISystemRiskLevel,
        AISystemStatus,
        list_ai_systems,
    )
    s = None
    r = None
    if status:
        try:
            s = AISystemStatus(status)
        except ValueError:
            pass
    if risk_level:
        try:
            r = AISystemRiskLevel(risk_level)
        except ValueError:
            pass
    systems = list_ai_systems(organization_id, status=s, risk_level=r, department=department)
    return [sys.model_dump() for sys in systems]


@app.get("/api/ai-registry/system/{system_id}")
def get_ai_system_api(
    system_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """AIシステムを取得."""
    from app.services.ai_registry import get_ai_system
    system = get_ai_system(system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="AI System not found")
    return system.model_dump()


@app.put("/api/ai-registry/system/{system_id}")
def update_ai_system_api(
    system_id: str,
    data: dict,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """AIシステムを更新."""
    from app.services.ai_registry import AISystemUpdate, update_ai_system
    system = update_ai_system(system_id, AISystemUpdate(**data))
    if system is None:
        raise HTTPException(status_code=404, detail="AI System not found")
    return system.model_dump()


@app.delete("/api/ai-registry/system/{system_id}")
def delete_ai_system_api(
    system_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """AIシステムを削除."""
    from app.services.ai_registry import delete_ai_system
    success = delete_ai_system(system_id)
    if not success:
        raise HTTPException(status_code=404, detail="AI System not found")
    return {"status": "deleted"}


@app.get("/api/ai-registry/dashboard/{organization_id}")
def get_ai_registry_dashboard_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """AIシステム台帳ダッシュボードを取得."""
    from app.services.ai_registry import get_registry_dashboard
    return get_registry_dashboard(organization_id).model_dump()


@app.get("/api/ai-registry/shadow-ai/{organization_id}")
def detect_shadow_ai_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """Shadow AI（IT未承認AIシステム）を検出."""
    from app.services.ai_registry import detect_shadow_ai
    return [s.model_dump() for s in detect_shadow_ai(organization_id)]


@app.get("/api/ai-registry/dependencies/{system_id}")
def get_ai_dependencies_api(
    system_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """AIシステムの依存関係マップを取得."""
    from app.services.ai_registry import get_dependency_map
    dep_map = get_dependency_map(system_id)
    if dep_map is None:
        raise HTTPException(status_code=404, detail="AI System not found")
    return dep_map.model_dump()


# ── Evidence Collector ──────────────────────────────────────────

@app.post("/api/evidence-collector/configs")
def register_collector_config_api(
    organization_id: str,
    collector_type: str,
    config: dict,
    schedule: str = "weekly",
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """コレクター設定を登録."""
    from app.services.evidence_collector import (
        CollectorType,
        ScheduleFrequency,
        register_collector_config,
    )
    try:
        ct = CollectorType(collector_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid collector type: {collector_type}")
    try:
        sf = ScheduleFrequency(schedule)
    except ValueError:
        sf = ScheduleFrequency.WEEKLY
    cc = register_collector_config(organization_id, ct, config, sf)
    return cc.model_dump()


@app.get("/api/evidence-collector/configs/{organization_id}")
def list_collector_configs_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """コレクター設定一覧を取得."""
    from app.services.evidence_collector import list_collector_configs
    return [c.model_dump() for c in list_collector_configs(organization_id)]


@app.post("/api/evidence-collector/run/{config_id}")
def run_collection_api(
    config_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """エビデンス収集を実行."""
    from app.services.evidence_collector import run_collection
    result = run_collection(config_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Collector config not found")
    return result.model_dump()


@app.post("/api/evidence-collector/run-all/{organization_id}")
def run_all_collections_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """全コレクターで収集を実行."""
    from app.services.evidence_collector import run_all_collections
    results = run_all_collections(organization_id)
    return [r.model_dump() for r in results]


@app.get("/api/evidence-collector/dashboard/{organization_id}")
def get_collection_dashboard_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """収集率ダッシュボードを取得."""
    from app.services.evidence_collector import get_collection_dashboard
    return get_collection_dashboard(organization_id).model_dump()


# ── Integration Hub ─────────────────────────────────────────────

@app.get("/api/integration-hub/providers")
def list_integration_providers_api(
    _user: TokenPayload = Depends(get_current_user),
    category: str = "",
) -> list[dict]:
    """利用可能なプロバイダー一覧を取得."""
    from app.services.integration_hub import ProviderCategory, list_providers
    cat = None
    if category:
        try:
            cat = ProviderCategory(category)
        except ValueError:
            pass
    return [p.model_dump() for p in list_providers(cat)]


@app.post("/api/integration-hub/connections")
def create_integration_connection_api(
    data: dict,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """連携接続を作成."""
    from app.services.integration_hub import IntegrationConnectionCreate, create_connection
    conn = create_connection(IntegrationConnectionCreate(**data))
    return conn.model_dump()


@app.get("/api/integration-hub/connections/{organization_id}")
def list_integration_connections_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """連携接続一覧を取得."""
    from app.services.integration_hub import list_connections
    return [c.model_dump() for c in list_connections(organization_id)]


@app.put("/api/integration-hub/connections/{connection_id}")
def update_integration_connection_api(
    connection_id: str,
    data: dict,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """連携接続を更新."""
    from app.services.integration_hub import IntegrationConnectionUpdate, update_connection
    conn = update_connection(connection_id, IntegrationConnectionUpdate(**data))
    if conn is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn.model_dump()


@app.delete("/api/integration-hub/connections/{connection_id}")
def delete_integration_connection_api(
    connection_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """連携接続を削除."""
    from app.services.integration_hub import delete_connection
    success = delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"status": "deleted"}


@app.post("/api/integration-hub/route-event")
def route_event_api(
    organization_id: str,
    event_type: str,
    payload: dict,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """イベントを連携先にルーティング."""
    from app.services.integration_hub import route_event
    return route_event(organization_id, event_type, payload).model_dump()


@app.get("/api/integration-hub/dashboard/{organization_id}")
def get_integration_hub_dashboard_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """Integration Hubダッシュボードを取得."""
    from app.services.integration_hub import get_hub_dashboard
    return get_hub_dashboard(organization_id).model_dump()


# ── AI Advisor (Chatbot) ───────────────────────────────────────

@app.post("/api/ai-advisor/chat")
def ai_advisor_chat_api(
    data: dict,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """AIアドバイザーにメッセージを送信."""
    from app.services.ai_advisor import ChatRequest, chat
    response = chat(ChatRequest(**data))
    return response.model_dump()


@app.get("/api/ai-advisor/sessions/{organization_id}")
def list_chat_sessions_api(
    organization_id: str,
    _user: TokenPayload = Depends(get_current_user),
    user_id: str = "",
) -> list[dict]:
    """チャットセッション一覧を取得."""
    from app.services.ai_advisor import list_sessions
    return [s.model_dump() for s in list_sessions(organization_id, user_id)]


@app.get("/api/ai-advisor/session/{session_id}")
def get_chat_session_api(
    session_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """チャットセッションを取得."""
    from app.services.ai_advisor import get_session
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session.model_dump()


@app.delete("/api/ai-advisor/session/{session_id}")
def delete_chat_session_api(
    session_id: str,
    _user: TokenPayload = Depends(get_current_user),
) -> dict:
    """チャットセッションを削除."""
    from app.services.ai_advisor import delete_session
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"status": "deleted"}
