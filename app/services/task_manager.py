# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""改善アクションのタスク管理サービス.

ギャップ分析で出た改善アクションをタスク化し、
担当者アサイン・期限設定・進捗管理を行う。
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.db.database import get_db
from app.models import (
    ActionTask,
    ActionTaskCreate,
    ActionTaskUpdate,
    TaskStatus,
    TaskBoardSummary,
)


def create_task(task_data: ActionTaskCreate) -> ActionTask:
    """改善アクションタスクを作成.

    Args:
        task_data: タスク作成データ

    Returns:
        ActionTask: 作成されたタスク
    """
    task = ActionTask(
        organization_id=task_data.organization_id,
        gap_req_id=task_data.gap_req_id,
        title=task_data.title,
        description=task_data.description,
        assignee=task_data.assignee,
        due_date=task_data.due_date,
        priority=task_data.priority,
    )

    db = get_db()
    with db.get_session() as session:
        from app.db.database import ActionTaskRow

        row = ActionTaskRow(
            id=task.id,
            organization_id=task.organization_id,
            result_json=task.model_dump_json(),
        )
        session.add(row)
        session.commit()

    return task


def update_task(task_id: str, update: ActionTaskUpdate) -> ActionTask | None:
    """タスクを更新.

    Args:
        task_id: タスクID
        update: 更新データ

    Returns:
        ActionTask | None: 更新されたタスク、または見つからない場合None
    """
    db = get_db()
    with db.get_session() as session:
        from app.db.database import ActionTaskRow

        row = session.query(ActionTaskRow).filter_by(id=task_id).first()
        if row is None:
            return None

        task = ActionTask.model_validate_json(row.result_json)

        if update.status is not None:
            task.status = update.status
        if update.assignee is not None:
            task.assignee = update.assignee
        if update.due_date is not None:
            task.due_date = update.due_date
        if update.priority is not None:
            task.priority = update.priority
        if update.note is not None:
            task.notes.append(
                f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] {update.note}"
            )

        task.updated_at = datetime.now(timezone.utc).isoformat()

        row.result_json = task.model_dump_json()
        session.commit()

    return task


def get_task(task_id: str) -> ActionTask | None:
    """IDからタスクを取得."""
    db = get_db()
    with db.get_session() as session:
        from app.db.database import ActionTaskRow

        row = session.query(ActionTaskRow).filter_by(id=task_id).first()
        if row is None:
            return None
        return ActionTask.model_validate_json(row.result_json)


def list_tasks(
    organization_id: str,
    status: TaskStatus | None = None,
) -> list[ActionTask]:
    """組織のタスク一覧を取得.

    Args:
        organization_id: 組織ID
        status: フィルタするステータス（省略時は全件）

    Returns:
        list[ActionTask]: タスクリスト
    """
    db = get_db()
    with db.get_session() as session:
        from app.db.database import ActionTaskRow

        rows = (
            session.query(ActionTaskRow)
            .filter_by(organization_id=organization_id)
            .all()
        )
        tasks = [ActionTask.model_validate_json(r.result_json) for r in rows]
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks


def get_board_summary(organization_id: str) -> TaskBoardSummary:
    """カンバンボード用のサマリーを取得.

    Args:
        organization_id: 組織ID

    Returns:
        TaskBoardSummary: ボードサマリー
    """
    tasks = list_tasks(organization_id)

    todo = [t for t in tasks if t.status == TaskStatus.TODO]
    in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
    done = [t for t in tasks if t.status == TaskStatus.DONE]

    overdue = [
        t for t in tasks
        if t.due_date
        and t.status != TaskStatus.DONE
        and t.due_date < datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ]

    return TaskBoardSummary(
        organization_id=organization_id,
        total=len(tasks),
        todo_count=len(todo),
        in_progress_count=len(in_progress),
        done_count=len(done),
        overdue_count=len(overdue),
        todo_tasks=todo,
        in_progress_tasks=in_progress,
        done_tasks=done,
    )


def create_tasks_from_gap_analysis(
    organization_id: str,
    gaps: list[dict],
) -> list[ActionTask]:
    """ギャップ分析結果から自動的にタスクを生成.

    Args:
        organization_id: 組織ID
        gaps: ギャップ分析のgapsリスト

    Returns:
        list[ActionTask]: 生成されたタスクリスト
    """
    created: list[ActionTask] = []
    for gap in gaps:
        status_val = gap.get("status", "")
        if status_val == "compliant":
            continue

        actions = gap.get("improvement_actions", [])
        for action in actions:
            task_data = ActionTaskCreate(
                organization_id=organization_id,
                gap_req_id=gap.get("req_id", ""),
                title=action,
                description=f"要件 {gap.get('req_id', '')}: {gap.get('title', '')} の改善アクション",
                priority=gap.get("priority", "medium"),
            )
            task = create_task(task_data)
            created.append(task)

    return created
