# JPGovAI 競合・先行技術調査レポート

**調査日: 2026年3月24日**
**調査者: Claude Opus 4.6**
**調査方針: 徹底的かつ残酷なまでに正直に**

---

## エグゼクティブサマリー（忖度なし）

### 結論を先に

1. **市場は実在する** — ただし「急成長中」ではなく「黎明期」。日本のAIガバナンス市場は2024年時点で推定数十億円規模、2030年に約125億円（Grand View Research）。世界市場のCAGR 35-45%は印象的だが、日本市場の絶対値は小さい。

2. **直接競合のSaaS製品は日本にほぼ存在しない** — ただし「存在しない」のは需要がないからかもしれない。コンサルファーム（PwC、EY、KPMG、デロイト、NEC、NRI）がサービスで席巻しており、SaaS化のインセンティブがまだ弱い。

3. **グローバル競合は強力** — Credo AI、Holistic AI、OneTrust、FairNow、Vantaなどが存在し、資金力・機能・顧客基盤で圧倒的。ただし日本語対応・日本規制特化は弱い。

4. **OSSの代替品がある** — VerifyWiseがISO 42001対応のオープンソースプラットフォームを提供。PASTA（学術フレームワーク）も多規制自動評価を実現。

5. **特許性はグレー** — SHA-256/Merkle Treeの監査証跡は先行研究（AuditableLLM、Codebat Technologies）が存在。マルチ規制クロスマッピングはRelyance AI、OneTrust、PASTAが類似機能を提供。完全に新規とは言い難い。

---

## 1. 競合製品の徹底調査

### 1.1 グローバルAIガバナンス専業SaaS

| 製品 | URL | 推定価格 | 対象市場 | 日本対応 | JPGovAIとの比較 |
|------|-----|---------|---------|---------|----------------|
| **Credo AI** | https://www.credo.ai/ | 非公開（エンタープライズ） | グローバル | なし | AI監視・バイアス検出に強い。日本規制対応なし。ガバナンスポリシーの自動適用に特化 |
| **Holistic AI** | https://www.holisticai.com/ | 非公開 | グローバル | なし | EU AI Act、NIST RMF、ISO 42001対応。日本規制は非対応。継続監視に強み |
| **FairNow** | https://fairnow.ai/ | 非公開 | グローバル | なし | ISO 42001対応あり。25+の法規制フレームワーク対応。監査人ネットワーク。日本規制は非対応 |
| **Relyance AI** | https://www.relyance.ai/ | 平均契約額 約$105,240/年 | グローバル | なし | シャドーAI検出、データフロー追跡。マルチ規制マッピングあり。日本規制は非対応 |
| **Saidot** | https://www.saidot.ai/ | 非公開 | 欧州中心 | なし | EU AI Act特化。Azure AI Foundry連携。Microsoft Marketplace掲載 |
| **AICompliant** | https://aicompliant.ai/ | 非公開 | グローバル | なし | 規制マッピング自動提案、タスク自動生成 |

### 1.2 汎用GRC→AIガバナンス拡張

| 製品 | URL | 推定価格 | JPGovAIとの比較 |
|------|-----|---------|----------------|
| **OneTrust** | https://www.onetrust.com/ | $10,000-$50,000+/年 | 2026年3月にリアルタイムAIガバナンス・エージェント監視機能を追加。最大の脅威。ただし日本規制特化ではない |
| **Vanta** | https://www.vanta.com/ | $7,500-$100,000/年 | EU AI Act対応済み。AIエージェントによる自動証拠収集。日本規制は非対応だが拡張性あり |
| **Drata** | https://drata.com/ | $7,500-$100,000+/年 | AI Compliance Tools一覧を公開。SOC2/ISO27001中心だがAIガバナンスに拡張中 |
| **Sprinto** | https://sprinto.com/ | $4,000+/年 | AIコンプライアンス5社比較記事を公開。自動監視・証拠収集 |

