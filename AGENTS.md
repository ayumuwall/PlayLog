<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

> **OpenSpec優先**: 本ドキュメントは OpenSpec 導入前に作成されたため、内容が矛盾する場合は **OpenSpec ワークフロー（`openspec/AGENTS.md`）を常に優先**してください。

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

When drafting a new proposal:
- `proposal.md` **must** include both `## Why` and `## What Changes` sections before sharing or archiving the change.
- Proposal change-id（例: `add-foo-bar`）には、AGENTS.md ロードマップの該当タスク番号をサフィックス（`-task3` 等）として必ず付与し、どの段階の実装か分かるようにする。

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# AGENTS.md — PlayLog

本ドキュメントは、OpenAI Codex（CLI / IDE拡張）を前提に、以下仕様のアプリを**段階的に自動生成・実装・テスト・パッケージング**させるための指示書です。

- **対象OS**: macOS / Windows（Intel/Apple Silicon/AMD64）
- **対象DJソフト**: Algoriddim **djay**、AlphaTheta **rekordbox** **v5 / v6 / v7**、**Serato DJ Pro / Lite**
- **要件**:
  - 再生履歴（History / Set）を**読み取り専用**で抽出
  - **TXT / CSV / JSON**を選択可能
  - **1晩（ナイトセッション）= 1ファイル**で保存
  - **ファイル名に日付（night日）とDJソフト名**を含める
  - **簡易GUI**（Electron）で配布（CLIも併用可）
  - **プライバシー配慮**: 全処理はローカル。外部送信なし。

---

## 0. リポジトリ構成（初期化）
```
repo/
  packages/
    playlog-core/         # 抽出コア（Python）
      playlog/            # Python package (schema, extractors, writers)
      tests/
    playlog-cli/          # CLI（Python, playlog-coreに依存）
    playlog-gui/          # GUI（Electron：React + TypeScript）
      src/
      build/
      scripts/
  assets/
    fixtures/             # サンプル .plist / rekordbox.xml / ダミーDB / Serato crate
  dist/                   # 配布成果物
  scripts/
    make_fixtures.py
    verify_env.py
  README.md
  AGENTS.md              # 本書
  LICENSE
```

> **方針**: コア抽出は Python（互換性・ライブラリ豊富・pyrekordbox利用）で実装し、GUIは Electron から **バンドル済みPythonバイナリ**（PyInstaller）を叩く。CLI と GUI の両輪により、自動テストと配布を簡易化。

---

## 1. 抽出対象とデータモデル

### 1.1 PlayEvent（共通スキーマ）
`playlog-core` では、すべての入力を下記スキーマに正規化します。

```json
{
  "app": "djay | rekordbox | serato",
  "app_version": "string | null",
  "session_id": "string | null",          // セット名やHISTORY名
  "session_date": "YYYY-MM-DD | null",   // セッション推定日
  "played_at": "ISO-8601 | null",        // トラック個別の開始時刻（得られる場合）
  "title": "string",
  "artist": "string",
  "album": "string",
  "duration_sec": 0,
  "deck": "A/B/... | null",
  "bpm": "number | null",
  "key": "string | null",
  "source_path": "string | null",         // ローカルファイルパス等
  "source_track_id": "string | null",     // rekordbox内部IDなど
  "raw": { /* 生データ断片（任意）*/ }
}
```

### 1.2 djay
- 既定ディレクトリから **Sets** フォルダ配下の `.plist` を走査
- 各plist内のトラック配列をヒューリスティックに抽出
- セッション日付はファイル名／メタから推定

### 1.3 rekordbox v5/6/7
- **モード=auto**: まず `pyrekordbox` によるDB読み取りを試行（v6/v7のSQLCipher復号含む）。失敗時は **XML**（ユーザー指定 `rekordbox.xml`）へフォールバック
- v5では平文SQLiteも存在。`pyrekordbox` がバージョン差を吸収。得られないメタは空欄
- HISTORY系のプレイリスト名から `session_id`、日付を推定

### 1.4 Serato DJ Pro / Lite
- **ライブラリ位置**（自動検出）:
  - macOS: `~/Music/_Serato_`
  - Windows: `C:\Users\<username>\Music\_Serato_`
- **取得モード**（`--serato-mode auto|crate|logs`）:
  1) **crate**（既定優先）: `_Serato_` 内の **History / crate** 形式を直接解析し、再生順・メタを抽出。
  2) **logs**: `_Serato_/Logs` のセッションログから補助情報を抽出（診断用のため項目は限定・欠損があり得る）。
