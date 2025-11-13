## 1. リポジトリ構造の作成
- [ ] packages/playlog-core, playlog-cli, playlog-gui と assets/dist/scripts ディレクトリを作成する
- [ ] 各パッケージに最小限の __init__ や src ファイル、Python/Node 設定ファイル（pyproject.toml, package.json など）を配置する

## 2. ツールチェーン設定
- [ ] ruff, mypy, pytest, coverage 設定を追加し、Python パッケージの依存を定義する
- [ ] ESLint, Prettier, Vite/Electron の初期設定と npm scripts を用意する

## 3. CI / ドキュメント
- [ ] GitHub Actions で Ubuntu/macOS/Windows + Python3.12/Node20 の lint/test マトリクスを構築する
- [ ] README にバッジ、開発者セットアップ手順、CI 概要を追記する
