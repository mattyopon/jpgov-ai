# Copyright (c) 2026 Yutaro Maeda
# Licensed under the Business Source License 1.1. See LICENSE file for details.

"""Streamlit UI for JPGovAI - ISO 42001認証準備 & AIガバナンス管理.

使い方:
    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations


import requests
import streamlit as st

# APIベースURL
API_BASE = "http://localhost:8000/api"

st.set_page_config(
    page_title="JPGovAI - AI Governance 統合管理",
    page_icon="🏛️",
    layout="wide",
)


def api_get(path: str, params: dict | None = None) -> dict | list | None:
    """API GETリクエスト."""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API通信エラー: {e}")
        return None


def api_post(path: str, data: dict) -> dict | None:
    """API POSTリクエスト."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=data, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API通信エラー: {e}")
        return None


# ── Sidebar ───────────────────────────────────────────────────────

st.sidebar.title("JPGovAI")
st.sidebar.markdown("**AI Governance 統合管理**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "メニュー",
    [
        "ホーム",
        "組織登録",
        "自己診断",
        "ギャップ分析",
        "ISO 42001チェック",
        "AI推進法チェック",
        "リスクアセスメント",
        "マルチ規制ダッシュボード",
        "ポリシー生成",
        "タスク管理",
        "エビデンス管理",
        "レポート生成",
        "エクスポート",
        "監査証跡",
        "ガイドライン参照",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("対応規制:")
st.sidebar.markdown("- METI AI事業者ガイドライン v1.1")
st.sidebar.markdown("- ISO/IEC 42001:2023 (AIMS)")
st.sidebar.markdown("- AI推進法（2025年施行）")
st.sidebar.markdown("Version 0.2.0")

# ── Session State ─────────────────────────────────────────────────

if "org_id" not in st.session_state:
    st.session_state.org_id = ""
if "org_name" not in st.session_state:
    st.session_state.org_name = ""
if "assessment_id" not in st.session_state:
    st.session_state.assessment_id = ""
if "gap_id" not in st.session_state:
    st.session_state.gap_id = ""


# ── Pages ─────────────────────────────────────────────────────────

if page == "ホーム":
    st.title("JPGovAI - AI Governance 統合管理")
    st.markdown(
        """
        ### JPGovAIとは
        AI関連の3つの主要規制に対する準拠状況を一元管理するプラットフォームです。

        ### 対応規制
        | 規制 | 内容 |
        |------|------|
        | **METI AI事業者ガイドライン** | 経済産業省・総務省のAIガバナンス基準 |
        | **ISO/IEC 42001:2023** | AIマネジメントシステム国際標準 |
        | **AI推進法（2025年施行）** | 日本のAI基本法 |

        ### 機能一覧
        1. **自己診断**: 25問の質問票でAIガバナンス成熟度を診断
        2. **ギャップ分析**: ガイドラインの各要件に対する充足状況を可視化
        3. **ISO 42001チェック**: ISO認証対応状況をMETI結果から自動評価
        4. **AI推進法チェック**: AI推進法の準拠状況を確認
        5. **リスクアセスメント**: EU AI Act準拠のリスク分類
        6. **マルチ規制ダッシュボード**: 3規制の準拠状況を一画面で可視化
        7. **ポリシー生成**: 方針文書テンプレートを自動生成
        8. **タスク管理**: 改善アクションのカンバンボード管理
        9. **エビデンス管理**: 各要件に対するエビデンスを一元管理
        10. **レポート生成**: 申請用レポートをAIが自動生成
        11. **エクスポート**: CSV/JSON/認証パッケージの一括出力
        12. **監査証跡**: 全操作の改竄防止ログを自動記録
        """
    )

    # Health check
    health = api_get("/health")
    if health:
        st.success(f"APIサーバー接続OK (version: {health.get('version', '?')})")
    else:
        st.warning("APIサーバーに接続できません。`uvicorn app.main:app --reload` で起動してください。")

elif page == "組織登録":
    st.title("組織登録")
    st.markdown("AIガバナンス診断を行う組織の情報を登録します。")

    with st.form("org_form"):
        name = st.text_input("組織名", placeholder="株式会社サンプル")
        industry = st.selectbox(
            "業種",
            ["IT・通信", "金融・保険", "医療・ヘルスケア", "製造", "小売・EC", "公共・行政", "教育", "その他"],
        )
        size = st.selectbox(
            "企業規模",
            ["small (50人未満)", "medium (50-300人)", "large (300-1000人)", "enterprise (1000人以上)"],
        )
        ai_role = st.selectbox(
            "AI事業者としての立場",
            ["developer (AI開発者)", "provider (AI提供者)", "user (AI利用者)"],
        )
        submitted = st.form_submit_button("登録")

    if submitted and name:
        result = api_post(
            "/organizations",
            {
                "name": name,
                "industry": industry,
                "size": size.split(" ")[0],
                "ai_role": ai_role.split(" ")[0],
            },
        )
        if result:
            st.session_state.org_id = result["id"]
            st.session_state.org_name = name
            st.success(f"組織を登録しました。ID: {result['id']}")

    if st.session_state.org_id:
        st.info(f"現在の組織ID: {st.session_state.org_id}")

elif page == "自己診断":
    st.title("AI利用状況の自己診断")
    st.markdown("質問票に回答して、AIガバナンス成熟度を診断します。")

    if not st.session_state.org_id:
        st.warning("先に「組織登録」を行ってください。")
    else:
        questions = api_get("/guidelines/questions")
        if questions:
            answers = []
            with st.form("assessment_form"):
                for i, q in enumerate(questions):
                    st.markdown(f"**Q{i+1}. {q['text']}**")
                    selected = st.radio(
                        f"選択 (Q{i+1})",
                        options=range(len(q["options"])),
                        format_func=lambda x, opts=q["options"]: opts[x],
                        key=f"q_{q['question_id']}",
                        horizontal=True,
                    )
                    answers.append(
                        {"question_id": q["question_id"], "selected_index": selected}
                    )
                    st.markdown("---")

                submitted = st.form_submit_button("診断を実行", type="primary")

            if submitted:
                result = api_post(
                    "/assessment",
                    {
                        "organization_id": st.session_state.org_id,
                        "answers": answers,
                    },
                )
                if result:
                    st.session_state.assessment_id = result["id"]
                    st.success("診断が完了しました！")

                    # 結果表示
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("総合スコア", f"{result['overall_score']:.2f} / 4.00")
                    with col2:
                        st.metric("成熟度レベル", f"Level {result['maturity_level']}")

                    st.subheader("カテゴリ別スコア")
                    for cs in result.get("category_scores", []):
                        progress = cs["score"] / cs["max_score"]
                        st.markdown(f"**{cs['category_title']}**")
                        st.progress(progress, text=f"{cs['score']:.2f} / {cs['max_score']:.2f} (Level {cs['maturity_level']})")

elif page == "ギャップ分析":
    st.title("ギャップ分析")
    st.markdown("ガイドラインの各要件に対する充足状況を分析します。")

    if not st.session_state.assessment_id:
        st.warning("先に「自己診断」を実行してください。")
    else:
        if st.button("ギャップ分析を実行", type="primary"):
            with st.spinner("分析中...（AI改善提案を生成しています）"):
                result = api_post(
                    f"/gap-analysis?assessment_id={st.session_state.assessment_id}",
                    {},
                )
            if result:
                st.session_state.gap_id = result["id"]
                st.success("分析が完了しました！")

                # サマリー
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("充足", result["compliant_count"], delta_color="normal")
                with col2:
                    st.metric("部分充足", result["partial_count"], delta_color="off")
                with col3:
                    st.metric("未充足", result["non_compliant_count"], delta_color="inverse")

                # 要件別ステータス
                st.subheader("要件別ステータス")
                for gap in result.get("gaps", []):
                    status = gap["status"]
                    if status == "compliant":
                        color = "🟢"
                    elif status == "partial":
                        color = "🟡"
                    else:
                        color = "🔴"

                    with st.expander(f"{color} {gap['req_id']}: {gap['title']} ({status})"):
                        st.markdown(f"**スコア**: {gap['current_score']:.2f}")
                        st.markdown(f"**優先度**: {gap['priority']}")
                        if gap.get("gap_description"):
                            st.markdown(f"**ギャップ**: {gap['gap_description']}")
                        if gap.get("improvement_actions"):
                            st.markdown("**改善アクション**:")
                            for action in gap["improvement_actions"]:
                                st.markdown(f"  - {action}")

                # AI改善提案
                if result.get("ai_recommendations"):
                    st.subheader("AI改善提案")
                    st.markdown(result["ai_recommendations"])

elif page == "ISO 42001チェック":
    st.title("ISO/IEC 42001 (AIMS) 対応チェック")
    st.markdown("ISO 42001の要求事項に対する準拠状況をMETIギャップ分析結果から評価します。")

    if not st.session_state.gap_id:
        st.warning("先に「ギャップ分析」を実行してください。")
    else:
        if st.button("ISO 42001チェックを実行", type="primary"):
            with st.spinner("チェック中..."):
                result = api_post(
                    f"/iso-check?gap_analysis_id={st.session_state.gap_id}",
                    {},
                )
            if result:
                st.success("チェック完了！")

                # サマリー
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("充足", result["compliant_count"])
                with col2:
                    st.metric("部分充足", result["partial_count"])
                with col3:
                    st.metric("未充足", result["non_compliant_count"])
                with col4:
                    st.metric("総合スコア", f"{result['overall_score']:.2f}")

                # 条項別サマリー
                st.subheader("条項別サマリー")
                for clause in result.get("clause_summaries", []):
                    status = clause["status"]
                    if status == "compliant":
                        icon = "🟢"
                    elif status == "partial":
                        icon = "🟡"
                    else:
                        icon = "🔴"
                    st.markdown(
                        f"{icon} **{clause['clause_id']}. {clause['title']}** "
                        f"— {clause['compliant_count']}/{clause['total_requirements']}充足 "
                        f"(スコア: {clause['avg_score']:.2f})"
                    )

                # 個別要求事項
                st.subheader("要求事項別ステータス")
                for item in result.get("items", []):
                    status = item["status"]
                    if status == "compliant":
                        color = "🟢"
                    elif status == "partial":
                        color = "🟡"
                    elif status == "non_compliant":
                        color = "🔴"
                    else:
                        color = "⚪"
                    with st.expander(f"{color} {item['req_id']}: {item['title']} ({status})"):
                        st.markdown(f"**条項**: {item['clause']}")
                        st.markdown(f"**スコア**: {item['score']:.2f}")
                        st.markdown(f"**説明**: {item['description']}")
                        if item.get("meti_mapping_titles"):
                            st.markdown("**対応METI要件**:")
                            for mt in item["meti_mapping_titles"]:
                                st.markdown(f"  - {mt}")

elif page == "AI推進法チェック":
    st.title("AI推進法（2025年施行）要件一覧")
    st.markdown("AI推進法の要件とMETI/ISO 42001とのマッピングを表示します。")

    chapters = api_get("/guidelines/ai-promotion-act/chapters")
    requirements = api_get("/guidelines/ai-promotion-act/requirements")

    if chapters and requirements:
        for ch in chapters:
            with st.expander(f"{ch['chapter_id']}: {ch['title']} ({ch['requirement_count']}要件)"):
                st.markdown(ch["description"])
                ch_reqs = [r for r in requirements if True]  # filter by chapter would need chapter_id in req
                for r in requirements:
                    # Simple approach: show all requirements under their matching chapter
                    # Match by checking if the requirement's article correlates
                    pass

        st.subheader("全要件一覧")
        for r in requirements:
            obligation_badge = "🔴 義務" if r["obligation_type"] == "mandatory" else "🟡 努力義務"
            with st.expander(f"{obligation_badge} {r['req_id']}: {r['title']}"):
                st.markdown(f"**条文**: {r['article']}")
                st.markdown(f"**説明**: {r['description']}")
                if r.get("meti_mapping"):
                    st.markdown(f"**対応METI要件**: {', '.join(r['meti_mapping'])}")
                if r.get("iso_mapping"):
                    st.markdown(f"**対応ISO 42001**: {', '.join(r['iso_mapping'])}")

elif page == "リスクアセスメント":
    st.title("リスクアセスメント（EU AI Act準拠）")
    st.markdown("AIシステムのリスクレベルを分類し、追加要件を確認します。")

    if not st.session_state.org_id:
        st.warning("先に「組織登録」を行ってください。")
    else:
        tab1, tab2 = st.tabs(["新規アセスメント", "アセスメント一覧"])

        with tab1:
            questions = api_get("/risk-assessment/questions")
            if questions:
                with st.form("risk_form"):
                    system_name = st.text_input("AIシステム名", placeholder="顧客対応チャットボット")
                    system_desc = st.text_area("AIシステムの説明", placeholder="顧客からの問い合わせに自動回答するAIシステム")

                    st.markdown("### リスク分類質問")
                    answers = {}
                    for q in questions:
                        answers[q["key"]] = st.checkbox(q["question"], key=f"rq_{q['question_id']}")

                    submitted = st.form_submit_button("アセスメント実行", type="primary")

                if submitted and system_name:
                    result = api_post(
                        "/risk-assessment",
                        {
                            "organization_id": st.session_state.org_id,
                            "system_name": system_name,
                            "system_description": system_desc,
                            "answers": answers,
                        },
                    )
                    if result:
                        risk = result["overall_risk_level"]
                        if risk == "high":
                            st.error("リスクレベル: 高リスク (HIGH)")
                        elif risk == "limited":
                            st.warning("リスクレベル: 限定的リスク (LIMITED)")
                        else:
                            st.success("リスクレベル: 最小リスク (MINIMAL)")

                        st.subheader("追加要件")
                        for req in result.get("additional_requirements", []):
                            st.markdown(f"- {req}")

        with tab2:
            assessments = api_get(f"/risk-assessments/{st.session_state.org_id}")
            if assessments:
                for ra in assessments:
                    risk = ra["overall_risk_level"]
                    badge = "🔴" if risk == "high" else ("🟡" if risk == "limited" else "🟢")
                    with st.expander(f"{badge} {ra['system_name']} ({risk})"):
                        st.markdown(f"**説明**: {ra.get('system_description', '')}")
                        st.markdown(f"**ID**: {ra['id']}")
            else:
                st.info("まだアセスメントがありません。")

elif page == "マルチ規制ダッシュボード":
    st.title("マルチ規制ダッシュボード")
    st.markdown("METI + ISO 42001 + AI推進法の準拠状況を一画面で確認します。")

    if not st.session_state.gap_id:
        st.warning("先に「ギャップ分析」を実行してください。")
    else:
        dashboard = api_get(
            f"/dashboard/{st.session_state.org_id}",
            params={"gap_analysis_id": st.session_state.gap_id},
        )
        if dashboard:
            # 全体準拠率
            st.metric("全体準拠率", f"{dashboard['overall_compliance_rate']:.1%}")

            # 3規制のカード
            cols = st.columns(3)
            regulations = [
                ("meti_status", "METI"),
                ("iso_status", "ISO 42001"),
                ("act_status", "AI推進法"),
            ]
            for col, (key, label) in zip(cols, regulations):
                with col:
                    status = dashboard.get(key)
                    if status:
                        st.markdown(f"### {label}")
                        st.metric("準拠率", f"{status['compliance_rate']:.1%}")
                        st.metric("スコア", f"{status['overall_score']:.2f}")
                        st.markdown(
                            f"充足: {status['compliant_count']} / "
                            f"部分: {status['partial_count']} / "
                            f"未充足: {status['non_compliant_count']}"
                        )
                    else:
                        st.markdown(f"### {label}")
                        st.info("データなし")

            # 優先アクション
            st.subheader("優先改善アクション")
            for action in dashboard.get("priority_actions", [])[:10]:
                with st.expander(f"[{action['source']}] {action['req_id']}: {action['title']}"):
                    st.markdown(f"**優先度**: {action['priority']}")
                    if action.get("actions"):
                        for a in action["actions"]:
                            st.markdown(f"- {a}")

elif page == "ポリシー生成":
    st.title("ポリシーテンプレート自動生成")
    st.markdown("AIガバナンスに必要な方針文書のテンプレートを生成します。")

    if not st.session_state.org_id:
        st.warning("先に「組織登録」を行ってください。")
    else:
        org_name = st.session_state.org_name or "貴社"

        policy_types = api_get("/policies/types")
        if policy_types:
            tab1, tab2 = st.tabs(["個別生成", "一括生成"])

            with tab1:
                selected_type = st.selectbox(
                    "ポリシー種別",
                    options=[p["type"] for p in policy_types],
                    format_func=lambda x: next(p["title"] for p in policy_types if p["type"] == x),
                )
                if st.button("生成", type="primary"):
                    result = api_post(
                        "/policies/generate",
                        {
                            "organization_id": st.session_state.org_id,
                            "organization_name": org_name,
                            "policy_type": selected_type,
                        },
                    )
                    if result:
                        st.success(f"「{result['title']}」を生成しました。")
                        st.markdown(result["full_text"])
                        st.download_button(
                            "テキストをダウンロード",
                            result["full_text"],
                            file_name=f"{selected_type}_policy.md",
                        )

            with tab2:
                if st.button("全ポリシーを一括生成", type="primary"):
                    results = api_post(
                        f"/policies/generate-all?organization_id={st.session_state.org_id}&organization_name={org_name}",
                        {},
                    )
                    if results:
                        st.success(f"{len(results)}件のポリシーを生成しました。")
                        for doc in results:
                            with st.expander(doc["title"]):
                                st.markdown(doc["full_text"])

elif page == "タスク管理":
    st.title("改善アクション タスク管理")
    st.markdown("ギャップ分析で出た改善アクションのタスク管理を行います。")

    if not st.session_state.org_id:
        st.warning("先に「組織登録」を行ってください。")
    else:
        tab1, tab2, tab3 = st.tabs(["カンバンボード", "タスク作成", "ギャップから自動生成"])

        with tab1:
            board = api_get(f"/tasks/board/{st.session_state.org_id}")
            if board:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("総タスク数", board["total"])
                with col2:
                    st.metric("未着手", board["todo_count"])
                with col3:
                    st.metric("進行中", board["in_progress_count"])
                with col4:
                    st.metric("完了", board["done_count"])

                # カンバンボード風の3カラム
                cols = st.columns(3)
                sections = [
                    ("📋 未着手 (TODO)", board.get("todo_tasks", [])),
                    ("🔄 進行中", board.get("in_progress_tasks", [])),
                    ("✅ 完了", board.get("done_tasks", [])),
                ]
                for col, (title, tasks) in zip(cols, sections):
                    with col:
                        st.markdown(f"### {title}")
                        for task in tasks:
                            with st.expander(f"{task['title'][:40]}"):
                                st.markdown(f"**要件**: {task.get('gap_req_id', '-')}")
                                st.markdown(f"**担当者**: {task.get('assignee', '未割当')}")
                                st.markdown(f"**期限**: {task.get('due_date', '-')}")
                                st.markdown(f"**優先度**: {task.get('priority', '-')}")

        with tab2:
            with st.form("task_form"):
                title = st.text_input("タスク名")
                description = st.text_area("説明")
                assignee = st.text_input("担当者")
                due_date = st.date_input("期限")
                priority = st.selectbox("優先度", ["high", "medium", "low"])
                submitted = st.form_submit_button("作成")

            if submitted and title:
                result = api_post(
                    "/tasks",
                    {
                        "organization_id": st.session_state.org_id,
                        "title": title,
                        "description": description,
                        "assignee": assignee,
                        "due_date": str(due_date),
                        "priority": priority,
                    },
                )
                if result:
                    st.success(f"タスクを作成しました: {result['title']}")

        with tab3:
            if not st.session_state.gap_id:
                st.warning("先に「ギャップ分析」を実行してください。")
            else:
                if st.button("ギャップ分析から自動生成", type="primary"):
                    with st.spinner("タスクを生成中..."):
                        result = api_post(
                            f"/tasks/from-gap-analysis?organization_id={st.session_state.org_id}&gap_analysis_id={st.session_state.gap_id}",
                            {},
                        )
                    if result:
                        st.success(f"{len(result)}件のタスクを生成しました。")

elif page == "エビデンス管理":
    st.title("エビデンス管理")
    st.markdown("各要件に対するエビデンスをアップロード・管理します。")

    if not st.session_state.org_id:
        st.warning("先に「組織登録」を行ってください。")
    else:
        tab1, tab2 = st.tabs(["アップロード", "充足率ダッシュボード"])

        with tab1:
            st.subheader("エビデンスのアップロード")
            requirements = api_get("/guidelines/requirements")
            if requirements:
                with st.form("evidence_form"):
                    req_options = {
                        f"{r['req_id']}: {r['title']}": r["req_id"]
                        for r in requirements
                    }
                    selected_req = st.selectbox("対象要件", list(req_options.keys()))
                    filename = st.text_input("ファイル名", placeholder="governance_policy_v1.pdf")
                    description = st.text_area("説明", placeholder="AIガバナンス基本方針文書（2024年版）")
                    file_type = st.selectbox(
                        "文書種別",
                        ["policy (方針文書)", "test_result (テスト結果)", "audit_log (監査ログ)",
                         "training_record (研修記録)", "other (その他)"],
                    )
                    submitted = st.form_submit_button("登録")

                if submitted and filename:
                    result = api_post(
                        "/evidence",
                        {
                            "organization_id": st.session_state.org_id,
                            "requirement_id": req_options[selected_req],
                            "filename": filename,
                            "description": description,
                            "file_type": file_type.split(" ")[0],
                        },
                    )
                    if result:
                        st.success(f"エビデンスを登録しました。ID: {result['id']}")

        with tab2:
            st.subheader("エビデンス充足率")
            summary = api_get(f"/evidence-summary/{st.session_state.org_id}")
            if summary:
                st.metric(
                    "全体充足率",
                    f"{summary['coverage_rate']:.0%}",
                )
                st.progress(summary["coverage_rate"])

                st.markdown("### カテゴリ別充足率")
                for cat_id, info in summary.get("by_category", {}).items():
                    rate = info.get("rate", 0)
                    st.markdown(f"**{info.get('title', cat_id)}**")
                    st.progress(
                        rate,
                        text=f"{info.get('covered', 0)}/{info.get('total', 0)} ({rate:.0%})",
                    )

elif page == "レポート生成":
    st.title("レポート生成")
    st.markdown("ISO 42001認証準備・AIガバナンス成熟度評価レポートを自動生成します。")

    if not st.session_state.assessment_id or not st.session_state.gap_id:
        st.warning("先に「自己診断」と「ギャップ分析」を実行してください。")
    else:
        if st.button("レポートを生成", type="primary"):
            with st.spinner("レポート生成中..."):
                result = api_post(
                    "/report",
                    {
                        "organization_id": st.session_state.org_id,
                        "assessment_id": st.session_state.assessment_id,
                        "gap_analysis_id": st.session_state.gap_id,
                        "include_evidence": True,
                    },
                )
            if result:
                st.success(f"レポートを生成しました: {result['filename']}")
                st.info(f"プレビュー: {result.get('content_preview', '')}")

elif page == "エクスポート":
    st.title("データエクスポート")
    st.markdown("診断・分析結果をCSV/JSONでエクスポート、または認証パッケージを生成します。")

    if not st.session_state.assessment_id:
        st.warning("先に「自己診断」を実行してください。")
    else:
        tab1, tab2, tab3 = st.tabs(["個別エクスポート", "ISO認証パッケージ", "METI報告パッケージ"])

        with tab1:
            st.subheader("個別データエクスポート")
            fmt = st.selectbox("フォーマット", ["json", "csv"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("診断結果をエクスポート"):
                    result = api_get(
                        f"/export/assessment/{st.session_state.assessment_id}",
                        params={"fmt": fmt},
                    )
                    if result:
                        st.download_button(
                            "ダウンロード",
                            result["content"],
                            file_name=f"assessment.{fmt}",
                        )
            with col2:
                if st.session_state.gap_id and st.button("ギャップ分析をエクスポート"):
                    result = api_get(
                        f"/export/gap-analysis/{st.session_state.gap_id}",
                        params={"fmt": fmt},
                    )
                    if result:
                        st.download_button(
                            "ダウンロード",
                            result["content"],
                            file_name=f"gap_analysis.{fmt}",
                        )

        with tab2:
            st.subheader("ISO 42001認証申請パッケージ")
            if st.session_state.gap_id:
                if st.button("ISO認証パッケージを生成", type="primary"):
                    result = api_post(
                        f"/export/iso-certification-package?assessment_id={st.session_state.assessment_id}&gap_analysis_id={st.session_state.gap_id}",
                        {},
                    )
                    if result:
                        st.success(f"パッケージを生成しました（{len(result.get('files', {}))}ファイル）")
                        for fname, content in result.get("files", {}).items():
                            st.download_button(
                                f"{fname}",
                                content,
                                file_name=fname,
                                key=f"dl_{fname}",
                            )

        with tab3:
            st.subheader("METI報告用パッケージ")
            if st.session_state.gap_id:
                if st.button("METI報告パッケージを生成", type="primary"):
                    result = api_post(
                        f"/export/meti-report-package?assessment_id={st.session_state.assessment_id}&gap_analysis_id={st.session_state.gap_id}",
                        {},
                    )
                    if result:
                        st.success(f"パッケージを生成しました（{len(result.get('files', {}))}ファイル）")
                        for fname, content in result.get("files", {}).items():
                            st.download_button(
                                f"{fname}",
                                content,
                                file_name=fname,
                                key=f"dl_meti_{fname}",
                            )

elif page == "監査証跡":
    st.title("監査証跡")
    st.markdown("全操作の改竄防止ログを確認します。")

    # チェーン検証
    col1, col2 = st.columns(2)
    with col1:
        if st.button("チェーン整合性を検証"):
            status = api_get("/audit/verify")
            if status:
                if status["chain_valid"]:
                    st.success(f"チェーン整合性: 有効 (イベント数: {status['total_events']})")
                else:
                    st.error("チェーン整合性: 改竄検出！")
                    for err in status.get("errors", []):
                        st.error(err)
                st.code(f"Merkle Root: {status['merkle_root']}", language="text")

    with col2:
        st.metric("", "SHA-256 ハッシュチェーン")
        st.caption("全イベントが暗号学的ハッシュで連鎖されています")

    # イベント一覧
    st.subheader("イベント一覧")
    events = api_get("/audit/events", params={"limit": 50})
    if events:
        for ev in reversed(events):
            with st.expander(
                f"#{ev['sequence']} | {ev['action']} | {ev['timestamp'][:19]}"
            ):
                st.json(ev)
    else:
        st.info("まだ監査イベントがありません。")

elif page == "ガイドライン参照":
    st.title("ガイドライン参照")

    tab1, tab2, tab3 = st.tabs(["METI AI事業者ガイドライン", "ISO 42001", "AI推進法"])

    with tab1:
        st.subheader("METI AI事業者ガイドライン 要件一覧")
        categories = api_get("/guidelines/categories")
        if categories:
            for cat in categories:
                with st.expander(
                    f"{cat['category_id']}: {cat['title']} ({cat['requirement_count']}要件)"
                ):
                    st.markdown(cat["description"])
                    requirements = api_get("/guidelines/requirements")
                    if requirements:
                        cat_reqs = [r for r in requirements if r["category_id"] == cat["category_id"]]
                        for r in cat_reqs:
                            st.markdown(f"**{r['req_id']}: {r['title']}**")
                            st.markdown(f"  {r['description']}")
                            st.caption(f"対象: {', '.join(r['target_roles'])}")
                            st.markdown("---")

    with tab2:
        st.subheader("ISO/IEC 42001:2023 要求事項一覧")
        clauses = api_get("/guidelines/iso42001/clauses")
        iso_reqs = api_get("/guidelines/iso42001/requirements")
        if clauses and iso_reqs:
            for clause in clauses:
                with st.expander(
                    f"条項{clause['clause_id']}: {clause['title']} ({clause['requirement_count']}要求事項)"
                ):
                    st.markdown(clause["description"])
                    for r in iso_reqs:
                        if r["clause"].startswith(clause["clause_id"] + ".") or r["clause"] == clause["clause_id"]:
                            st.markdown(f"**{r['req_id']} ({r['clause']}): {r['title']}**")
                            st.markdown(f"  {r['description']}")
                            if r.get("meti_mapping"):
                                st.caption(f"対応METI要件: {', '.join(r['meti_mapping'])}")
                            st.markdown("---")

    with tab3:
        st.subheader("AI推進法 要件一覧")
        act_chapters = api_get("/guidelines/ai-promotion-act/chapters")
        act_reqs = api_get("/guidelines/ai-promotion-act/requirements")
        if act_chapters and act_reqs:
            for ch in act_chapters:
                with st.expander(f"{ch['chapter_id']}: {ch['title']} ({ch['requirement_count']}要件)"):
                    st.markdown(ch["description"])

            st.markdown("---")
            for r in act_reqs:
                badge = "🔴 義務" if r["obligation_type"] == "mandatory" else "🟡 努力義務"
                with st.expander(f"{badge} {r['req_id']}: {r['title']}"):
                    st.markdown(f"**条文**: {r['article']}")
                    st.markdown(f"**説明**: {r['description']}")
                    if r.get("meti_mapping"):
                        st.markdown(f"**対応METI要件**: {', '.join(r['meti_mapping'])}")
                    if r.get("iso_mapping"):
                        st.markdown(f"**対応ISO 42001**: {', '.join(r['iso_mapping'])}")
