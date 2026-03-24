# Copyright (c) 2026 Yutaro Maeda
# Licensed under the MIT License. See LICENSE file for details.

"""Tests for the task manager service."""

from __future__ import annotations

import pytest

from app.db.database import get_db, reset_db
from app.models import ActionTaskCreate, ActionTaskUpdate, TaskStatus
from app.services.task_manager import (
    create_task,
    create_tasks_from_gap_analysis,
    get_board_summary,
    get_task,
    list_tasks,
    update_task,
)


@pytest.fixture(autouse=True)
def _setup_db(tmp_path):
    reset_db()
    db_url = f"sqlite:///{tmp_path}/test.db"
    db = get_db(db_url)
    db.create_tables()
    yield
    reset_db()


class TestTaskManager:
    """Task management tests."""

    def test_create_task(self):
        task = create_task(ActionTaskCreate(
            organization_id="org-001",
            title="Test task",
            description="A test",
        ))
        assert task.id
        assert task.title == "Test task"
        assert task.status == TaskStatus.TODO

    def test_get_task(self):
        created = create_task(ActionTaskCreate(
            organization_id="org-001",
            title="Test task",
        ))
        loaded = get_task(created.id)
        assert loaded is not None
        assert loaded.title == "Test task"

    def test_get_nonexistent(self):
        assert get_task("nonexistent") is None

    def test_update_status(self):
        task = create_task(ActionTaskCreate(
            organization_id="org-001",
            title="Test",
        ))
        updated = update_task(task.id, ActionTaskUpdate(status=TaskStatus.IN_PROGRESS))
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_update_assignee(self):
        task = create_task(ActionTaskCreate(
            organization_id="org-001",
            title="Test",
        ))
        updated = update_task(task.id, ActionTaskUpdate(assignee="Taro"))
        assert updated is not None
        assert updated.assignee == "Taro"

    def test_update_with_note(self):
        task = create_task(ActionTaskCreate(
            organization_id="org-001",
            title="Test",
        ))
        updated = update_task(task.id, ActionTaskUpdate(note="Progress made"))
        assert updated is not None
        assert len(updated.notes) == 1
        assert "Progress made" in updated.notes[0]

    def test_update_nonexistent(self):
        result = update_task("nonexistent", ActionTaskUpdate(status=TaskStatus.DONE))
        assert result is None

    def test_list_tasks(self):
        create_task(ActionTaskCreate(organization_id="org-001", title="Task 1"))
        create_task(ActionTaskCreate(organization_id="org-001", title="Task 2"))
        create_task(ActionTaskCreate(organization_id="org-002", title="Task 3"))
        tasks = list_tasks("org-001")
        assert len(tasks) == 2

    def test_list_tasks_with_filter(self):
        t1 = create_task(ActionTaskCreate(organization_id="org-001", title="Task 1"))
        create_task(ActionTaskCreate(organization_id="org-001", title="Task 2"))
        update_task(t1.id, ActionTaskUpdate(status=TaskStatus.DONE))
        done_tasks = list_tasks("org-001", TaskStatus.DONE)
        assert len(done_tasks) == 1

    def test_board_summary(self):
        t1 = create_task(ActionTaskCreate(organization_id="org-001", title="Task 1"))
        create_task(ActionTaskCreate(organization_id="org-001", title="Task 2"))
        update_task(t1.id, ActionTaskUpdate(status=TaskStatus.IN_PROGRESS))

        board = get_board_summary("org-001")
        assert board.total == 2
        assert board.in_progress_count == 1
        assert board.todo_count == 1
        assert board.done_count == 0

    def test_create_from_gap_analysis(self):
        gaps = [
            {
                "req_id": "C01-R01",
                "title": "人間の尊厳",
                "status": "non_compliant",
                "priority": "high",
                "improvement_actions": ["Action A", "Action B"],
            },
            {
                "req_id": "C01-R02",
                "title": "意思決定",
                "status": "compliant",
                "priority": "low",
                "improvement_actions": ["Should not appear"],
            },
        ]
        tasks = create_tasks_from_gap_analysis("org-001", gaps)
        # Only non-compliant items should generate tasks
        assert len(tasks) == 2  # 2 actions from C01-R01
        assert tasks[0].gap_req_id == "C01-R01"
