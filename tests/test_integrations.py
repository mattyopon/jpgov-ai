# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the Slack integration service."""

from __future__ import annotations

from typing import Any

import pytest

from app.db.database import get_db, reset_db
from app.models import (
    IntegrationConfigCreate,
    IntegrationConfigUpdate,
)
from app.services.integrations import (
    _build_slack_payload,
    create_integration_config,
    get_integration_config,
    list_integration_configs,
    notify_approval_created,
    notify_approval_result,
    notify_incident,
    notify_monthly_report,
    notify_new_gap,
    notify_review_reminder,
    notify_score_drop,
    reset_webhook_sender,
    send_notification,
    set_webhook_sender,
    update_integration_config,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    """Use a temporary database for each test."""
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()
    reset_webhook_sender()


def _create_config(
    org_id: str = "org-001",
    webhook_url: str = "https://hooks.slack.com/test",
) -> IntegrationConfigCreate:
    return IntegrationConfigCreate(
        organization_id=org_id,
        integration_type="slack",
        webhook_url=webhook_url,
        enabled=True,
        language="ja",
    )


class MockSender:
    """テスト用のWebhook送信モック."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.return_value = True

    def __call__(self, url: str, payload: dict[str, Any]) -> bool:
        self.calls.append((url, payload))
        return self.return_value


class TestIntegrationConfig:
    """Integration config CRUD tests."""

    def test_create_config(self):
        """Should create an integration config."""
        config = create_integration_config(_create_config())
        assert config.organization_id == "org-001"
        assert config.integration_type == "slack"
        assert config.webhook_url == "https://hooks.slack.com/test"
        assert config.enabled is True

    def test_get_config(self):
        """Should retrieve an integration config."""
        create_integration_config(_create_config())
        config = get_integration_config("org-001", "slack")
        assert config is not None
        assert config.webhook_url == "https://hooks.slack.com/test"

    def test_get_config_not_found(self):
        """Should return None for non-existent config."""
        config = get_integration_config("org-999", "slack")
        assert config is None

    def test_update_config(self):
        """Should update an integration config."""
        create_integration_config(_create_config())
        updated = update_integration_config(
            "org-001",
            "slack",
            IntegrationConfigUpdate(
                webhook_url="https://hooks.slack.com/new",
                enabled=False,
                notify_incident=False,
            ),
        )
        assert updated is not None
        assert updated.webhook_url == "https://hooks.slack.com/new"
        assert updated.enabled is False
        assert updated.notify_incident is False

    def test_update_config_not_found(self):
        """Should return None for non-existent config."""
        result = update_integration_config(
            "org-999", "slack", IntegrationConfigUpdate(enabled=False)
        )
        assert result is None

    def test_list_configs(self):
        """Should list all configs for an organization."""
        create_integration_config(_create_config())
        configs = list_integration_configs("org-001")
        assert len(configs) == 1
        assert configs[0].integration_type == "slack"


class TestSlackNotification:
    """Slack notification tests."""

    def test_build_payload_ja(self):
        """Should build Japanese Slack payload."""
        payload = _build_slack_payload(
            "review_reminder",
            "ja",
            {"due_date": "2026-04-01", "cycle_type": "quarterly"},
        )
        assert "[JPGovAI]" in payload["text"]
        assert "リマインダー" in payload["text"]
        assert payload["blocks"][0]["text"]["text"].find("2026-04-01") != -1

    def test_build_payload_en(self):
        """Should build English Slack payload."""
        payload = _build_slack_payload(
            "review_reminder",
            "en",
            {"due_date": "2026-04-01", "cycle_type": "quarterly"},
        )
        assert "Review Reminder" in payload["text"]

    def test_build_payload_unknown_event(self):
        """Should handle unknown event type."""
        payload = _build_slack_payload("unknown_event", "ja", {"key": "val"})
        assert "[JPGovAI]" in payload["text"]

    def test_send_notification_with_mock(self):
        """Should send notification via mock sender."""
        mock = MockSender()
        set_webhook_sender(mock)

        create_integration_config(_create_config())
        result = send_notification("org-001", "review_reminder", {"due_date": "2026-04-01", "cycle_type": "quarterly"})

        assert result is True
        assert len(mock.calls) == 1
        assert mock.calls[0][0] == "https://hooks.slack.com/test"

    def test_send_notification_disabled(self):
        """Should not send when integration is disabled."""
        mock = MockSender()
        set_webhook_sender(mock)

        create_integration_config(_create_config())
        update_integration_config("org-001", "slack", IntegrationConfigUpdate(enabled=False))

        result = send_notification("org-001", "review_reminder", {"due_date": "2026-04-01", "cycle_type": "quarterly"})
        assert result is False
        assert len(mock.calls) == 0

    def test_send_notification_no_config(self):
        """Should return False when no config exists."""
        result = send_notification("org-999", "review_reminder", {})
        assert result is False

    def test_send_notification_event_disabled(self):
        """Should not send when specific event notification is disabled."""
        mock = MockSender()
        set_webhook_sender(mock)

        create_integration_config(_create_config())
        update_integration_config(
            "org-001", "slack", IntegrationConfigUpdate(notify_incident=False)
        )

        result = send_notification("org-001", "incident_reported", {"title": "test", "severity": "high", "incident_type": "bias"})
        assert result is False

    def test_notify_review_reminder(self):
        """Should send review reminder."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_review_reminder("org-001", "2026-04-01", "quarterly", 7)
        assert result is True
        assert len(mock.calls) == 1

    def test_notify_approval_created(self):
        """Should send approval created notification."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_approval_created("org-001", "ポリシー改定", "user-001")
        assert result is True

    def test_notify_approval_result_approved(self):
        """Should send approval approved notification."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_approval_result("org-001", "ポリシー改定", True, "admin-001")
        assert result is True

    def test_notify_approval_result_rejected(self):
        """Should send approval rejected notification."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_approval_result("org-001", "ポリシー改定", False, comment="要修正")
        assert result is True

    def test_notify_score_drop(self):
        """Should send score drop notification."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_score_drop("org-001", 1.5, 2.0)
        assert result is True

    def test_notify_new_gap(self):
        """Should send new gap notification."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_new_gap("org-001", "R001", "安全性方針", "high")
        assert result is True

    def test_notify_incident(self):
        """Should send incident notification."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_incident("org-001", "バイアス検出", "high", "bias")
        assert result is True

    def test_notify_monthly_report(self):
        """Should send monthly report notification."""
        mock = MockSender()
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = notify_monthly_report("org-001", 2026, 3)
        assert result is True

    def test_sender_failure(self):
        """Should return False when sender fails."""
        mock = MockSender()
        mock.return_value = False
        set_webhook_sender(mock)
        create_integration_config(_create_config())

        result = send_notification("org-001", "review_reminder", {"due_date": "2026-04-01", "cycle_type": "quarterly"})
        assert result is False