### 1.3 日本国内プレイヤー

| プレイヤー | 種別 | 内容 | JPGovAIとの比較 |
|-----------|------|------|----------------|
| **PwC Japan** | コンサル | ISO 42001認証取得支援、AIガバナンス構築支援（7テーマ）、大阪市アセスメント実施 | 最大の競合。ただしコンサル（500万〜3000万円）で、SaaS製品なし |
| **EY Japan** | コンサル | AI利用ガバナンス + AI開発・運用ガバナンスの2軸支援 | コンサルのみ |
| **KPMG Japan** | コンサル | 2026年3月「AIエージェント管理態勢構築支援サービス」本格展開。「KPMG Trusted AI」フレームワーク | コンサルのみ。タイミング的に最新 |
| **デロイト** | コンサル | AIガバナンス解説・コラム中心 | コンサルのみ |
| **NEC** | コンサル+製品 | AIガバナンスサービス3種（2025年12月〜）。Cisco AI Defenseとの連携。「AIディスカバリープログラム＋」（6観点診断） | **最も直接的な競合**。SaaS的な要素あり。ただし大企業向け |
| **NRI / NRIセキュア** | コンサル | 「AIリスクガバナンス構築支援サービス」。10要素フレームワーク | コンサルのみ |
| **AIガバナンス協会（AIGA）** | 業界団体 | 「AIガバナンスナビ」（自己診断ツール）。Excelベースの成熟度チェッカー。100社超参加 | **重要な先行事例**。機能は限定的（Excel）だが、コンセプトがJPGovAIの25問診断と類似 |
| **IBM Watson x.governance** | プラットフォーム | 36種類のバイアス検出指標。モデル登録〜説明可能性レポート自動化 | グローバル製品の日本展開。AIガバナンス「管理」より「技術的モニタリング」寄り |
| **Google Cloud Vertex AI** | プラットフォーム | Model Monitoring + AI Explanations。2025年版でEU AI Actテンプレート追加 | 技術プラットフォーム。規制対応ツールではない |

### 1.4 致命的発見: AIガバナンス協会のAIガバナンスナビ

**これはJPGovAIにとって最も警戒すべき存在。**

- 100社超の企業が参加する業界団体が運営
- 自己診断ツール（成熟度チェッカー）を提供
- AI事業者ガイドラインに基づく「AIガバナンス・アクション目標」への準拠度を測定
- 無料で会員企業に提供
- **ただしExcelベースで、SaaS製品ではない**
- ISO 42001やAI推進法のクロスマッピングは未実装

**JPGovAIとの差別化ポイント**: SaaS、クロスマッピング、AI改善提案、暗号学的監査証跡。ただし「25問で成熟度診断」というコンセプトの先行事例としてAIGAのナビが存在する事実は、特許性に影響する可能性がある。

### 1.5 AIガバナンス認証制度の動向

- **AIガバナンス協会**: 「AIガバナンス認証制度に関するディスカッションペーパー ver 1.0」を2024年6月に公表。第三者認証制度の枠組みを検討中
- **ISMS-AC（JIPDEC系列）**: ISO/IEC 42001に基づく認証の認定を開始。2026年1月にSGSジャパンとテュフラインランドジャパンを認定
- **「AIガバナンスマーク」**: **現時点では正式には存在しない**。AIガバナンス協会が認証制度を検討中だが、Pマーク的な「マーク制度」は未確立

**JPGovAIへの示唆**: 認証制度が立ち上がれば、その準備ツールとしての需要が生まれる。ただし制度自体が未確立であり、いつ実現するか不透明。

---

## 2. OSSで同等のものが存在しないか

### 2.1 直接的な代替OSS