- **時刻情報**: crate 直解析では**曲ごとの絶対時刻が存在しないライブラリ構成もある**ため、取得できれば `played_at` として出力、無い場合は未設定。`--timeline-estimate` で推定の付加が可能（推定値）。
- crate/history の `*.crate` ファイルは **4バイトタグ + 4バイト長 + データ**の繰り返しで構成され、`otrk` チャンク配下からタイトル/アーティスト/BPM/Deck などを抽出する。取得できた断片は `PlayEvent.raw` に格納し、欠損は `None` として扱う。
- `_Serato_/Logs/*.log` は `Session Start @ ...` 行や `HH:MM:SS<TAB>Deck 1<TAB>Artist - Title` の並びを best-effort で解析し、ミッドナイト跨ぎは `PlayEvent.played_at` の昇順で補正する。ログに absolute 時刻が無い場合でも、開始日時はファイル名や mtime から推定する。
- Serato セッションの night 日付は `floor_by_cutoff`（既定 08:00）で求める。`--timeline-estimate` が有効でかつ crate に時刻が存在しない場合は、セッションアンカーをファイル名／更新日時から 22:00 とみなし、曲長を積算して推定 `played_at` を生成し `timeline_mode=estimated` を付与する。

### 1.5 セッション化（ナイト単位）
**目的**: 「1晩=1ファイル」を正しく切り出す。

- **ナイト境界（cutoff）**: 既定は **08:00**（ローカルタイムゾーン）。**その日08:00までは前日として扱う**。`cutoff` 以降の時刻は**当日のナイト**。
  - 例: 2025-11-12 23:00〜翌 02:30 は **2025-11-12 のナイト**。
  - 例: 2025-11-13 07:40 は **2025-11-12 のナイト**（cutoff=08:00の場合）。
- **セッション候補の抽出**:
  1) **djay**: 各 `.plist`（DJ Set）を1セッション候補として扱う。内部にトラックの開始/終了があれば使用。
  2) **rekordbox**: HISTORY系プレイリスト（`HISTORY yyyy-mm-dd` 等）を1セッション候補とし、曲ごとの再生時刻が取得できれば利用。
  3) **serato**: crate/history のまとまりを候補とし、時刻があれば採用、無ければ推定や手動編集で補完。
- **ミッドナイト跨ぎ**: セッション候補内の最小 `played_at` をアンカーにしてナイト日を決定。タイムスタンプが無い場合は、
  - djay: ファイル名日時、`plist`ヘッダ、`mtime` を優先順位で利用。
  - rekordbox: プレイリスト名の日付、作成時刻、`master.db` の補助情報。
  - serato: crate ファイルの更新日時やログのヒント。
- **連続演奏の分割**（任意）: トラック間の無音/間隔が **`session_gap` 分以上（既定 60 分）**空いた場合、新しいセッションとして分割。
- **タイムゾーン**: 既定はOSのローカル。`--tz Asia/Tokyo` などで上書き可能。
- **推定タイムライン（任意）**: `--timeline-estimate` 有効時は、セッション開始（自動推定 or `--set-start`）＋曲長/クロスフェードから概算 `played_at` を付与（推定である旨をヘッダに明記）。

---

## 2. 出力仕様

### 2.0 既定の出力先
- **デスクトップ/`PlayLog Archives`**（macOS/Windows 共通）。
- 実装メモ: Windows は **Known Folder API（FOLDERID_Desktop）**で取得、macOSは `~/Desktop`。フォルダが無ければ作成。権限エラー時はホーム直下にフォールバック。

### 2.1 出力形式
- **JSON**: **1晩=1ファイル**（トップレベルに `session` メタ、`events` 配列に `PlayEvent[]`）。
- **CSV**: **1晩=1ファイル**（その晩の全曲を1行ずつ）。オプションで**全セッション統合CSV**（追記/再生成）も作成可能。
- **TXT**: **1晩=1ファイル**。ヘッダにセッション情報、続けて曲リストをレンダリング。

### 2.2 ファイル命名規約
- **ナイト日**: `night_date = floor_by_cutoff(min(played_at))`。時刻が無い場合は候補の推定時刻/ファイル名/mtimeを使用。
- **形式**: `YYYYMMDD_{app}_NIGHT_{session-id-or-venue}`
  - 例: `20251112_rekordbox_NIGHT_HISTORY-2025-11-12.json`
- 文字列はOS互換のためサニタイズ（`/\:*?"<>|` 等の置換）。

