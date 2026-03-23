"""FastAPI application for JPGovAI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.db.database import OrganizationRow, get_db
from app.guidelines.meti_v1_1 import ASSESSMENT_QUESTIONS, CATEGORIES
from app.models import (
    AssessmentRequest,
    AssessmentResult,
    AuditChainStatus,
    AuditEventResponse,
    EvidenceRecord,
    EvidenceSummary,
    EvidenceUpload,
    GapAnalysisResult,
    OrganizationCreate,
    OrganizationResponse,
    ReportRequest,
    ReportResponse,
)
from app.services.assessment import get_assessment, run_assessment
from app.services.audit_trail import get_audit_ledger
from app.services.evidence import get_evidence_summary, list_evidence, upload_evidence
from app.services.gap_analysis import get_gap_analysis, run_gap_analysis
from app.services.report_gen import generate_report

app = FastAPI(
    title="JPGovAI",
    description="AI Governance Mark取得支援SaaS - METI AI事業者ガイドライン準拠",
    version="0.1.0",
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
    return {"status": "ok", "service": "JPGovAI", "version": "0.1.0"}
