## ADDED Requirements
### Requirement: Serato Library Detection
Serato 抽出器は `_Serato_` ディレクトリの既定パス（macOS: `~/Music/_Serato_`, Windows: `C:\\Users\\<user>\\Music\\_Serato_`）を自動探索し、`--serato-root` で上書きできるようにすることを **MUST** とする。`serato-mode=auto` の場合は crate 解析を優先し、失敗時のみ logs モードへフォールバックする。

#### Scenario: auto-detect default roots
- **WHEN** ユーザーが `serato-mode=auto` で実行し、既定パスに `_Serato_` が存在する
- **THEN** 抽出器は crate/history を列挙してセッション候補を作成し、検出結果を NDJSON ログへ `component=serato` として記録する

#### Scenario: honor explicit root override
- **WHEN** `--serato-root /Volumes/External/_Serato_` が指定される
- **THEN** 抽出器は既定パスを無視し、指定パスの crate/logs を走査しつつモード選択（crate→logs フォールバック）をログに出力する

### Requirement: Serato Crate Parsing
crate/history ファイルの 4 バイトタグ + 4 バイト長 + データ構造を解析し、トラック順序を維持した PlayEvent を生成することを **MUST** とする。欠損フィールドは `None`/空文字を許容し、raw データ片を `PlayEvent.raw` に格納する。

#### Scenario: parse binary crate entries
- **WHEN** crate ファイルが `otrk` エントリを含み、タイトル/アーティスト/BPM/再生時間のタグが存在する
- **THEN** 抽出器は順次読み取りながら Unicode へ変換し、PlayEvent に `title`, `artist`, `duration_sec`, `deck` を設定して出力する

#### Scenario: tolerate missing metadata
- **WHEN** crate の一部タグが欠損しているか、Serato ライブラリに絶対時刻が含まれない
- **THEN** 抽出器は欠損項目を `None` にした上でイベントを生成し、取得できたキーのみを raw に保存して後段処理で参照できるようにする

### Requirement: Serato Logs Extraction
`serato-mode=logs`（もしくは auto フォールバック）では `_Serato_/Logs` 内のテキストセッションファイルを解析し、得られる session_id / played_at / deck / error 情報を best-effort で PlayEvent に反映することを **SHALL** とする。

#### Scenario: parse log sessions
- **WHEN** `_Serato_/Logs/2025-03-10@Club.log` に曲の開始時刻とタイトルが記録されている
- **THEN** 抽出器はログを読み取り、行ごとのタイムスタンプを ISO8601 `played_at` に変換し、session_id をログファイル名からサニタイズして設定する

#### Scenario: degrade gracefully on sparse logs
- **WHEN** ログが開始時刻のみを含み、曲ごとの詳細が無い
- **THEN** 抽出器は利用可能なフィールドのみで PlayEvent を生成し、欠損について info レベルの NDJSON ログを出力する

### Requirement: Serato Session Normalization
Serato 由来のイベントは night cutoff（既定 08:00）、`session_gap=60` 分、`--timeline-estimate` オプションを適用して 1 晩=1ファイルのセッションに正規化することを **MUST** とする。

#### Scenario: compute night dates
- **WHEN** crate の最小 `played_at` が `2025-05-02T02:30`、cutoff=08:00 が適用される
- **THEN** 抽出器は night_date を `2025-05-01` と判断し、出力ファイル名に `20250501_serato_NIGHT_<session>` を使用できるよう session メタを構築する

#### Scenario: apply timeline estimation
- **WHEN** `--timeline-estimate` が有効で crate に絶対時刻が無い
- **THEN** 抽出器はセッション開始推定時刻と曲長から played_at を推定し、ヘッダに `timeline_mode=estimated` を設定して Writer に渡す
