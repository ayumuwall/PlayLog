## ADDED Requirements
### Requirement: PlayEvent Normalization
PlayLog コアは全DJソフトの抽出結果を `PlayEvent` スキーマへ正規化し、日付/時刻/デッキ/メタ情報を欠損許容付きで型安全に扱えることを **MUST** とする。

#### Scenario: Accept well-formed event
- WHEN extractor がタイトル・アーティスト・ISO8601形式の `played_at` を含む1件のトラックをモデルに渡す
- THEN Pydantic モデルが値を受け入れて `app`, `session_id`, `played_at` などが正規化され、`dict()` の結果がJSONシリアライズ可能になる

#### Scenario: Reject invalid payload
- WHEN `title` が空文字で `duration_sec` に負数を含むペイロードを検証する
- THEN モデルが ValidationError を発生させ、呼び出し元に理由を返す

### Requirement: Per-Night Writer Outputs
Writer 実装は 1晩=1ファイルの原則で JSON/TXT/CSV を生成し、ナイト日付・アプリ名・セッションIDを含むファイル名/ディレクトリ構造を **SHALL** で統一する。

#### Scenario: Emit per-night artifacts
- WHEN セッションメタ（night_date=2025-11-12, app=rekordbox, session_id=HISTORY-001）と PlayEvent 配列を Writer に渡す
- THEN `{OUT}/rekordbox/2025-11-12/HISTORY-001/` 配下に `session.json`, `session.txt`, `session.csv` が作成され、TXTはAGENTS.mdのテンプレートでレンダリングされる

#### Scenario: Sanitize reserved characters
- WHEN session_id に `HIS/<>:*?` のようなOS予約文字が含まれる
- THEN Writer がサニタイズ処理を行い、安全なファイル/フォルダ名で出力し、ログには置換後の値が記録される
