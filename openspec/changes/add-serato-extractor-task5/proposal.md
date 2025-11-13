## Why
- PlayLog は djay / rekordbox のみ対応しており、Serato DJ Pro / Lite のユーザーが 1 晩=1ファイル のエクスポートを行えない状態になっている。
- Serato の履歴データは `_Serato_` 配下で crate（バイナリ）と logs（テキスト）の 2 形式が混在し、既存仕様ではこの差分に対応する抽出パイプラインが未定義である。
- GUI/CLI 双方で起動直後に Serato を自動スキャンする要件（AGENTS.md 3.1）を満たすには、core 層に Serato 抽出器と設定フラグの仕様を先に固める必要がある。

## What Changes
- `playlog-core` に Serato 抽出器を追加し、OS ごとの `_Serato_` 既定パス検出および `auto|crate|logs` モードの切り替え手順を定義する。
- crate/parser: 4 バイトタグ + 長さ + データのバイナリ構造を読み取り、History/Crate ごとのセッション候補と PlayEvent 正規化ルール（曲順維持、deck/played_at 推定、raw 断片格納）を策定する。
- logs/parser: `_Serato_/Logs` のテキストログを解析し、取得できるメタデータのみを補助情報として PlayEvent に埋め込むフォールバック動作を定義する。
- ナイトセッション分割（cutoff=08:00、session_gap=60 分）と `--timeline-estimate` オプションを Serato イベントに適用する際の基準を明文化する。
- CLI/GUI から Serato 抽出を有効化するための設定キー（`--serato-mode`, `--serato-root` 等）とログ要件（NDJSON イベント、root 検出ログ）を specification に反映する。

## Impact
- `playlog-core`: 新規 `serato` extractor、バイナリパーサ、タイムライン推定の Serato 特化ロジック、設定/ファクトリの拡張。
- `playlog-cli`: `--serato-mode`, `--serato-root`, `--timeline-estimate` との連携、auto モード時の優先順位ログ出力。
- `packages/playlog-gui`: 起動時スキャン結果へ Serato 情報を追加し、設定画面に Serato モード切替を露出。
- `assets/fixtures`: crate/logs の最小サンプルを追加し、pytest で利用する。
