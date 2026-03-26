# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""AutoFix（自動修復）エンジン.

診断で「要対応」と出た項目に対して、必要なポリシー文書・チェックリスト・
エビデンステンプレート・タスクリスト・セルフチェック質問を自動生成する。

v2: policy_templates.py の実用的な雛形文書を使用。
    文書に status フィールド（draft → review → approved）を追加。
    承認すると該当要件のスコアが自動更新される。

Anthropic APIキーがない場合はテンプレートベースの文書生成（穴埋め方式）。
APIキーがある場合はClaude APIで組織の状況に合わせた文書をカスタム生成。
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from app.knowledge.autofix_definitions import (
    AutoFixDefinition,
    get_autofix_definition,
)
from app.knowledge.policy_templates import get_policy_template
from app.guidelines.meti_v1_1 import get_requirement
from app.models import (
    AutoFixResult,
    AutoFixTask,
    ChecklistItem,
    ComplianceStatus,
    DocumentStatus,
    GeneratedDocument,
    RequirementGap,
    SelfCheckItem,
)


class AutoFixEngine:
    """改善提案を自動実行するエンジン."""

    def fix_requirement(
        self,
        requirement_id: str,
        org_context: dict[str, str] | None = None,
    ) -> AutoFixResult:
        """1つの要件に対する自動修復を実行.

        Args:
            requirement_id: 要件ID（例: "C01-R01"）
            org_context: 組織情報（org_name, industry 等）

        Returns:
            AutoFixResult: 生成された文書・タスク等
        """
        if org_context is None:
            org_context = {}

        org_name = org_context.get("org_name", "貴社")
        industry = org_context.get("industry", "")
        ai_usage = org_context.get("ai_usage", "")
        date_str = datetime.now(timezone.utc).strftime("%Y年%m月%d日")

        # 要件情報を取得
        req = get_requirement(requirement_id)
        req_title = req.title if req else requirement_id

        # AutoFix定義を取得
        defn = get_autofix_definition(requirement_id)

        if defn is None:
            # 定義がない要件には汎用的なAutoFixを返す
            return self._generate_generic_fix(requirement_id, req_title, org_name, date_str)

        # 1) 実用的雛形文書（policy_templates.py）を優先して生成
        policy_template = get_policy_template(requirement_id)
        if policy_template:
            documents = self._generate_from_policy_template(
                requirement_id, policy_template, defn, org_name, date_str, industry, ai_usage,
            )
        else:
            # フォールバック: autofix_definitions.py のテンプレートを使用
            documents = self._generate_documents_from_template(defn, org_name, date_str)

        # APIキーがある場合はAI生成版で上書き
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and not api_key.startswith("sk-ant-xxx"):
            ai_documents = self._generate_documents_with_ai(
                defn, org_context, api_key
            )
            if ai_documents:
                documents = ai_documents

        # タスクリスト生成
        tasks = [
            AutoFixTask(
                title=td.title,
                description=td.description,
                assignee_role=td.assignee_role,
                deadline_days=td.deadline_days,
                depends_on=list(td.depends_on),
            )
            for td in defn.tasks
        ]

        # チェックリスト（文書からchecklist型のものを抽出）
        checklist_items: list[ChecklistItem] = []
        for td in defn.tasks:
            checklist_items.append(ChecklistItem(text=td.title, checked=False))

        # セルフチェック質問
        self_check = [
            SelfCheckItem(
                question=sc.question,
                expected_answer=sc.expected_answer,
            )
            for sc in defn.self_check_questions
        ]

        return AutoFixResult(
            requirement_id=requirement_id,
            requirement_title=req_title,
            generated_documents=documents,
            checklist=checklist_items,
            tasks=tasks,
            self_check_questions=self_check,
            status="generated",
        )

    def fix_all_gaps(
        self,
        gaps: list[RequirementGap],
        org_context: dict[str, str] | None = None,
    ) -> list[AutoFixResult]:
        """全Gapに対する自動修復を一括実行.

        Args:
            gaps: ギャップ分析結果のgapsリスト
            org_context: 組織情報

        Returns:
            list[AutoFixResult]: 各要件の修復結果
        """
        results: list[AutoFixResult] = []
        for gap in gaps:
            if gap.status == ComplianceStatus.COMPLIANT:
                continue
            result = self.fix_requirement(gap.req_id, org_context)
            results.append(result)
        return results

    def approve_document(
        self,
        result: AutoFixResult,
        document_index: int = 0,
    ) -> AutoFixResult:
        """文書を承認し、ステータスを更新する.

        Args:
            result: AutoFixResult
            document_index: 承認する文書のインデックス

        Returns:
            更新された AutoFixResult
        """
        if 0 <= document_index < len(result.generated_documents):
            doc = result.generated_documents[document_index]
            doc.status = DocumentStatus.APPROVED

        # 全文書が承認済みなら result の status を completed に更新
        all_approved = all(
            d.status == DocumentStatus.APPROVED
            for d in result.generated_documents
        )
        if all_approved:
            result.status = "completed"

        return result

    def approve_all_documents(
        self,
        result: AutoFixResult,
    ) -> AutoFixResult:
        """全文書を一括承認する.

        Args:
            result: AutoFixResult

        Returns:
            更新された AutoFixResult
        """
        for doc in result.generated_documents:
            doc.status = DocumentStatus.APPROVED
        result.status = "completed"
        return result

    def generate_policy_document(
        self,
        requirement_id: str,
        org_context: dict[str, str] | None = None,
    ) -> str:
        """要件に対応するポリシー文書を自動生成.

        Args:
            requirement_id: 要件ID
            org_context: 組織情報

        Returns:
            str: 生成されたポリシー文書（Markdown）
        """
        result = self.fix_requirement(requirement_id, org_context)
        policy_docs = [
            d for d in result.generated_documents
            if d.doc_type == "policy"
        ]
        if policy_docs:
            return policy_docs[0].content
        # ポリシー文書がない場合は最初の文書を返す
        if result.generated_documents:
            return result.generated_documents[0].content
        return ""

    def generate_checklist(
        self,
        requirement_id: str,
    ) -> list[ChecklistItem]:
        """対応チェックリストを自動生成.

        Args:
            requirement_id: 要件ID

        Returns:
            list[ChecklistItem]: チェックリスト
        """
        result = self.fix_requirement(requirement_id)
        return result.checklist

    def generate_evidence_template(
        self,
        requirement_id: str,
        org_context: dict[str, str] | None = None,
    ) -> str:
        """エビデンスのテンプレートを生成.

        Args:
            requirement_id: 要件ID
            org_context: 組織情報

        Returns:
            str: エビデンステンプレート（Markdown）
        """
        result = self.fix_requirement(requirement_id, org_context)
        template_docs = [
            d for d in result.generated_documents
            if d.doc_type == "template"
        ]
        if template_docs:
            return template_docs[0].content
        return ""

    def generate_task_plan(
        self,
        requirement_id: str,
        org_context: dict[str, str] | None = None,
    ) -> list[AutoFixTask]:
        """実行タスクリストを生成（担当者/期限付き）.

        Args:
            requirement_id: 要件ID
            org_context: 組織情報

        Returns:
            list[AutoFixTask]: タスクリスト
        """
        result = self.fix_requirement(requirement_id, org_context)
        return result.tasks

    # ── 内部メソッド ──

    def _generate_from_policy_template(
        self,
        requirement_id: str,
        policy_template: str,
        defn: AutoFixDefinition,
        org_name: str,
        date_str: str,
        industry: str,
        ai_usage: str,
    ) -> list[GeneratedDocument]:
        """実用的雛形文書（policy_templates.py）から文書を生成.

        雛形文書を主文書として生成し、autofix_definitions の補助文書も含める。
        """
        # プレースホルダを置換
        content = policy_template.format(
            org_name=org_name,
            date=date_str,
            industry=industry or "（業種未設定）",
            ai_usage=ai_usage or "（AI利用状況未設定）",
        )

        # 主文書のタイトルとdoc_typeを判定
        primary_title = defn.documents[0].title if defn.documents else f"{requirement_id} 対応文書"
        primary_doc_type = defn.documents[0].doc_type if defn.documents else "policy"

        documents: list[GeneratedDocument] = [
            GeneratedDocument(
                title=primary_title,
                content=content,
                doc_type=primary_doc_type,
                status=DocumentStatus.DRAFT,
            ),
        ]

        # autofix_definitions の補助文書（2番目以降）も追加
        if len(defn.documents) > 1:
            for doc_def in defn.documents[1:]:
                aux_content = doc_def.template.format(
                    org_name=org_name,
                    date=date_str,
                )
                documents.append(
                    GeneratedDocument(
                        title=doc_def.title,
                        content=aux_content,
                        doc_type=doc_def.doc_type,
                        status=DocumentStatus.DRAFT,
                    )
                )

        return documents

    def _generate_documents_from_template(
        self,
        defn: AutoFixDefinition,
        org_name: str,
        date_str: str,
    ) -> list[GeneratedDocument]:
        """テンプレートベースの文書生成."""
        documents: list[GeneratedDocument] = []
        for doc_def in defn.documents:
            content = doc_def.template.format(
                org_name=org_name,
                date=date_str,
            )
            documents.append(
                GeneratedDocument(
                    title=doc_def.title,
                    content=content,
                    doc_type=doc_def.doc_type,
                )
            )
        return documents

    def _generate_documents_with_ai(
        self,
        defn: AutoFixDefinition,
        org_context: dict[str, str],
        api_key: str,
    ) -> list[GeneratedDocument]:
        """Claude APIを使った文書生成.

        APIエラー時はNoneを返し、テンプレート版にフォールバックする。
        """
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            org_name = org_context.get("org_name", "貴社")
            industry = org_context.get("industry", "")
            size = org_context.get("size", "")

            documents: list[GeneratedDocument] = []

            for doc_def in defn.documents:
                prompt = (
                    f"あなたはAIガバナンスの専門家です。\n"
                    f"以下の条件で{doc_def.doc_type}文書を作成してください。\n\n"
                    f"## 条件\n"
                    f"- 組織名: {org_name}\n"
                    f"- 業種: {industry or '不明'}\n"
                    f"- 規模: {size or '不明'}\n"
                    f"- 文書タイプ: {doc_def.doc_type}\n"
                    f"- 文書タイトル: {doc_def.title}\n"
                    f"- 要件ID: {defn.requirement_id}\n\n"
                    f"## テンプレート（これをベースに組織に合わせてカスタマイズ）\n"
                    f"{doc_def.template}\n\n"
                    f"Markdown形式で出力してください。日本語で記述してください。"
                )

                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=3000,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = message.content[0].text

                documents.append(
                    GeneratedDocument(
                        title=doc_def.title,
                        content=content,
                        doc_type=doc_def.doc_type,
                    )
                )

            return documents
        except Exception:
            return []

    def _generate_generic_fix(
        self,
        requirement_id: str,
        req_title: str,
        org_name: str,
        date_str: str,
    ) -> AutoFixResult:
        """AutoFix定義がない要件への汎用的な修復."""
        generic_doc = GeneratedDocument(
            title=f"{req_title} 対応方針書",
            content=(
                f"# {req_title} 対応方針書\n\n"
                f"**組織名**: {org_name}\n"
                f"**作成日**: {date_str}\n\n"
                f"## 1. 目的\n"
                f"要件「{req_title}」（{requirement_id}）への対応方針を定める。\n\n"
                f"## 2. 対応計画\n"
                f"- 現状の調査と課題の特定\n"
                f"- 改善計画の策定\n"
                f"- 改善の実施\n"
                f"- 効果検証\n\n"
                f"---\n"
                f"*本文書はJPGovAIにより自動生成されたドラフトです。*"
            ),
            doc_type="policy",
        )

        generic_tasks = [
            AutoFixTask(
                title="現状を詳細に調査する",
                description=f"要件「{req_title}」に対する現状を調査する",
                assignee_role="AIガバナンス責任者",
                deadline_days=14,
            ),
            AutoFixTask(
                title="改善計画を策定する",
                description="調査結果に基づき改善計画を策定し、責任者と期限を設定する",
                assignee_role="AIガバナンス責任者",
                deadline_days=30,
                depends_on=[0],
            ),
        ]

        return AutoFixResult(
            requirement_id=requirement_id,
            requirement_title=req_title,
            generated_documents=[generic_doc],
            checklist=[
                ChecklistItem(text="現状を調査する", checked=False),
                ChecklistItem(text="改善計画を策定する", checked=False),
            ],
            tasks=generic_tasks,
            self_check_questions=[
                SelfCheckItem(
                    question=f"「{req_title}」に対する改善計画を策定しましたか？",
                    expected_answer="yes",
                ),
            ],
            status="generated",
        )
