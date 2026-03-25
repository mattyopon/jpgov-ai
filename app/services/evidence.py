# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""エビデンス管理サービス（強化版）.

各要件に対するエビデンス（方針文書、テスト結果、監査ログ等）の
アップロード・管理と充足率ダッシュボード情報を提供する。

Phase 2 強化:
- ファイルシステムベースの実ストレージ（uploads/{org_id}/{requirement_id}/）
- ファイルメタデータ（名前、サイズ、SHA-256ハッシュ、アップロード日時、アップロード者）
- エビデンスの有効期限設定と期限切れアラート
- エビデンスカバレッジ率の算出
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from app.db.database import EvidenceRow, get_db
from app.guidelines.meti_v1_1 import CATEGORIES, all_requirements
from app.models import EvidenceFile, EvidenceRecord, EvidenceSummary, EvidenceUpload


UPLOAD_DIR = Path("uploads")


def upload_evidence(
    evidence: EvidenceUpload,
    file_content: bytes | None = None,
    uploaded_by: str = "",
    expires_at: str = "",
) -> EvidenceRecord:
    """エビデンスをアップロード.

    Phase 2: ファイルシステムベースの実ストレージ。
    file_content が None の場合はメタデータのみ登録（後方互換性）。

    Args:
        evidence: アップロード情報
        file_content: ファイルバイナリ（None=メタデータのみ）
        uploaded_by: アップロード者のuser_id
        expires_at: 有効期限（ISO 8601、空=無期限）

    Returns:
        EvidenceRecord: 保存されたエビデンスレコード
    """
    # uploads/{org_id}/{requirement_id}/ 配下に保存
    org_dir = UPLOAD_DIR / evidence.organization_id / evidence.requirement_id
    org_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{evidence.filename}"
    file_path = org_dir / unique_name

    file_size = 0
    file_hash = ""

    if file_content is not None:
        file_path.write_bytes(file_content)
        file_size = len(file_content)
        file_hash = hashlib.sha256(file_content).hexdigest()

    record = EvidenceRecord(
        organization_id=evidence.organization_id,
        requirement_id=evidence.requirement_id,
        filename=evidence.filename,
        description=evidence.description,
        file_type=evidence.file_type,
        file_path=str(file_path),
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


def upload_evidence_v2(
    evidence: EvidenceUpload,
    file_content: bytes | None = None,
    uploaded_by: str = "",
    expires_at: str = "",
) -> EvidenceFile:
    """エビデンスをアップロード（強化版）.

    Args:
        evidence: アップロード情報
        file_content: ファイルバイナリ（None=メタデータのみ）
        uploaded_by: アップロード者のuser_id
        expires_at: 有効期限（ISO 8601、空=無期限）

    Returns:
        EvidenceFile: 保存されたエビデンスファイル（メタデータ付き）
    """
    org_dir = UPLOAD_DIR / evidence.organization_id / evidence.requirement_id
    org_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{evidence.filename}"
    file_path = org_dir / unique_name

    file_size = 0
    file_hash = ""

    if file_content is not None:
        file_path.write_bytes(file_content)
        file_size = len(file_content)
        file_hash = hashlib.sha256(file_content).hexdigest()

    ef = EvidenceFile(
        organization_id=evidence.organization_id,
        requirement_id=evidence.requirement_id,
        filename=evidence.filename,
        description=evidence.description,
        file_type=evidence.file_type,
        file_path=str(file_path),
        file_size=file_size,
        file_hash=file_hash,
        uploaded_by=uploaded_by,
        expires_at=expires_at,
    )

    # 既存テーブルにも保存（後方互換）
    db = get_db()
    with db.get_session() as session:
        row = EvidenceRow(
            id=ef.id,
            organization_id=ef.organization_id,
            requirement_id=ef.requirement_id,
            filename=ef.filename,
            description=ef.description,
            file_type=ef.file_type,
            file_path=ef.file_path,
        )
        session.add(row)
        session.commit()

    return ef


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


def get_expiring_evidence(
    organization_id: str,
    within_days: int = 30,
) -> list[EvidenceRecord]:
    """有効期限が近いエビデンスを取得.

    注: 現在のEvidenceRowには expires_at カラムがないため、
    この関数はEvidenceFile（upload_evidence_v2経由）のデータを
    将来のDB拡張で対応予定。現時点では空リストを返す。

    Args:
        organization_id: 組織ID
        within_days: 何日以内に期限切れか

    Returns:
        list[EvidenceRecord]: 期限切れ間近のエビデンスリスト
    """
    # 将来のDB拡張で expires_at カラム追加後に実装
    # 現時点では空リストを返す
    return []


def get_evidence_coverage_rate(organization_id: str) -> float:
    """エビデンスカバレッジ率を算出.

    全要件のうちエビデンスが揃っている割合。

    Args:
        organization_id: 組織ID

    Returns:
        float: カバレッジ率 (0.0-1.0)
    """
    summary = get_evidence_summary(organization_id)
    return summary.coverage_rate
