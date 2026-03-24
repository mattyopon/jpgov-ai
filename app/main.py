# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""FastAPI application for JPGovAI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.db.database import OrganizationRow, get_db
from app.guidelines.ai_promotion_act import ACT_CHAPTERS, all_act_requirements
from app.guidelines.iso42001 import ISO_CLAUSES, all_iso_requirements, get_meti_to_iso_mapping
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, CATEGORIES
from app.models import (
    ActionTask,
    ActionTaskCreate,
    ActionTaskUpdate,
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
    ISOCheckResult,
    MultiRegulationDashboard,
    OrganizationCreate,
    OrganizationResponse,
    PolicyDocument,
    PolicyGenerateRequest,
    ReportRequest,
    ReportResponse,
    RiskAssessmentRequest,
    RiskAssessmentResult,
    TaskBoardSummary,
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
    description="AI Governance Mark取得支援SaaS - METI AI事業者ガイドライン / ISO 42001 / AI推進法 準拠",
    version="0.2.0",
)


# ── Startup ───────────────────────────────────────────────────────

@app.on_event("startup")
def startup() -> None:
    """DB初期化."""
    get_db()


# ── Organizations ─────────────────────────────────────────────────

@app.post("/api/organizations", response_model=OrganizationResponse)
def create_organization(org: OrganizationCreate) -> OrganizationResponse:
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
def get_categories() -> list[dict]:
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
def get_requirements() -> list[dict]:
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
def get_questions() -> list[dict]:
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
def get_iso_clauses() -> list[dict]:
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
def get_iso_requirements() -> list[dict]:
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
def get_cross_mapping() -> dict:
    """METI <-> ISO 42001 クロスマッピング."""
    return get_meti_to_iso_mapping()


# ── AI推進法 Guidelines ──────────────────────────────────────────

@app.get("/api/guidelines/ai-promotion-act/chapters")
def get_act_chapters() -> list[dict]:
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
def get_act_requirements() -> list[dict]:
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
def submit_assessment(req: AssessmentRequest) -> AssessmentResult:
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
def get_assessment_by_id(assessment_id: str) -> AssessmentResult:
    """診断結果を取得."""
    result = get_assessment(assessment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return result


# ── Gap Analysis ──────────────────────────────────────────────────

@app.post("/api/gap-analysis", response_model=GapAnalysisResult)
async def submit_gap_analysis(assessment_id: str) -> GapAnalysisResult:
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
def get_gap_analysis_by_id(gap_id: str) -> GapAnalysisResult:
    """ギャップ分析結果を取得."""
    result = get_gap_analysis(gap_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")
    return result


# ── ISO 42001 Check ──────────────────────────────────────────────

@app.post("/api/iso-check", response_model=ISOCheckResult)
def submit_iso_check(gap_analysis_id: str) -> ISOCheckResult:
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
def get_risk_questions_api() -> list[dict]:
    """リスク分類用の質問一覧."""
    return get_risk_questions()


@app.post("/api/risk-assessment", response_model=RiskAssessmentResult)
def submit_risk_assessment(req: RiskAssessmentRequest) -> RiskAssessmentResult:
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
def get_risk_assessment_by_id(assessment_id: str) -> RiskAssessmentResult:
    """リスクアセスメント結果を取得."""
    result = get_risk_assessment(assessment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    return result


@app.get("/api/risk-assessments/{organization_id}", response_model=list[RiskAssessmentResult])
def get_risk_assessments(organization_id: str) -> list[RiskAssessmentResult]:
    """組織のリスクアセスメント一覧."""
    return list_risk_assessments(organization_id)


# ── Task Management ──────────────────────────────────────────────

@app.post("/api/tasks", response_model=ActionTask)
def create_task_api(task_data: ActionTaskCreate) -> ActionTask:
    """改善タスクを作成."""
    return create_task(task_data)


@app.get("/api/tasks/{task_id}", response_model=ActionTask)
def get_task_api(task_id: str) -> ActionTask:
    """タスクを取得."""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}", response_model=ActionTask)
def update_task_api(task_id: str, update: ActionTaskUpdate) -> ActionTask:
    """タスクを更新."""
    task = update_task(task_id, update)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/tasks/org/{organization_id}", response_model=list[ActionTask])
def list_tasks_api(organization_id: str, status: str | None = None) -> list[ActionTask]:
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
def get_board_api(organization_id: str) -> TaskBoardSummary:
    """カンバンボードサマリーを取得."""
    return get_board_summary(organization_id)


@app.post("/api/tasks/from-gap-analysis", response_model=list[ActionTask])
def create_tasks_from_gap_api(organization_id: str, gap_analysis_id: str) -> list[ActionTask]:
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
def get_policy_types() -> list[dict]:
    """利用可能なポリシータイプ一覧."""
    return get_available_policy_types()


@app.post("/api/policies/generate", response_model=PolicyDocument)
def generate_policy_api(req: PolicyGenerateRequest) -> PolicyDocument:
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
def generate_all_policies_api(organization_id: str, organization_name: str) -> list[PolicyDocument]:
    """全ポリシーをまとめて生成."""
    return generate_all_policies(organization_name, organization_id)


# ── Multi-Regulation Dashboard ───────────────────────────────────

@app.get("/api/dashboard/{organization_id}", response_model=MultiRegulationDashboard)
def get_dashboard(organization_id: str, gap_analysis_id: str) -> MultiRegulationDashboard:
    """マルチ規制ダッシュボードを取得."""
    gap = get_gap_analysis(gap_analysis_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="Gap analysis not found")

    # ISO チェックも実行
    iso_result = run_iso_check(gap)

    return build_multi_regulation_dashboard(organization_id, gap, iso_result)


# ── Export ────────────────────────────────────────────────────────

@app.get("/api/export/assessment/{assessment_id}")
def export_assessment_api(assessment_id: str, fmt: str = "json") -> dict:
    """Assessment結果をエクスポート."""
    assessment = get_assessment(assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    export_fmt = ExportFormat.CSV if fmt == "csv" else ExportFormat.JSON
    content = export_assessment(assessment, export_fmt)
    return {"format": fmt, "content": content}


@app.get("/api/export/gap-analysis/{gap_id}")
def export_gap_analysis_api(gap_id: str, fmt: str = "json") -> dict:
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
def submit_evidence(evidence: EvidenceUpload) -> EvidenceRecord:
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
def get_evidence(organization_id: str, requirement_id: str | None = None) -> list[EvidenceRecord]:
    """エビデンス一覧を取得."""
    return list_evidence(organization_id, requirement_id)


@app.get("/api/evidence-summary/{organization_id}", response_model=EvidenceSummary)
def get_evidence_summary_api(organization_id: str) -> EvidenceSummary:
    """エビデンス充足率サマリー."""
    return get_evidence_summary(organization_id)


# ── Report ────────────────────────────────────────────────────────

@app.post("/api/report", response_model=ReportResponse)
async def generate_report_api(req: ReportRequest) -> ReportResponse:
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
def get_audit_events(limit: int = 100, offset: int = 0) -> list[AuditEventResponse]:
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
def verify_audit_chain() -> AuditChainStatus:
    """監査チェーンの整合性を検証."""
    ledger = get_audit_ledger()
    return ledger.get_status()


# ── Health ────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check() -> dict:
    """ヘルスチェック."""
    return {"status": "ok", "service": "JPGovAI", "version": "0.2.0"}