### 2.3 ディレクトリ構成
```
{OUT}/                                   # 既定: Desktop/PlayLog Archives
  playlog-run.log                         # 全体ランのテキストログ（詳細）
  playlog-run.ndjson                      # 全体ランのNDJSONログ（機械可読）
  {app}/
    {YYYY-MM-DD(night)}/
      {session_id}/
        session.json      # 1晩=1ファイル（JSON）
        session.txt       # 1晩=1ファイル（TXT）
        session.csv       # 1晩の全曲（CSV）
        session.log       # その晩の詳細テキストログ
        session.ndjson    # その晩のNDJSONログ
```

### 2.4 TXTテンプレート
```
[PlayLog]
App: {app} ({app_version})
NightDate: {night_date}  (cutoff={cutoff} / tz={tz})
Session: {session_id}
Start: {session_start}  End: {session_end}
Tracks: {events_count}
Timeline: {timeline_mode}  # actual | estimated

--- Tracks ---
{index}. [{played_at}] {artist} - {title}  (Album: {album}, BPM: {bpm}, Key: {key}, DurationSec: {duration_sec})
...
```

---

## 3. GUI（Electron）

### 3.1 画面フロー
1. **起動直後に自動スキャン（常に3ソフト）**: アプリ起動時に **djay / rekordbox / Serato を必ず全てスキャン**し、検出結果（見つかったアプリ・セッション候補件数・最終更新）を即時表示。**ウィザードは無し**。
   - **既定の出力先**: デスクトップ/`PlayLog Archives`（自動作成）。
   - 見つからないアプリは**静かにスキップ**し、検出ログだけ残す。
2. **クイックアーカイブ（ボタン一発）**: スキャン結果をそのまま用いて **「アーカイブ開始」** を押すだけで抽出→保存を実行。
3. **出力設定（任意）**: 別画面で、フォーマット（TXT/CSV/JSON）、**ナイト境界 `cutoff`（既定 08:00）**、**セッション分割 `session_gap`（既定 60分）**、**タイムゾーン**、**推定タイムライン ON/OFF**、上書きポリシー/統合CSV などを編集可能。
4. **セッション確認（任意）**: 推定されたナイト単位の一覧を表示し、**手動でマージ/スプリット**できるUI。
5. **実行**: 進捗バー、件数、エラー、ログ表示。
6. **結果**: エクスプローラで開く、統計（抽出数/失敗数）。

### 3.2 バックエンド連携
- 抽出コアは PyInstaller 同梱の `playlog` バイナリ。Main から spawn。
- 標準出力は **NDJSON進捗**（level, ts, component, event, details）を流し、RendererにIPC転送。
- **ログ永続化**: 実行開始時に `{OUT}/playlog-run.log / playlog-run.ndjson` をオープン。セッションごとに `{OUT}/{app}/{date}/{session}/session.log / session.ndjson` を併用。
- 例外/スタックトレースは `level=error` としてNDJSONに付与しつつ、テキストログにも整形出力。
- 既定の `log-level=debug` で最大限の情報を残す。設定で変更可。

### 3.3 配布
- `electron-builder` で macOS `.dmg` / Windows `.exe` / `.msi`
- 追加オプション: コードサイン、Auto-Update（任意）

---

## 4. CLI（併用）
```
# 既定設定（djay/rekordbox/seratoすべて を自動スキャン、出力先は Desktop/PlayLog Archives）
python -m playlog_cli run --tz Asia/Tokyo --formats json,txt,csv

# Serato の crate を優先し、_Serato_ ルートを明示＆タイムライン推定を有効化
python -m playlog_cli run --apps serato \
  --serato-mode auto \
  --serato-root "/Volumes/SSD/_Serato_" \
  --timeline-estimate \
  --formats json,txt \
  --tz Asia/Tokyo
```

> NOTE: `--night-cutoff` / `--session-gap` / `--per-night` などは CLI 側の次フェーズで実装予定。現行の `run` β版では Serato 向けの `--serato-mode` / `--serato-root` / `--timeline-estimate` を優先して実装している。

**主なフラグ**
- `--apps djay,rekordbox,serato`（**未指定時は all**）
- `--rb-mode auto|db|xml`, `--rb-xml <path>`
- `--serato-mode auto|crate|logs`, `--serato-root <path>`
- `--since <YYYY-MM-DD>` / `--until <YYYY-MM-DD>`
- `--formats json,txt,csv`
- `--per-night`（ナイト単位で1ファイル）
- `--night-cutoff HH:MM`（**既定 08:00**）
- `--session-gap <minutes>`（既定 60）
- `--tz <IANA TZ>`（例: Asia/Tokyo）
- `--timeline-estimate`（推定タイムライン出力を有効化）
- `--set-start "YYYY-MM-DD HH:MM"`（推定時のアンカー）
- `--log-level debug|info|warn|error`（**既定 debug**）
- `--log-format ndjson|text`（**既定 ndjson**、両方同時出力も可）
- `--no-global-log`（ラン全体ログを抑止、デフォルトは出力）
- `--redact-paths`（ログ上のフルパスをマスク）

