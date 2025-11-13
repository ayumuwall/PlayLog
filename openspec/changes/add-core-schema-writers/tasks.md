## 1. モデル/ユーティリティ実装
- [x] `packages/playlog-core/playlog/models.py` に PlayEvent/NightSession/PlaylogConfig とサニタイズ・カットオフ計算ユーティリティを追加する
- [x] Pydantic バリデーション（必須フィールド、ISO8601時刻、tz扱い）と単体テストを作成する

## 2. Writer 抽象とフォーマット実装
- [x] `writers.py` に Writer 抽象を定義し、JSON/TXT/CSV Writer を実装して出力ディレクトリ構造・ファイル名ルールを統一する
- [x] TXT テンプレート（AGENTS.md準拠）と CSV 1晩=1ファイル出力を検証する pytest を追加する

## 3. 開発者向け整備
- [x] assets/fixtures にテスト用サンプルを追加し、README へ PlayEvent/Writer 概要とテスト実行方法を追記する
- [x] ruff/mypy/pytest を実行し、CI が通ることを確認する
