# Proposal: add-djay-extractor-task3

## Goal
- AGENTS.md の実装計画 Task3 で定義された djay 抽出器を playlog-core に実装し、Sets フォルダ内の .plist から PlayEvent を生成できるようにする。
- デフォルト探索パス（macOS/Windows）とヒューリスティック抽出ルールを整備し、日時・セッションID・deck 情報を可能な限り補完する。

## Scope
- `packages/playlog-core/playlog/extractors/djay.py` を追加し、`Sets` ディレクトリ探索、.plist パース、PlayEvent 正規化までを実装する。
- plist からの session メタ推定（ファイル名/mtime/内部メタデータ）と `NightSession` への変換ヘルパーを用意する。
- フォールバック処理: 期待キーが欠損しても再帰的に `Tracks` 相当の配列を抽出し、最低限 Title/Artist を出力する。
- `assets/fixtures/djay/` に複数 plist サンプルを追加し、`pytest` で件数や night_date 推定ロジックを検証する。
- 既存 Writer/モデルとの統合を確認する smoke テストを追加する。

## Out of Scope
- rekordbox/Serato 等ほかの抽出器の実装・修正。
- GUI/CLI 側での UI 変更（CLI から呼び出し可能にするのは別タスクで扱う）。

## Risks / Mitigations
- plist の構造差異が大きい → 既知のキー（`History Tracks`, `Tracks`, `Root` など）を列挙し、再帰探索で対応。サンプルを増やして回帰テストを行う。
- ファイルサイズが大きい場合の性能 → plist はローカル読み取りのため、ストリーム読み込みと遅延評価を検討。初期実装ではメモリ常駐だが将来 `yield` 化を見込む。
- タイムゾーン推定が不明瞭 → OS ローカルタイムゾーンを既定にし、CLI オプションから override できるようにする（設定値を利用）。

## Success Criteria
- `pytest` に djay 抽出器のフィクスチャテストを追加し、CI で合格する。
- `.plist` から抽出した PlayEvent が night-date 算出・Writer への連携まで一貫して動作する。
- CLI/GUI から呼び出すために必要な `djay.extract()` API が提供され、lint/mypy も通過する。
