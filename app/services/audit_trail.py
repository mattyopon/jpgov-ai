# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""監査証跡サービス（ハッシュチェーン）.

全操作の改竄防止ログを提供する。
agent-complyのEventLedger実装パターンを参考に、
SHA-256ハッシュチェーンによる改竄防止機構を実装。

参考: /home/user/repos/agent-comply/src/agent_comply/ledger.py
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.db.database import AuditEventRow, get_db
from app.models import AuditChainStatus


# ── Hash helpers ──────────────────────────────────────────────────

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _merkle_parent(left: str, right: str) -> str:
    return _sha256(left + right)


# ── Ledger Event ──────────────────────────────────────────────────

class AuditEvent(BaseModel):
    """監査イベント."""

    event_id: str = Field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:12]}")
    sequence: int = 0
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    action: str = ""
    actor: str = "system"
    resource_type: str = ""
    resource_id: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    payload_hash: str = ""
    previous_hash: str = ""
    event_hash: str = ""

    def compute_payload_hash(self) -> str:
        """ペイロードのハッシュを計算."""
        payload = {
            "action": self.action,
            "actor": self.actor,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
        }
        return _sha256(json.dumps(payload, sort_keys=True, default=str))

    def compute_hash(self) -> str:
        """イベント全体のハッシュを計算."""
        blob = json.dumps(
            {
                "event_id": self.event_id,
                "sequence": self.sequence,
                "timestamp": self.timestamp,
                "payload_hash": self.payload_hash,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha256(blob).hexdigest()


# ── Merkle Tree ───────────────────────────────────────────────────

class MerkleTree:
    """Incrementally-maintained Merkle tree over event hashes."""

    def __init__(self) -> None:
        self._leaves: list[str] = []
        self._tree: list[str] = [""]

    def add_leaf(self, leaf_hash: str) -> None:
        self._leaves.append(leaf_hash)
        self._rebuild()

    @property
    def root(self) -> str:
        if not self._leaves:
            return _sha256("")
        return self._tree[1]

    @property
    def leaf_count(self) -> int:
        return len(self._leaves)

    @property
    def _padded_size(self) -> int:
        if not self._leaves:
            return 1
        return 1 << math.ceil(math.log2(max(len(self._leaves), 1)))

    def _rebuild(self) -> None:
        n = self._padded_size
        empty = _sha256("")
        size = 2 * n + 1
        tree = [""] * size
        for i in range(n):
            tree[n + i] = self._leaves[i] if i < len(self._leaves) else empty
        for i in range(n - 1, 0, -1):
            tree[i] = _merkle_parent(tree[2 * i], tree[2 * i + 1])
        self._tree = tree


# ── Audit Ledger ──────────────────────────────────────────────────

GENESIS_HASH = _sha256("JPGOV-AI-GENESIS")


class AuditLedger:
    """改竄防止ハッシュチェーン付き監査証跡."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._merkle = MerkleTree()
        self._loaded_from_db = False

    def _load_from_db(self) -> None:
        """DBからイベントを読み込み."""
        if self._loaded_from_db:
            return
        db = get_db()
        with db.get_session() as session:
            rows = (
                session.query(AuditEventRow)
                .order_by(AuditEventRow.sequence)
                .all()
            )
            for row in rows:
                ev = AuditEvent(
                    event_id=row.id,
                    sequence=row.sequence,
                    timestamp=row.timestamp,
                    payload_hash=row.payload_hash,
                    previous_hash=row.previous_hash,
                    event_hash=row.event_hash,
                    **json.loads(row.payload_json),
                )
                self._events.append(ev)
                self._merkle.add_leaf(ev.event_hash)
        self._loaded_from_db = True

    def append(
        self,
        action: str,
        actor: str = "system",
        resource_type: str = "",
        resource_id: str = "",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """監査イベントを追記.

        Args:
            action: 操作種別
            actor: 操作者
            resource_type: リソース種別
            resource_id: リソースID
            details: 追加情報

        Returns:
            AuditEvent: 作成されたイベント
        """
        self._load_from_db()

        previous_hash = (
            self._events[-1].event_hash if self._events else GENESIS_HASH
        )

        ev = AuditEvent(
            sequence=len(self._events),
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            previous_hash=previous_hash,
        )
        ev.payload_hash = ev.compute_payload_hash()
        ev.event_hash = ev.compute_hash()

        self._events.append(ev)
        self._merkle.add_leaf(ev.event_hash)

        # DB保存
        db = get_db()
        with db.get_session() as session:
            row = AuditEventRow(
                id=ev.event_id,
                sequence=ev.sequence,
                timestamp=ev.timestamp,
                payload_json=json.dumps(
                    {
                        "action": ev.action,
                        "actor": ev.actor,
                        "resource_type": ev.resource_type,
                        "resource_id": ev.resource_id,
                        "details": ev.details,
                    },
                    default=str,
                ),
                payload_hash=ev.payload_hash,
                previous_hash=ev.previous_hash,
                event_hash=ev.event_hash,
            )
            session.add(row)
            session.commit()

        return ev

    def get_events(self, limit: int = 100, offset: int = 0) -> list[AuditEvent]:
        """イベント一覧を取得."""
        self._load_from_db()
        return self._events[offset : offset + limit]

    def verify_chain(self) -> tuple[bool, list[str]]:
        """ハッシュチェーン全体を検証.

        Returns:
            tuple[bool, list[str]]: (検証結果, エラーリスト)
        """
        self._load_from_db()
        errors: list[str] = []

        if not self._events:
            return True, errors

        # Genesis link
        if self._events[0].previous_hash != GENESIS_HASH:
            errors.append("Event 0: genesis hash mismatch")

        for i, ev in enumerate(self._events):
            # イベントハッシュの検証
            expected = ev.compute_hash()
            if ev.event_hash != expected:
                errors.append(
                    f"Event {i} ({ev.event_id}): event_hash mismatch"
                )

            # ペイロードハッシュの検証
            expected_payload = ev.compute_payload_hash()
            if ev.payload_hash != expected_payload:
                errors.append(
                    f"Event {i} ({ev.event_id}): payload_hash mismatch"
                )

            # 後方リンクの検証
            if i > 0 and ev.previous_hash != self._events[i - 1].event_hash:
                errors.append(
                    f"Event {i} ({ev.event_id}): previous_hash chain break"
                )

        return len(errors) == 0, errors

    def get_status(self) -> AuditChainStatus:
        """監査チェーンの状態を取得."""
        self._load_from_db()
        is_valid, errors = self.verify_chain()
        return AuditChainStatus(
            total_events=len(self._events),
            chain_valid=is_valid,
            merkle_root=self._merkle.root,
            errors=errors,
        )


# Singleton
_ledger: AuditLedger | None = None


def get_audit_ledger() -> AuditLedger:
    """監査台帳のシングルトンを取得."""
    global _ledger
    if _ledger is None:
        _ledger = AuditLedger()
    return _ledger


def reset_audit_ledger() -> None:
    """テスト用リセット."""
    global _ledger
    _ledger = None