---

## 5. 依存関係・バージョン
- Python 3.10+
- `pyrekordbox`（v5/6/7対応、SQLCipher自動）
- `sqlcipher3-wheels`（必要時）
- `plistlib`, `lxml` or `xml.etree.ElementTree`, `click`/`typer`, `pydantic`
- Electron 28+ / Node 20+, `electron-builder`

> 備考: SQLCipher のネイティブ依存は `pyrekordbox` と `sqlcipher3-wheels` の組み合わせで極力吸収。Windows/macOS 双方のCIでwheel解決を確認。

---

## 6. テスト戦略
- **ユニット**:
  - plist → PlayEvent 変換
  - rekordbox XML → PlayEvent 変換
  - DB経由（pyrekordbox）は**モック**＋小規模実DB（暗号化テストはスキップ可）
- **統合**:
  - `assets/fixtures` の実ファイルで end-to-end 抽出、出力ファイルと件数を検証
- **回帰**:
  - 既知のエッジケース（空Artist、特殊文字、長大タイトル、重複）
- **GUI**:
  - Playwright でレンダラーの基本導線、IPC 経路、エラー表示

---

## 7. セキュリティ & プライバシー
- 完全ローカル。ネットワークアクセスなし（GUI起動時に `--offline` を既定）
- 読み取り専用（元DB/ファイルは変更しない）
- ログに個人情報やフルパスを残さないオプション（`--redact-paths`）

---

## 8. 開発フロー（Codex前提）
> ここから先は **Codex CLI / IDE拡張** に渡す指示テンプレートです。各タスクは**独立的に完了可能**で、受け入れ条件を満たすPRを作成します。

### 共通プロンプト（先頭に付与）
```
あなたは熟練のソフトウェアエンジニア兼リリースエンジニアです。要件を満たし、堅牢で可読性の高いコードとテスト、ビルドスクリプトを作成します。
原則: セキュア / 冪等 / ログ明瞭 / エラーハンドリング徹底 / クロスプラットフォーム。
変更は最小のPR単位で。コミットメッセージは Conventional Commits に従うこと。
```

### タスク1: リポジトリ初期化
**目的**: 上記のディレクトリ構成でMonorepoを作成し、Python・Nodeのツールチェーンを設定。
- 成果物: `pyproject.toml`（core/cli）、`package.json`（gui）、`ruff`, `mypy`, `pytest`, `prettier`, `eslint`, `vite` 設定
- 受け入れ基準: CI（GitHub Actions）で `lint`, `test` が通る

**Codexへの指示**
```
repo直下に上記構成で空のパッケージを作り、基本設定を入れて。CIは Ubuntu-latest / macOS-latest / windows-latest の3OSで、Python3.12とNode20をマトリクス実行。READMEのバッジも付与。
```

### タスク2: スキーマ & Writer 実装
**目的**: `PlayEvent` のPydanticモデル、`Writer`抽象、`JsonWriter` / `TxtWriter` / `CsvBatchWriter` 実装
- 受け入れ基準: 単体テスト（fixtures→出力）合格。サニタイズ関数でOS予約文字を回避。

**Codexへの指示**
```
packages/playlog-core/playlog 以下に models.py, writers.py を作成。TXTテンプレはAGENTS.mdの仕様通り。CSVは“1晩=1ファイル”で書き出すCsvBatchWriterを実装。
```

### タスク3: djay 抽出器
**目的**: `.plist` 走査・解析・正規化
- 受け入れ基準: fixturesの複数plistで、期待件数のPlayEventが生成されること

**Codexへの指示**
```
packages/playlog-core/playlog/extractors/djay.py を実装。デフォルト探索パス候補をOS別に用意。Title/Artist/Album/Start/Endなど、キー名バリエーションに耐性を持たせる再帰抽出を実装。
```

### タスク4: rekordbox 抽出器（DB / XML / auto）
**目的**: `pyrekordbox` を優先し、失敗時は XML を使用
- 受け入れ基準: v5/6/7の想定fixturesで件数一致。DB不可環境でXMLにフォールバックすること。

