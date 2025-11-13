## ADDED Requirements
### Requirement: djay Set Detection
djay 抽出器は macOS/Windows の既定ライブラリパスから `Sets/*.plist` を走査し、最終更新日やファイル名からセッション候補を検出することを **MUST** とする。

#### Scenario: auto-discover default folders
- WHEN macOS の `~/Music/djay/History/Sets` に `.plist` が存在する
- THEN 抽出器はフォルダを自動探索し、各 plist をナイトセッション候補としてキューに追加する

#### Scenario: ignore missing roots gracefully
- WHEN 既定パスが存在しない
- THEN 抽出器は警告ログのみを出し、例外を投げずに他アプリの抽出を続行する

### Requirement: djay plist Normalization
plist 内の `History Tracks` / `Tracks` 配列から PlayEvent を生成し、`session_id`, `night_date`, `played_at`, `deck` などを可能な限り補完することを **MUST** とする。

#### Scenario: parse standard fields
- WHEN plist が `Date Started`, `Song Title`, `Artist`, `StartTime` などのキーを含む
- THEN 抽出器は PlayEvent にタイトル/アーティスト/ISO8601 `played_at` をセットし、`NightSession` として night_date を cut-off 08:00 で算出する

#### Scenario: fallback for missing keys
- WHEN plist に複数のトラック配列があり一部キーが欠損している
- THEN 抽出器は再帰探索で最も詳細なトラック配列を見つけ、欠損フィールドは空文字または `None` に設定しつつイベントを出力する

### Requirement: Session Metadata Rendering
抽出器はファイル名や plist メタデータから `session_id`・`session_label` を決定し、Writer で安全なディレクトリ名として利用できるようサニタイズすることを **SHALL** とする。

#### Scenario: derive session identifiers
- WHEN plist ファイル名が `20251112 DJ Set.plist` で内部に `History Name` が含まれる
- THEN session_id は `History Name` を優先し、存在しない場合はファイル名をサニタイズして使用する

#### Scenario: attach raw fragments
- WHEN トラックレコードに未定義の追加キーが存在する
- THEN 抽出器は元データ断片を `PlayEvent.raw` に格納し、後続処理で利用できるようにする
