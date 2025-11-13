# Proposal: add-core-schema-writers

## Goal
- PlayEvent スキーマとセッションメタモデルを Pydantic で定義し、抽出結果を共通フォーマットへ正規化できる状態を作る。
- Writer 抽象と JSON/TXT/CSV 実装を整備し、1晩=1ファイルの出力仕様（AGENTS.md 準拠）を満たす。

## Scope
- `packages/playlog-core/playlog/models.py` に PlayEvent/NightSession/PlaylogConfig などのモデルとサニタイズ/日付変換ユーティリティを実装。
- `packages/playlog-core/playlog/writers.py` に Writer 抽象、JsonWriter、TxtWriter、CsvBatchWriter を実装し、出力ディレクトリ構造とファイル命名ロジックを含める。
- AGENTS.md の TXT テンプレートやナイト日付算出ルール（cutoff=08:00 既定）をコード化し、`assets/fixtures` を用いたテストを追加。
- `pytest` で PlayEvent→各Writerの出力比較テストを追加し、予約文字サニタイズや per-night 分割ロジックを検証。

## Assumptions
- Python 3.10+ / Pydantic v2 系を前提にモデルを実装する。
- timezone/cutoff の計算は標準ライブラリ `zoneinfo` で対応可能であり、追加依存は不要。
- CSV Writer は「1晩=1ファイル」を既定とし、統合CSVは将来オプションのフックのみ用意すればよい。

## Success Criteria
- `pytest` が PlayEvent/Writer 関連テストを通過し、CI で失敗しない。
- JSON/TXT/CSV の出力内容とファイル名が仕様（カットオフ・フォーマット・サニタイズ）に従う。
- 新規追加したモデル/ユーティリティに対し mypy/ruff でエラーが発生しない。