**Codexへの指示**
```
packages/playlog-core/playlog/extractors/rekordbox.py を実装。mode=auto|db|xml。pyrekordboxからHistory相当のプレイリスト/セッションを辿り、PlayEventへ正規化。XMLは <NODE Type="1"> 配下のHISTORY系PLAYLISTを集計。
```

### タスク5: Serato 抽出器（crate / logs）
**目的**: `_Serato_` 内構造と Logs に対応（exportは対象外）
- 受け入れ基準: fixturesのcrateサンプルで件数一致。logsモードは最低限の補助情報出力。

**Codexへの指示**
```
packages/playlog-core/playlog/extractors/serato.py を実装。auto|crate|logs に対応。
- crate: Seratoのcrate/historyバイナリ形式（4バイトタグ+長さ+データ）を解析するパーサーを実装。
- logs: _Serato_/Logs のセッションログから取得できる範囲で補助情報を抽出（仕様非公開につき best-effort）。
```

### タスク6: CLI
**目的**: `playlog-cli` に Typer/Clickで `probe` / `run` を実装
- 受け入れ基準: `--help` が仕様通り、E2Eテスト合格、エラー時に適切なexit code

**Codexへの指示**
```
packages/playlog-cli にエントリポイントを作成。--apps, --rb-mode, --rb-xml, --serato-mode, --since/--until, --formats, --per-night, --out などを実装。標準出力は進捗をNDJSONで流す。
```

### タスク7: GUI（Electron）
**目的**: 起動時自動スキャン→クイックアーカイブ→進捗表示（ボタン一発）
- 受け入れ基準: macOS/Windowsでビルドでき、fixture抽出がGUIから成功

**Codexへの指示**
```
packages/playlog-gui を Vite + React + TS で生成。Mainプロセスから PyInstaller化した playlog バイナリを同梱し spawn。RendererはipcRendererでログ表示。設定はelectron-storeに保存。
```

### タスク8: パッケージング
**目的**: PyInstallerで `playlog` を各OS向けにビルドし、Electronに同梱。`electron-builder` で最終成果物を生成
- 受け入れ基準: dist/ に .dmg / .exe が生まれ、起動～抽出～保存が通る

**Codexへの指示**
```
PyInstaller specを作成し、不要ライブラリを除外。GitHub Actionsで3OSビルド。成果物をArtifactsに保存。electron-builderのnsis/dmg設定を追加。
```

### タスク9: QA / ドキュメント
**目的**: 既知の制約・FAQ・トラブルシューティング、利用手順を README に反映
- 受け入れ基準: バージョン差異、権限問題（Windowsのフォルダ権限等）、SQLCipher周りの注意が明記

**Codexへの指示**
```
READMEにGUI/CLIの使い方、対応バージョン、よくある質問を追加。スクリーンショットはモックでOK。
```

**README 記述ルール**
- 基本情報（冒頭説明・機能概要など）は DJ / ミュージシャンが読む前提で、技術リテラシーの低い読者でも理解しやすい平易な文章でまとめること。
- 「開発者向けの情報」セクションでは、現在の仕様に沿って要点のみを簡潔に整理し、冗長な説明や過度な詳細は避けること。

---

## 9. 受け入れ基準（総合）
- djay/rekordbox/serato の **いずれか**から、fixturesで **2晩以上**のナイトセッションを抽出できる
- **1晩=1ファイル**（TXT/JSON/CSV）が保存され、**ナイト境界のカットオフ（08:00既定）**が反映されている
- CSVは各晩の件数がTXT/JSONと一致し、（選択時）統合CSVも生成される
- GUIで「起動時自動スキャン→（必要なら設定）→アーカイブ開始→保存」まで通る
- macOS/Windowsの双方で実行可能（CIでSmokeテスト）

---

## 10. コーディング規約
- Python: `ruff`, `mypy(strict)`, `pytest`
- TypeScript: `eslint`, `prettier`, strictモード
- ログ: `structlog` もしくは最小実装のJSON logger
- 例外: 必ずユーザーに分かるメッセージ + 非0終了

---

## 11. リスク / 代替案
- SQLCipherのネイティブ依存解決に失敗 → **XMLフォールバック**で機能維持
- djayのplist構造差 → キー名ゆれに強いヒューリスティック + 生plist保管
- Serato crate で時刻欠損 → `--timeline-estimate` で概算、必要に応じて手動修正UI

---

## 12. ローカルでの動かし方（開発者）
```
# core & cli
pyenv local 3.12
pip install -e packages/playlog-core -e packages/playlog-cli
pytest -q

# gui（開発）
cd packages/playlog-gui
npm i
npm run dev
```

---

## 13. ライセンス
- MIT（サンプル）

---
