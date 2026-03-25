# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Tests for the evidence collector service."""

from __future__ import annotations

import pytest

from app.services.evidence_collector import (
    AWSCollector,
    CollectionStatus,
    CollectorType,
    GitHubCollector,
    JiraCollector,
    ManualCollector,
    get_collection_dashboard,
    get_collector_config,
    list_collector_configs,
    register_collector_config,
    reset_collectors,
    run_all_collections,
    run_collection,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_collectors()
    yield
    reset_collectors()


ORG_ID = "org-test-001"


# ── GitHub Collector Tests ──────────────────────────────────────

class TestGitHubCollector:
    def test_validate_config_valid(self):
        collector = GitHubCollector()
        errors = collector.validate_config({
            "token": "ghp_xxx",
            "repos": ["owner/repo1"],
        })
        assert errors == []

    def test_validate_config_missing_token(self):
        collector = GitHubCollector()
        errors = collector.validate_config({"repos": ["owner/repo1"]})
        assert len(errors) == 1
        assert "Token" in errors[0]

    def test_validate_config_missing_repos(self):
        collector = GitHubCollector()
        errors = collector.validate_config({"token": "ghp_xxx"})
        assert len(errors) == 1
        assert "repository" in errors[0].lower()

    def test_collect(self):
        collector = GitHubCollector()
        result = collector.collect(ORG_ID, {
            "token": "ghp_xxx",
            "repos": ["owner/repo1", "owner/repo2"],
        })
        assert result.status == CollectionStatus.SUCCESS
        assert result.items_collected > 0
        assert result.items_mapped > 0
        assert len(result.evidence_items) == 6  # 3 checks * 2 repos
        assert result.collector_type == CollectorType.GITHUB

    def test_collect_evidence_has_requirement_ids(self):
        collector = GitHubCollector()
        result = collector.collect(ORG_ID, {
            "token": "ghp_xxx",
            "repos": ["owner/repo1"],
        })
        for item in result.evidence_items:
            assert len(item.requirement_ids) > 0

    def test_collector_type(self):
        assert GitHubCollector().collector_type() == CollectorType.GITHUB


# ── AWS Collector Tests ─────────────────────────────────────────

class TestAWSCollector:
    def test_validate_config_valid(self):
        collector = AWSCollector()
        errors = collector.validate_config({
            "aws_account_id": "123456789012",
            "region": "ap-northeast-1",
        })
        assert errors == []

    def test_validate_config_missing(self):
        collector = AWSCollector()
        errors = collector.validate_config({})
        assert len(errors) == 2

    def test_collect(self):
        collector = AWSCollector()
        result = collector.collect(ORG_ID, {
            "aws_account_id": "123456789012",
            "region": "ap-northeast-1",
        })
        assert result.status == CollectionStatus.SUCCESS
        assert result.items_collected == 3  # IAM, CloudTrail, Config Rules
        assert result.collector_type == CollectorType.AWS

    def test_collector_type(self):
        assert AWSCollector().collector_type() == CollectorType.AWS


# ── Jira Collector Tests ────────────────────────────────────────

class TestJiraCollector:
    def test_validate_config_valid(self):
        collector = JiraCollector()
        errors = collector.validate_config({
            "jira_url": "https://company.atlassian.net",
            "api_token": "xxx",
            "project_key": "GOV",
        })
        assert errors == []

    def test_validate_config_missing(self):
        collector = JiraCollector()
        errors = collector.validate_config({})
        assert len(errors) == 3

    def test_collect(self):
        collector = JiraCollector()
        result = collector.collect(ORG_ID, {
            "jira_url": "https://company.atlassian.net",
            "api_token": "xxx",
            "project_key": "GOV",
        })
        assert result.status == CollectionStatus.SUCCESS
        assert result.items_collected == 2
        assert result.collector_type == CollectorType.JIRA

    def test_collector_type(self):
        assert JiraCollector().collector_type() == CollectorType.JIRA


# ── Manual Collector Tests ──────────────────────────────────────

class TestManualCollector:
    def test_collect(self):
        collector = ManualCollector()
        result = collector.collect(ORG_ID, {})
        assert result.status == CollectionStatus.SUCCESS
        assert result.items_collected == 0

    def test_validate_config(self):
        assert ManualCollector().validate_config({}) == []


# ── Collector Manager Tests ─────────────────────────────────────

class TestCollectorManager:
    def test_register_config(self):
        config = register_collector_config(
            ORG_ID,
            CollectorType.GITHUB,
            {"token": "ghp_xxx", "repos": ["owner/repo1"]},
        )
        assert config.enabled is True
        assert config.collector_type == CollectorType.GITHUB

    def test_register_config_invalid(self):
        config = register_collector_config(
            ORG_ID,
            CollectorType.GITHUB,
            {},  # missing token and repos
        )
        assert config.enabled is False
        assert config.last_status == CollectionStatus.FAILURE

    def test_get_config(self):
        config = register_collector_config(
            ORG_ID, CollectorType.GITHUB,
            {"token": "ghp_xxx", "repos": ["owner/repo1"]},
        )
        fetched = get_collector_config(config.id)
        assert fetched is not None
        assert fetched.id == config.id

    def test_list_configs(self):
        register_collector_config(
            ORG_ID, CollectorType.GITHUB,
            {"token": "ghp_xxx", "repos": ["owner/repo1"]},
        )
        register_collector_config(
            ORG_ID, CollectorType.AWS,
            {"aws_account_id": "123", "region": "us-east-1"},
        )
        configs = list_collector_configs(ORG_ID)
        assert len(configs) == 2

    def test_run_collection(self):
        config = register_collector_config(
            ORG_ID, CollectorType.GITHUB,
            {"token": "ghp_xxx", "repos": ["owner/repo1"]},
        )
        result = run_collection(config.id)
        assert result is not None
        assert result.status == CollectionStatus.SUCCESS
        assert result.items_collected > 0

        # Config updated
        updated = get_collector_config(config.id)
        assert updated is not None
        assert updated.last_run != ""
        assert updated.last_status == CollectionStatus.SUCCESS

    def test_run_collection_nonexistent(self):
        assert run_collection("nonexistent") is None

    def test_run_all_collections(self):
        register_collector_config(
            ORG_ID, CollectorType.GITHUB,
            {"token": "ghp_xxx", "repos": ["owner/repo1"]},
        )
        register_collector_config(
            ORG_ID, CollectorType.AWS,
            {"aws_account_id": "123", "region": "us-east-1"},
        )
        results = run_all_collections(ORG_ID)
        assert len(results) == 2
        assert all(r.status == CollectionStatus.SUCCESS for r in results)


# ── Dashboard Tests ─────────────────────────────────────────────

class TestCollectionDashboard:
    def test_dashboard(self):
        config = register_collector_config(
            ORG_ID, CollectorType.GITHUB,
            {"token": "ghp_xxx", "repos": ["owner/repo1"]},
        )
        run_collection(config.id)

        dashboard = get_collection_dashboard(ORG_ID)
        assert dashboard.total_collectors == 1
        assert dashboard.active_collectors == 1
        assert dashboard.total_evidence_collected > 0
        assert dashboard.total_mapped > 0
        assert dashboard.coverage_rate > 0
        assert "github" in dashboard.by_collector

    def test_empty_dashboard(self):
        dashboard = get_collection_dashboard(ORG_ID)
        assert dashboard.total_collectors == 0
        assert dashboard.total_evidence_collected == 0
