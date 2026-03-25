# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the Integration Hub service."""

from __future__ import annotations

import pytest

from app.services.integration_hub import (
    AuthType,
    IntegrationConnectionCreate,
    IntegrationConnectionUpdate,
    IntegrationStatus,
    ProviderCategory,
    create_connection,
    delete_connection,
    get_connection,
    get_hub_dashboard,
    get_provider,
    list_connections,
    list_providers,
    reset_hub,
    route_event,
    update_connection,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_hub()
    yield
    reset_hub()


ORG_ID = "org-test-001"


# ── Provider Tests ──────────────────────────────────────────────

class TestProviders:
    def test_list_all_providers(self):
        providers = list_providers()
        assert len(providers) >= 15
        names = {p.name for p in providers}
        assert "Slack" in names
        assert "Microsoft Teams" in names
        assert "GitHub" in names
        assert "Jira" in names
        assert "Amazon Web Services" in names

    def test_list_by_category(self):
        comm = list_providers(ProviderCategory.COMMUNICATION)
        assert len(comm) == 3  # slack, teams, email
        for p in comm:
            assert p.category == ProviderCategory.COMMUNICATION

        cloud = list_providers(ProviderCategory.CLOUD)
        assert len(cloud) == 3  # aws, azure, gcp

    def test_get_provider(self):
        slack = get_provider("slack")
        assert slack is not None
        assert slack.name == "Slack"
        assert ProviderCategory.COMMUNICATION == slack.category
        assert len(slack.config_fields) > 0

    def test_get_nonexistent_provider(self):
        assert get_provider("nonexistent") is None


# ── Connection CRUD Tests ───────────────────────────────────────

class TestConnections:
    def test_create_connection(self):
        conn = create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
            credentials={"webhook_url": "https://hooks.slack.com/xxx"},
            subscribed_events=["incident.created"],
        ))
        assert conn.id
        assert conn.status == IntegrationStatus.CONNECTED

    def test_create_connection_invalid_auth_type(self):
        conn = create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.BASIC,  # not supported for Slack
        ))
        assert conn.status == IntegrationStatus.ERROR
        assert "not supported" in conn.error_message

    def test_create_connection_unknown_provider(self):
        conn = create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="nonexistent",
        ))
        assert conn.status == IntegrationStatus.ERROR

    def test_get_connection(self):
        conn = create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="github",
            auth_type=AuthType.API_KEY,
        ))
        fetched = get_connection(conn.id)
        assert fetched is not None
        assert fetched.provider_id == "github"

    def test_get_nonexistent_connection(self):
        assert get_connection("nonexistent") is None

    def test_update_connection(self):
        conn = create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
        ))
        updated = update_connection(conn.id, IntegrationConnectionUpdate(
            subscribed_events=["incident.created", "review.reminder"],
        ))
        assert updated is not None
        assert len(updated.subscribed_events) == 2

    def test_update_nonexistent(self):
        assert update_connection("nonexistent", IntegrationConnectionUpdate()) is None

    def test_delete_connection(self):
        conn = create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
        ))
        assert delete_connection(conn.id) is True
        assert get_connection(conn.id) is None

    def test_delete_nonexistent(self):
        assert delete_connection("nonexistent") is False

    def test_list_connections(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
        ))
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="github",
            auth_type=AuthType.API_KEY,
        ))
        conns = list_connections(ORG_ID)
        assert len(conns) == 2

    def test_list_connections_by_category(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
        ))
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="github",
            auth_type=AuthType.API_KEY,
        ))
        comm = list_connections(ORG_ID, ProviderCategory.COMMUNICATION)
        assert len(comm) == 1
        assert comm[0].provider_id == "slack"

    def test_list_connections_other_org(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
        ))
        assert list_connections("other-org") == []


# ── Event Routing Tests ─────────────────────────────────────────

class TestEventRouting:
    def test_route_event(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
            subscribed_events=["incident.created"],
        ))
        routing = route_event(ORG_ID, "incident.created", {"title": "Test"})
        assert len(routing.routed_to) == 1
        assert "Slack" in routing.routed_to

    def test_route_event_wildcard(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
            subscribed_events=["*"],
        ))
        routing = route_event(ORG_ID, "any.event", {})
        assert len(routing.routed_to) == 1

    def test_route_event_no_match(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
            subscribed_events=["incident.created"],
        ))
        routing = route_event(ORG_ID, "review.reminder", {})
        assert len(routing.routed_to) == 0

    def test_route_event_disconnected(self):
        conn = create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
            subscribed_events=["*"],
        ))
        update_connection(conn.id, IntegrationConnectionUpdate(
            status=IntegrationStatus.DISCONNECTED,
        ))
        routing = route_event(ORG_ID, "incident.created", {})
        assert len(routing.routed_to) == 0

    def test_route_event_multiple_targets(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
            subscribed_events=["incident.created"],
        ))
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="teams",
            auth_type=AuthType.WEBHOOK,
            subscribed_events=["incident.created"],
        ))
        routing = route_event(ORG_ID, "incident.created", {"title": "Test"})
        assert len(routing.routed_to) == 2


# ── Dashboard Tests ─────────────────────────────────────────────

class TestHubDashboard:
    def test_dashboard(self):
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="slack",
            auth_type=AuthType.WEBHOOK,
        ))
        create_connection(IntegrationConnectionCreate(
            organization_id=ORG_ID,
            provider_id="github",
            auth_type=AuthType.API_KEY,
        ))
        dashboard = get_hub_dashboard(ORG_ID)
        assert dashboard.total_providers >= 15
        assert dashboard.connected_count == 2
        assert dashboard.error_count == 0
        assert "communication" in dashboard.by_category
        assert "code" in dashboard.by_category

    def test_empty_dashboard(self):
        dashboard = get_hub_dashboard(ORG_ID)
        assert dashboard.connected_count == 0
        assert dashboard.error_count == 0
