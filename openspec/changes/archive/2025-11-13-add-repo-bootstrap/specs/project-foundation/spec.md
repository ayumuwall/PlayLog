## ADDED Requirements
### Requirement: Monorepo Bootstrap Structure
PlayLog リポジトリは Python コア・CLI・Electron GUI を含むモノレポ構造を維持し、指定ディレクトリ/設定ファイルを揃えてローカル開発を即時開始できる状態を **MUST** で保証する。

#### Scenario: Base layout scaffolding
WHEN 開発者がリポジトリを clone して `packages/` と `assets/` 以下を確認する
THEN `packages/playlog-core`, `packages/playlog-cli`, `packages/playlog-gui`, `assets/fixtures`, `dist`, `scripts` が空でも存在し README の構成図と一致していること
THEN 各 Python パッケージに `pyproject.toml`, `__init__.py`, テストディレクトリの雛形が含まれていること
THEN GUI パッケージに `package.json`, Vite/Electron の初期設定ファイル、npm scripts が含まれていること

### Requirement: Toolchain Configuration
Python/Node 双方の lint/test ツールチェーンを統一し、ruff/mypy/pytest と ESLint/Prettier/Vite が動作する設定を **SHALL** とする。

#### Scenario: Python lint/test ready
WHEN `pip install -e packages/playlog-core -e packages/playlog-cli` を実行する
THEN ruff・mypy・pytest 設定ファイルが存在し、それぞれ `ruff check`, `mypy`, `pytest` が成功する既定エントリを提供している

#### Scenario: Node lint/test ready
WHEN `cd packages/playlog-gui && npm install` を実行する
THEN `npm run lint` と `npm run test` が ESLint/Prettier/Vitest などの設定に基づいて動作し、TypeScript strict モードが有効になっている

### Requirement: Cross-Platform CI Pipeline
GitHub Actions で Ubuntu/macOS/Windows + Python3.12/Node20 の lint/test マトリクスを実行し、main/PR に対して自動検証を **MUST** で提供する。

#### Scenario: Matrix lint/test workflow
WHEN 開発者が PR を作成または main に push する
THEN CI が Python ステージで `ruff check`, `mypy`, `pytest` を実行し、Node ステージで `npm run lint`, `npm run test` を実行する
THEN すべての OS（ubuntu-latest, macos-latest, windows-latest）でジョブが成功しない限りマージできない状態である
