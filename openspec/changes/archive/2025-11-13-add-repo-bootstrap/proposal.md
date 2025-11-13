# Proposal: add-repo-bootstrap

## 背景
- PlayLog は Python 抽出コア、CLI、Electron GUI を一体で提供するが、現状のリポジトリは OpenSpec 資料のみで実装物が存在しない。
- 開発者が仕様を実行に移すためには、共通のディレクトリ構成、パッケージ設定、CI による lint/test パイプラインを定義する必要がある。

## 目的
- Monorepo のベース構造と依存ツールチェーンを整備し、後続タスク（スキーマ実装や抽出器作成）が即座に着手できる状態にする。
- 3OS（Ubuntu/macOS/Windows）で Python 3.12 + Node 20 の lint/test を自動実行し、クロスプラットフォーム要件を満たす。

## スコープ
- packages/playlog-core, playlog-cli, playlog-gui を空パッケージとして作成し、pyproject.toml / package.json / 各種設定ファイル（ruff, mypy, pytest, eslint, prettier, vite）を配置する。
- GitHub Actions Workflow を追加し、Python/Node のセットアップと lint/test 実行をマトリクス構成で回す。
- README にバッジと開発手順の最小記述を追加する。

## 非スコープ
- PlayEvent モデルや抽出器ロジックの実装
- GUI の画面設計や PyInstaller 連携
- 配布用ビルド（electron-builder, PyInstaller スクリプト）

## 期待される効果
- 仕様に沿ったツールチェーンが定義された状態で以降の Feature 変更を安全に進められる。
- CI により lint/test が常に検証され、マルチプラットフォームの互換性リスクを早期に検出できる。

## リスクと緩和策
- Node/Python バージョン差異による失敗 → asdf/pyenv 指定ではなく `actions/setup-*` で固定バージョンを取得。
- ディレクトリ構成の齟齬 → README と AGENTS.md の構造図を一致させる。

## 承認後の進め方
1. proposal/taks/spec を承認
2. リポジトリ初期化ブランチを作成
3. CI で lint/test を通過させて PR 提出
