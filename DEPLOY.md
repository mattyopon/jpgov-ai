# JPGovAI デプロイ手順（Streamlit Community Cloud — 無料）

## 5分でデプロイ

### Step 1: Streamlit Community Cloudにサインアップ
https://share.streamlit.io/ にアクセス
→ 「Continue with GitHub」でGitHubアカウント（mattyopon）でログイン

### Step 2: 新しいアプリをデプロイ
1. ダッシュボードで「New app」をクリック
2. 以下を設定:
   - Repository: `mattyopon/jpgov-ai`
   - Branch: `master`
   - Main file path: `ui/streamlit_app.py`
3. 「Advanced settings」を開いて環境変数を設定:
   - `ANTHROPIC_API_KEY` = あなたのAnthropicキー（AIアドバイザー用。なくても動く）
4. 「Deploy!」をクリック

### Step 3: 完了
数分でデプロイ完了。URLが発行される:
`https://jpgov-ai-xxxx.streamlit.app/`

### Step 4: LPにリンクを追加
LPの「無料で診断する」ボタンのリンク先をStreamlit URLに変更。

## 費用
無料（Streamlit Community Cloud）

## 注意事項
- Streamlit Community Cloudは公開アプリ。誰でもアクセス可能。
- ANTHROPIC_API_KEYは「Secrets」に設定（一般公開されない）
- SQLiteはStreamlitの一時ファイルシステムに保存。アプリ再起動でリセットされる。
  → 本番運用時はPostgreSQLに移行が必要。
- 無料枠はリソース制限あり（1GBメモリ）。最初のMVPには十分。
