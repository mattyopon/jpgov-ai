"""Tests for the audit trail (hash chain) service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.services.audit_trail import AuditLedger, GENESIS_HASH, reset_audit_ledger


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    reset_audit_ledger()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()
    reset_audit_ledger()


class TestAuditTrail:
    """Audit trail hash chain tests."""

    def test_empty_chain_is_valid(self):
        """An empty chain should be valid."""
        ledger = AuditLedger()
        is_valid, errors = ledger.verify_chain()
        assert is_valid
        assert len(errors) == 0

    def test_single_event(self):
        """A single event should be valid."""
        ledger = AuditLedger()
        ev = ledger.append(
            action="test.action",
            actor="test_user",
            resource_type="test",
            resource_id="123",
        )
        assert ev.event_hash
        assert ev.previous_hash == GENESIS_HASH
        is_valid, errors = ledger.verify_chain()
        assert is_valid

    def test_chain_of_three(self):
        """A chain of three events should be valid."""
        ledger = AuditLedger()
        ev1 = ledger.append(action="action.1")
        ev2 = ledger.append(action="action.2")
        ev3 = ledger.append(action="action.3")

        assert ev1.previous_hash == GENESIS_HASH
        assert ev2.previous_hash == ev1.event_hash
        assert ev3.previous_hash == ev2.event_hash

        is_valid, errors = ledger.verify_chain()
        assert is_valid

    def test_tampering_detection(self):
        """Tampering with an event should be detected."""
        ledger = AuditLedger()
        ledger.append(action="action.1")
        ledger.append(action="action.2")
        ledger.append(action="action.3")

        # Tamper with the second event's hash
        ledger._events[1].event_hash = "tampered_hash"

        is_valid, errors = ledger.verify_chain()
        assert not is_valid
        assert len(errors) > 0

    def test_payload_tampering_detection(self):
        """Tampering with payload should be detected."""
        ledger = AuditLedger()
        ledger.append(action="action.1", details={"key": "value"})

        # Tamper with the payload
        ledger._events[0].details = {"key": "tampered"}

        is_valid, errors = ledger.verify_chain()
        assert not is_valid

    def test_merkle_root_changes(self):
        """Merkle root should change with each new event."""
        ledger = AuditLedger()
        root0 = ledger._merkle.root

        ledger.append(action="action.1")
        root1 = ledger._merkle.root
        assert root1 != root0

        ledger.append(action="action.2")
        root2 = ledger._merkle.root
        assert root2 != root1

    def test_get_status(self):
        """Status should reflect the chain state."""
        ledger = AuditLedger()
        ledger.append(action="action.1")
        ledger.append(action="action.2")

        status = ledger.get_status()
        assert status.total_events == 2
        assert status.chain_valid is True
        assert status.merkle_root
        assert len(status.errors) == 0

    def test_get_events(self):
        """Should return events in order."""
        ledger = AuditLedger()
        ledger.append(action="action.1")
        ledger.append(action="action.2")
        ledger.append(action="action.3")

        events = ledger.get_events(limit=2)
        assert len(events) == 2
        assert events[0].action == "action.1"
        assert events[1].action == "action.2"

    def test_sequence_numbering(self):
        """Events should be sequentially numbered."""
        ledger = AuditLedger()
        ev1 = ledger.append(action="a")
        ev2 = ledger.append(action="b")
        ev3 = ledger.append(action="c")
        assert ev1.sequence == 0
        assert ev2.sequence == 1
        assert ev3.sequence == 2

    def test_event_has_timestamp(self):
        """Each event should have a timestamp."""
        ledger = AuditLedger()
        ev = ledger.append(action="test")
        assert ev.timestamp
        assert "T" in ev.timestamp  # ISO format
