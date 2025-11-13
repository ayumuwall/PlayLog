# playlog-cli

PlayLog の Typer 製 CLI です。`playlog-core` の抽出器を呼び出し、夜ごとの JSON/TXT/CSV を出力します。標準出力には NDJSON 形式で進捗ログを流します（`event=session-written` など）。

## `run` コマンド

```
python -m playlog_cli run [OPTIONS]
```

| オプション | 説明 |
| --- | --- |
| `--apps djay,rekordbox,serato` | 対象アプリをカンマ区切りで指定。省略時は3アプリすべて |
| `--out <dir>` | 出力先ディレクトリ（既定は `~/Desktop/PlayLog Archives`） |
| `--formats json,txt,csv` | 書き出すフォーマット。`json` / `txt` / `csv` を任意組み合わせ |
| `--tz <IANA TZ>` | 例: `Asia/Tokyo`。ナイト境界計算や timestamp の整形に使用 |
| `--serato-mode auto|crate|logs` | Serato の抽出モード。`auto` は crate→logs の順で試行 |
| `--serato-root <path>` | `_Serato_` ディレクトリを明示する場合に指定 |
| `--timeline-estimate` | Serato crate に timestamp が無い場合、曲長から `played_at` を推定 |

> rekordbox 用の `--rb-mode` など、追加の CLI フラグは別タスクで実装予定です。

## サンプル

### Serato のみを解析（crate を優先、タイムライン推定 ON）

```bash
python -m playlog_cli run --apps serato \
  --serato-mode auto \
  --serato-root "/Volumes/SSD/_Serato_" \
  --timeline-estimate \
  --formats json \
  --tz Asia/Tokyo
```

### 既定設定で3アプリをまとめて実行

```bash
python -m playlog_cli run --tz Asia/Tokyo --formats json,txt,csv
```

どちらの例でも、処理されたセッションごとに `session.json` / `session.txt` / `session.csv` が `${out}/{app}/{night_date}/{session_id}/` に生成され、標準出力には NDJSON の `{"event":"session-written","app":"serato",...}` のようなログが流れます。
