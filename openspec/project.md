# Project Context

## Language
- 既定出力は **日本語**。コメント/コミットメッセージ/PR説明や OpenSpec 生成物もすべて日本語で統一する。
- OpenSpec の構文キーワードのみ英語を維持（例：`### Requirement:`、`#### Scenario:`、`WHEN/THEN`、`MUST/SHALL`）。

## Purpose
DJ ソフト（djay / rekordbox / Serato）からセット履歴を読み取り、1晩=1ファイルで TXT/CSV/JSON を出力するクロスプラットフォームアプリ PlayLog を提供する。Python 製の抽出コア、Typer ベース CLI、Electron+React GUI を単一リポジトリで管理し、PyInstaller でバンドルしたコアを GUI から叩く構成で配布容易性と再現性を確保する。

## Tech Stack
- Python 3.10+（playlog-core, playlog-cli）
- Typer / Click, structlog, pydantic, pyrekordbox, sqlcipher3-wheels
- Node.js 20+ / Electron 28+ / React 18+ / TypeScript 5+（playlog-gui, Vite）
- PyInstaller, electron-builder, GitHub Actions（CI/CD）

## Project Conventions

### Code Style
- Python: PEP 8 + ruff/lint準拠、mypy(strict)必須、型ヒントを徹底。ログは構造化JSON（structlog相当）を優先。
- TypeScript/React: ESLint（strict), Prettier, JSXは関数コンポーネント。状態管理は React Query + hooks を基本とし、不要なクラス構文を避ける。
- CLIフラグやファイル名は kebab-case、Python内部の識別子は snake_case、TSは camelCase を既定とする。
- コメントは最小限で、推論が難しい処理や仕様依存部のみ日本語で補足する。

### Architecture Patterns
- モノレポ構造（packages/ 配下に core・cli・gui）。共通ロジックは playlog-core に集約し、CLI/GUI からコアを呼び出す。
- GUI は Electron Main から PyInstaller バンドル済み playlog 実行ファイルを spawn し、NDJSON ログを IPC 経由で Renderer に渡す。
- 抽出器は DJ ソフトごとに分割した Python モジュール（djay/rekordbox/serato）。PlayEvent Pydantic モデルで統一スキーマを提供し、Writer 抽象で TXT/CSV/JSON を切り替える。
- 出力ディレクトリ構造とログ（run log / session log）は core で一元管理し、GUI/CLI から同一コードパスを利用する。

### Testing Strategy
- ユニット: PlayEvent モデル、Writer、各抽出器のフォーマット変換を pytest でテスト。plist / XML / crate などの fixture を assets/fixtures で管理。
- 統合: CLI 経由で実行し、1晩=1ファイル出力・ナイト境界ロジックを検証。Serato など暗号化依存部はモック/サンプルDBで代替。
- GUI: Playwright or Spectron 相当でレンダラーの基本導線、自動スキャン、進捗表示をスモークテスト。IPC ログ経路も検証。
- CI は GitHub Actions（Ubuntu/macOS/Windows）で `ruff`, `mypy`, `pytest`, `npm run lint`, `npm run test` を並列実行する。

### Git Workflow
- main ブランチ保護。作業は feature/<topic> ブランチで実施し、PR は OpenSpec 承認後に作成。
- コミットメッセージは Conventional Commits（例: `feat(core): add writer factory`）。
- PR には OpenSpec change-id とリンクし、CI 緑化を必須条件とする。

## Domain Context
- DJ セット履歴はソフトごとにフォーマットが異なる（plist, rekordbox DB/XML, Serato crate/logs）。PlayLog はこれらを読み取り専用で解析し PlayEvent に正規化する。
- 「1晩=1ファイル」要件のため、夜間8:00カットオフや session_gap に基づきセッションを分割し、ナイト日をファイル名に含める。
- 出力は Desktop/PlayLog Archives 配下に JSON/TXT/CSV/ログを生成し、プライバシー保護のため外部送信は行わない。

## Important Constraints
- すべてローカル処理。ネットワークアクセス禁止（GUI も `--offline`）。
- 音源ライブラリへの書き込み禁止。抽出は読み取り専用で行い、エラー時も元データを変更しない。
- Windows/macOS 双方で動作し、Apple Silicon / Intel / AMD64 をサポート。
- SQLCipher 依存を吸収するため pyrekordbox + sqlcipher3-wheels を利用し、失敗時は XML フォールバックで機能維持。
- ログには個人情報やフルパスを残さない `--redact-paths` オプションを提供。

## External Dependencies
- pyrekordbox（rekordbox DB アクセス, SQLCipher解除含む）
- sqlcipher3-wheels（暗号化DB読み取り）
- plistlib, lxml, sqlite3 等の標準/外部ライブラリ
- Electron + electron-builder（GUI 配布）
- PyInstaller（Python コアの配布）
