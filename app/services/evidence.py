# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""エビデンス管理サービス.

各要件に対するエビデンス（方針文書、テスト結果、監査ログ等）の
アップロード・管理と充足率ダッシュボード情報を提供する。
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.db.database import EvidenceRow, get_db
from app.guidelines.meti_v1_1 import CATEGORIES, all_requirements
from app.models import EvidenceRecord, EvidenceSummary, EvidenceUpload


UPLOAD_DIR = Path("uploads")


def upload_evidence(evidence: EvidenceUpload) -> EvidenceRecord:
    """エビデンスをアップロード（プロトタイプ: ファイル保存はシミュレーション）.

    Args:
        evidence: アップロード情報

    Returns:
        EvidenceRecord: 保存されたエビデンスレコード
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    record = EvidenceRecord(
        organization_id=evidence.organization_id,
        requirement_id=evidence.requirement_id,
        filename=evidence.filename,
        description=evidence.description,
        file_type=evidence.file_type,
        file_path=str(UPLOAD_DIR / f"{uuid.uuid4().hex}_{evidence.filename}"),
    )

    db = get_db()
    with db.get_session() as session:
        row = EvidenceRow(
            id=record.id,
            organization_id=record.organization_id,
            requirement_id=record.requirement_id,
            filename=record.filename,
            description=record.description,
            file_type=record.file_type,
            file_path=record.file_path,
        )
        session.add(row)
        session.commit()

    return record


def list_evidence(
    organization_id: str,
    requirement_id: str | None = None,
) -> list[EvidenceRecord]:
    """エビデンス一覧を取得.

    Args:
        organization_id: 組織ID
        requirement_id: 絞り込む要件ID（省略時は全件）

    Returns:
        list[EvidenceRecord]: エビデンスレコードのリスト
    """
    db = get_db()
    with db.get_session() as session:
        query = session.query(EvidenceRow).filter_by(
            organization_id=organization_id
        )
        if requirement_id:
            query = query.filter_by(requirement_id=requirement_id)
        rows = query.all()
        return [
            EvidenceRecord(
                id=r.id,
                organization_id=r.organization_id,
                requirement_id=r.requirement_id,
                filename=r.filename,
                description=r.description,
                file_type=r.file_type,
                file_path=r.file_path,
                uploaded_at=r.uploaded_at,
            )
            for r in rows
        ]


def get_evidence_summary(organization_id: str) -> EvidenceSummary:
    """エビデンス充足率サマリーを取得.

    Args:
        organization_id: 組織ID

    Returns:
        EvidenceSummary: 充足率サマリー
    """
    all_reqs = all_requirements()
    evidences = list_evidence(organization_id)
    req_with_evidence = set(e.requirement_id for e in evidences)

    by_category: dict[str, dict] = {}
    for cat in CATEGORIES:
        cat_reqs = [r for r in cat.requirements]
        cat_req_ids = {r.req_id for r in cat_reqs}
        covered = cat_req_ids & req_with_evidence
        by_category[cat.category_id] = {
            "title": cat.title,
            "total": len(cat_reqs),
            "covered": len(covered),
            "rate": len(covered) / len(cat_reqs) if cat_reqs else 0.0,
        }

    total = len(all_reqs)
    covered_count = len(req_with_evidence & {r.req_id for r in all_reqs})

    return EvidenceSummary(
        organization_id=organization_id,
        total_requirements=total,
        requirements_with_evidence=covered_count,
        coverage_rate=covered_count / total if total > 0 else 0.0,
        by_category=by_category,
    )