| プロジェクト | GitHub Stars | 内容 | JPGovAIとの重複度 |
|-------------|-------------|------|------------------|
| **[VerifyWise](https://github.com/bluewave-labs/verifywise)** | 不明（活発） | EU AI Act、ISO 42001、NIST AI RMF対応のフルAIガバナンスプラットフォーム。BSL 1.1ライセンス | **高い**。ダッシュボード、リスク管理、ポリシー管理、監査証跡。日本規制は未対応 |
| **[AI Governance Framework Tools](https://github.com/BinaryVerseAI/ai-governance-framework-tools)** | 低 | NIST AI RMF → ISO 42001のギャップ分析Excelシート | 低〜中。クロスマッピングの先行実装（Excelレベル） |
| **[Unworldly](https://github.com/DilawarShafiq/unworldly)** | 低 | AIエージェントのフライトレコーダー。ISO 42001+HIPAA準拠の監査証跡 | 中。暗号学的監査証跡（tamper-proof）がJPGovAIと類似 |
| **[ISO 42001 Lead Implementer Toolkit](https://github.com/icdfa/iso-42001-lead-implementer-toolkit)** | 低 | テンプレート・ガイド・ケーススタディ集 | 低。テンプレート集であり、自動化ツールではない |
| **[42001-agentic](https://github.com/eljaunis/42001-agentic)** | 低 | ISO 42001のマッピング構造（エージェント的アプローチ） | 中。マッピング手法の先行研究 |
| **[CISO Assistant](https://github.com/intuitem/ciso-assistant-community)** | 高（GRCツール） | 汎用GRCプラットフォーム。ISO 42001サポートがissueとして提起されている | 中。将来的にISO 42001対応の可能性 |

### 2.2 大手OSS責任AI ツールキット

| ツールキット | 日本規制対応 | JPGovAIとの比較 |
|-------------|-----------|----------------|
| **IBM AI Fairness 360** | なし | バイアス検出に特化（70+指標）。ガバナンス管理ツールではない |
| **Google Model Cards** | なし | 透明性ドキュメントのフレームワーク。コンプライアンスツールではない |
| **Microsoft Responsible AI Toolkit** | なし（Microsoftは日本でAIガバナンスの5点提言を発表したが、ツールは日本規制非対応） | Purview等の汎用ツール。AI事業者ガイドライン特化ではない |
| **IBM watsonx.governance** | 部分的 | ISO 42001認証を取得（Granite models）。ただし規制コンプライアンス管理というよりMLOps/モデル管理寄り |

### 2.3 学術フレームワーク

| フレームワーク | 内容 | JPGovAIとの関係 |
|-------------|------|----------------|
| **[PASTA](https://arxiv.org/abs/2601.11702)** | 多規制AI準拠評価の自動化フレームワーク（2026年1月公開）。5政策を2分未満・約$3で評価。LLM駆動のペアワイズ評価。モデルカードベース | **重要な先行研究**。マルチ規制クロスマッピング＋LLM自動評価のコンセプトが類似。ただし学術研究であり、製品ではない |

### 残酷な真実

**VerifyWiseは無視できない脅威**。日本規制は未対応だが、オープンソースでISO 42001対応プラットフォームを提供している。もし誰かがVerifyWiseに日本規制モジュールを追加すれば、JPGovAIの存在意義が問われる。

**PASTAフレームワーク**は、JPGovAIの「マルチ規制自動評価 + LLM改善提案」というコアコンセプトの先行研究として、特許審査で引用される可能性がある。

---

## 3. 先行特許調査

### 3.1 関連特許

| 特許番号 | 出願者 | 内容 | JPGovAIへの影響 |
|---------|--------|------|----------------|
| **US11386296B2** | IBM | AIガバナンス・保証オペレーション。AI整合性・透明性管理 | AIガバナンスシステムの広範な特許。JPGovAIの基本概念と重複リスク |
| **US20240202351A1** | 不明 | 「責任あるAIのためのシステムと方法」。バイアス検出API、ガバナンスポリシー自動適用 | ガバナンスポリシー自動適用の先行技術 |
| **US20250165650A1** | 不明 | 「AIガバナンスを実行するシステムと方法」。SaaS展開。データプライバシー・漏洩防止 | **最も直接的な先行技術**。AIガバナンスをSaaSで提供するシステムの特許出願 |
| **WO2021084510A1** | IBM | AI環境でのエージェント実行。モデル構築・ガバナンス・ビジネスプロセス最適化 | エンドツーエンドAIガバナンスプラットフォームの先行技術 |

### 3.2 暗号学的監査証跡の先行技術

| 先行技術 | 内容 | JPGovAIへの影響 |
|---------|------|----------------|
| **AuditableLLM** (Electronics, 2025) | SHA-256ハッシュチェーンによる改竄防止監査証跡。LLM操作の監査フレームワーク | **直接的な先行技術**。「SHA-256ハッシュチェーン + AI操作の監査」の組み合わせが公開済み |
| **Codebat Technologies Inc.** | 規制AIワークフローの暗号学的証拠構造。Merkle-tree anchoring。特許出願中（ポスト量子対応版も） | **直接的な先行技術**。「Merkle Tree + 規制AIワークフロー」の特許出願が既に存在 |
| **US20170075938A1** | Time-Centric Merkle Hash Tree | 時間ベースのMerkle Hash Treeによるデータ検証 | Merkle Tree監査証跡の汎用先行技術 |

### 3.3 特許性の評価（残酷な正直さで）

#### 「マルチ規制クロスマッピングの自動化」

- **新規性**: **低〜中**。Relyance AIは「Dynamic Regulatory Mapping」を製品機能として提供。OneTrustも複数フレームワーク対応。PASTAは学術論文として公開。BinaryVerseAIはNIST→ISO 42001のギャップ分析をGitHubで公開。
- **日本規制特化**: AI事業者ガイドライン × ISO 42001 × AI推進法の3規制クロスマッピングは、現時点で他に実装例が確認されていない。ただし「日本規制に特化」しただけで特許が成立するかは疑問。

#### 「SHA-256ハッシュチェーン + Merkle Tree監査証跡（AIガバナンス用）」

- **新規性**: **低**。AuditableLLMが2025年にSHA-256ハッシュチェーンによるAI監査フレームワークを学術発表。Codebat Technologiesが「規制AIワークフローの暗号学的証拠構造」で特許出願中。Unworldly（GitHub OSS）がISO 42001準拠の改竄防止監査証跡を実装。
- **判定**: この組み合わせは先行技術が豊富で、特許化は困難。

#### 「25問のAI成熟度アセスメント」

- **新規性**: **低**。AIガバナンス協会のAIガバナンスナビが類似の自己診断ツールを提供。MITRE AI Maturity Modelが体系的な成熟度評価ツールを公開。質問数が25問であること自体に技術的な発明性はない。

#### 「LLMによるコンテキスト対応改善提案生成」

- **新規性**: **中**。組織プロファイル（業種・規模・AI利用パターン）に基づいてLLMが具体的な改善アクションを生成するアプローチは、PASTA等の学術研究にも見られるが、日本規制に特化した実装は確認されていない。ただしこれは「LLMの応用」であり、特許審査でアリスv.CLS Bank判決（抽象的アイデアの排除）に引っかかるリスクがある。

#### 総合判定

**特許取得の可能性: 20-35%**

最も特許性が高いのは、個々の要素ではなく「組み合わせ」の新規性:
- 組織プロファイルに基づく動的要件重み付け
- 日本3規制のクロスマッピングエンジン
- LLMコンテキスト対応改善提案
- 暗号学的監査証跡

ただし、各要素の先行技術が豊富であるため、「組み合わせの自明性」で拒絶される可能性が高い。

---

## 4. 市場の実在確認

### 4.1 ISO 42001認証の日本での実態

- **Godot社**: 2025年4月、日本初のISO 42001認証取得
- **国際協力データサービス**: 2026年1月、SGSジャパンのISMS-AC認定後初の認証
- **認証機関の認定**: SGSジャパン、テュフラインランドジャパンが2026年1月に認定開始
- **認証取得企業数**: **極めて少ない**。確認できたのは2社のみ（2026年3月時点）

**評価**: ISO 42001認証取得ブームは「まだ来ていない」。認証機関の認定が2026年1月に始まったばかりであり、本格的な需要はこれから。

### 4.2 AI推進法への企業対応

- 2025年6月施行だが、**罰則規定なし**。「努力義務」ベース
- 企業の反応: 「対応しなければならない」という切迫感は低い
- コンサルファームは積極的にサービス展開しているが、「法律対応」より「ガバナンス強化」の文脈

**評価**: AI推進法の罰則なし設計は、JPGovAIの「急務感」マーケティングを弱める。

### 4.3 企業の投資実態

- **AI関連予算**: 35%の企業が拡大予定、縮小はわずか1.1%
- **政府投資**: 2026年度から5年間で1兆円超（ただしインフラ・研究開発中心）
- **AIガバナンス市場（日本）**: 2030年に推定US$84.5M（約125億円）、CAGR 39.1%
- **現在の市場規模**: 推定US$10-20M程度（2025-2026年）

### 4.4 金融庁の動向（ポジティブシグナル）

- 2025年3月: AIディスカッションペーパー第1.0版公表
- 2026年3月: 第1.1版公表。金融機関のAIガバナンス・リスク管理の具体化
- 9割以上の金融機関がAIを利用中
- 金融庁がセーフハーバー提供を検討

**評価**: 金融セクターはAIガバナンスの最有望市場。規制圧力が最も強い。

### 4.5 残酷な問い: これは「解決策が問題を探している」状況か？

**答え: 半分イエス、半分ノー**

**イエスの根拠:**
- AI推進法に罰則なし → 法的強制力による需要創出が弱い
- ISO 42001認証取得企業は日本で2社のみ → 大量需要はまだない
- コンサルファームのサービスは「存在する」が、爆発的に売れている証拠なし
- AIガバナンスナビが無料で提供されている → 有料SaaSへの支払い意欲が未証明

**ノーの根拠:**
- AIガバナンス市場のCAGRは39.1%（日本） → 成長率は非常に高い
- 金融庁がディスカッションペーパーを継続更新 → セクター規制の強化傾向
- 100社超がAIガバナンス協会に参加 → 関心は確実にある
- EU AI Actの影響で、グローバル企業の日本法人に対応ニーズ
- ISMS-ACがISO 42001認定を開始 → 制度インフラが整い始めた

**結論: 市場は「3年早い」可能性がある。** 2026年時点では需要が限定的だが、2027-2028年にかけてISO 42001認証取得の流れ、金融庁規制の具体化、AIガバナンス認証制度の立ち上がりで需要が本格化する可能性がある。

---

## 5. JPGovAIの競争力評価

### 5.1 強み

1. **日本規制特化は正しいポジショニング** — グローバル競合が日本のAI事業者ガイドラインやAI推進法に対応する優先度は低い
2. **コンサル vs SaaSの価格差** — 年間30-72万円 vs 500-3000万円は明確な価値提案
3. **3規制クロスマッピング** — AI事業者ガイドライン × ISO 42001 × AI推進法の一元管理は確認できた範囲では他に実装なし
4. **タイミング** — ISO 42001認定機関の認定開始（2026年1月）の直後であり、市場形成の初期に参入

### 5.2 弱み（残酷に）

1. **市場規模が不確実** — 月額29,800円を払う中小企業がどれだけあるかが未検証
2. **コンサルの代替にはならない** — ISO 42001認証取得には結局コンサルが必要。ツールだけでは認証は取れない
3. **AIガバナンスナビとの差別化** — 無料の自己診断ツールが既にある。「なぜ有料版が必要か」の説明が必要
4. **VerifyWise（OSS）の脅威** — 日本規制モジュールが追加されれば、無料の代替品になる
5. **大手参入リスク** — NEC（Cisco連携）が2025年12月にサービス開始。PwCがISO 42001認証取得支援を本格化。大手が本気でSaaS化したら勝ち目が薄い
6. **AI推進法に罰則なし** — GDPR/EU AI Actのような「対応しないと罰金」の緊急性がない
7. **技術スタック** — SQLite + Streamlit は本番環境として脆弱。エンタープライズ顧客の信頼を得るには不十分

### 5.3 機会

1. **金融セクター特化** — 金融庁のディスカッションペーパーに基づく業界特化版
2. **ISO 42001認証準備ツール** — 認定機関（SGS、テュフラインランド）との連携
3. **AIガバナンス協会との連携** — 会員企業100社超へのアクセス
4. **EU AI Act対応の追加** — 日本法人のグローバル対応需要

### 5.4 脅威

1. **OneTrustの日本市場参入** — 2026年3月にリアルタイムAIガバナンス機能を追加。日本語対応すれば最大の脅威
2. **VantaのEU AI Act対応** — AI規制対応の自動化に本格参入。日本規制への拡張リスク
3. **大手コンサルのSaaS化** — PwC、NEC、KPMGがツール化を進めれば、ブランド力で圧勝される
4. **制度の遅延** — AIガバナンス認証制度が立ち上がらなければ、市場成長が鈍化

---

## 6. 戦略的提言

### 6.1 短期（0-6ヶ月）

- **無料診断を顧客獲得の入り口として最大限活用** — AIガバナンスナビとの差別化を明確にする（Excelの静的診断 vs クラウドベースのAI動的提案）
- **金融セクターに集中** — 金融庁ディスカッションペーパーへの対応を売りにする
- **技術スタックの強化** — SQLite → PostgreSQL、Streamlit → Next.js等。エンタープライズ対応

### 6.2 中期（6-18ヶ月）

- **ISO 42001認証機関との連携** — SGSジャパン、テュフラインランドとのパートナーシップ
- **AIガバナンス協会への加入** — ナビとの補完関係を構築
- **EU AI Act対応追加** — クロスマッピングを4規制に拡大

### 6.3 長期（18-36ヶ月）

- **AIガバナンス認証制度の準備ツール** — 制度立ち上げと同時にポジショニング
- **APIプラットフォーム化** — 他ツールへのガバナンスエンジン提供

### 6.4 特許戦略の修正

特許取得が困難な場合、以下の代替戦略を検討:
1. **スピードで勝つ** — 特許より先行者利益。日本市場でのブランド確立を優先
2. **ノウハウの蓄積** — 日本3規制のクロスマッピングテーブル自体が知的資産。特許ではなく営業秘密として保護
3. **特許出願は維持** — 防御的に仮出願は行い、先行技術に対するclaim narrowingで可能な範囲の権利化を目指す

---

## Sources

### 競合・市場
- [PwC Japan AIガバナンス](https://www.pwc.com/jp/ja/services/consulting/analytics/responsible-ai.html)
- [EY Japan AIガバナンス態勢構築支援](https://www.ey.com/ja_jp/services/consulting/ai-governance-services)
- [KPMG Japan AIエージェント管理態勢構築支援](https://kpmg.com/jp/ja/media/press-releases/2026/03/aiagent-governance.html)
- [NEC AIガバナンスサービス](https://jpn.nec.com/press/202512/20251202_02.html)
- [NRIセキュア AIリスクガバナンス構築支援](https://www.nri-secure.co.jp/service/consulting/ai-risk-governance)
- [AIガバナンス協会 AI Governance Navi](https://www.ai-governance.jp/ai-governance-navi)
- [AIガバナンス協会 認証制度DP](https://www.ai-governance.jp/ai-governance-certificate-system)
- [Credo AI](https://www.credo.ai/)
- [Holistic AI](https://www.holisticai.com/)
- [FairNow ISO 42001](https://fairnow.ai/platform/iso-42001-ai-compliance-software/)
- [OneTrust AI Governance](https://www.onetrust.com/solutions/ai-governance/)
- [OneTrust 2026 AI Governance拡張](https://siliconangle.com/2026/03/09/onetrust-expands-platform-real-time-ai-governance-agent-oversight-capabilities/)
- [Vanta EU AI Act](https://www.vanta.com/products/eu-ai-act)
- [Vanta Agentic Trust Platform](https://www.businesswire.com/news/home/20260319211415/en/Vantas-New-Agents-and-Enterprise-Controls-Eliminate-Audit-Chaos)
- [Relyance AI](https://www.relyance.ai/solutions/ai-regulatory-mapping-compliance-automation)
- [Saidot](https://www.saidot.ai/pricing)
- [AICompliant](https://aicompliant.ai/)
- [Splunk Best AI Governance Platforms 2026](https://www.splunk.com/en_us/blog/learn/ai-governance-platforms.html)
- [AI governance market CAGR 45.3%](https://www.marketsandmarkets.com/Market-Reports/ai-governance-market-176187291.html)

### OSS
- [VerifyWise](https://github.com/bluewave-labs/verifywise)
- [AI Governance Framework Tools](https://github.com/BinaryVerseAI/ai-governance-framework-tools)
- [Unworldly](https://github.com/DilawarShafiq/unworldly)
- [ISO 42001 Lead Implementer Toolkit](https://github.com/icdfa/iso-42001-lead-implementer-toolkit)
- [IBM AI Fairness 360](https://aif360.res.ibm.com/)
- [Google Model Cards](https://modelcards.withgoogle.com/)

### 特許・先行技術
- [US11386296B2 - IBM AI Governance](https://patents.google.com/patent/US11386296B2/en)
- [US20240202351A1 - Responsible AI](https://patents.google.com/patent/US20240202351A1/en)
- [US20250165650A1 - AI Governance System](https://patents.google.com/patent/US20250165650A1)
- [AuditableLLM (SHA-256 hash chain)](https://www.mdpi.com/2079-9292/15/1/56)
- [Codebat Technologies - Cryptographic Evidence](https://arxiv.org/abs/2511.17118)
- [PASTA Framework](https://arxiv.org/abs/2601.11702)

### 市場・規制
- [Japan AI Governance Market 2030](https://www.grandviewresearch.com/horizon/outlook/ai-governance-market/japan)
- [AI事業者ガイドライン v1.1](https://www.soumu.go.jp/main_content/001002576.pdf)
- [AI推進法 解説](https://fpf.org/blog/understanding-japans-ai-promotion-act-an-innovation-first-blueprint-for-ai-regulation/)
- [金融庁 AIディスカッションペーパー v1.1](https://www.fsa.go.jp/news/r7/sonota/20260303/aidp_version1.1.pdf)
- [SGSジャパン ISO 42001初認証](https://www.sgs.com/ja-jp/news/2025/04/sgs-issues-its-first-ever-iso-iec-42001-certification-in-japan)
- [ISMS-AC AIMS認定開始](https://isms.jp/topics/news/20250131.html)
- [JIPDEC AIMS認定](https://www.jipdec.or.jp/news/pressrelease/20260114.html)
- [Godot ISO 42001認証取得](https://prtimes.jp/main/html/rd/p/000000037.000106742.html)
- [人工知能基本計画](https://www8.cao.go.jp/cstp/ai/ai_plan/aiplan_20251223.pdf)
- [WEF Japan responsible AI](https://www.weforum.org/stories/2026/01/japan-path-to-responsible-ai-and-what-it-can-teach-us/)
- [AIガバナンス支援企業10種](https://www.aidma-hd.jp/ai/ai_governance_company/)
