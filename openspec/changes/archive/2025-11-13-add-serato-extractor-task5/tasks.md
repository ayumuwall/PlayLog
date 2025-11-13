## 1. Implementation
- [x] 1.1 `_Serato_` 既定パス検出ロジック（macOS: `~/Music/_Serato_`, Windows: `C:\\Users\\<user>\\Music\\_Serato_`）と `--serato-root` overrides を playlog-core 設定に追加する。
- [x] 1.2 crate/history バイナリ（4 バイトタグ + サイズ + データ）を走査するパーサーを実装し、曲順維持・Unicode/文字コード変換・生データの raw 保持を含む PlayEvent 正規化を行う。
- [x] 1.3 `_Serato_/Logs` のテキストログを解析し、取得可能な played_at / deck / session 情報を補完する logs モードを実装する（欠損時は best-effort で None を設定）。
- [x] 1.4 `serato-mode=auto|crate|logs` の切り替えとフォールバック順（auto=crate優先、失敗時にlogs）を定義し、NDJSON ロギングへモード選択経緯を出力する。
- [x] 1.5 ナイトセッション分割（cutoff, session_gap）と `--timeline-estimate` の Serato 取得データへの適用ルールを実装し、session_id/night_date/sanitized path を Writer へ渡す。
- [x] 1.6 CLI/GUI から Serato 抽出を呼び出せるよう、playlog-cli コマンドと GUI 設定項目を更新する。

## 2. Testing & Fixtures
- [x] 2.1 `assets/fixtures/serato` に crate/logs サンプルを追加し、pytest で crate/logs それぞれの出力件数・PlayEvent フィールドを検証するユニット/統合テストを書く。
- [x] 2.2 CLI 経由のエンドツーエンドテストを追加し、`--serato-mode` と `--timeline-estimate` の挙動、エラー時フォールバック、NDJSON ログ出力を確認する。

## 3. Documentation
- [x] 3.1 AGENTS.md / README に Serato 対応手順、`--serato-mode` / `--serato-root` の使い方、logs モードの制限事項を追記する。
