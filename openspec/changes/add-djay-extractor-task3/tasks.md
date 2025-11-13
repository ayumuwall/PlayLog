## 1. djay Extractor 実装 (Task3)
- [x] `packages/playlog-core/playlog/extractors/djay.py` を作成し、Sets ディレクトリ探索・plist パース・PlayEvent 正規化ロジックを実装する
- [x] ファイル名/メタ/mtime から night_date・session_id を推定するヘルパーを追加し、サニタイズやタイムゾーン対応を行う

## 2. フィクスチャとテスト
- [x] `assets/fixtures/djay/` に複数の plist サンプル（開始/終了時刻あり・欠損あり）を追加する
- [x] `packages/playlog-core/tests/test_djay_extractor.py` を作成し、抽出件数・night_date 算出・欠損耐性をカバーする
- [x] `pytest` を更新し、新旧テストすべてが通ることを確認する（CI でも有効）

## 3. 開発者向けノート
- [x] README か AGENTS 追補に djay 抽出器の実行方法・既知の制約を記載する
