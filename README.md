# PlayLog

[![CI](https://github.com/ayumu/PlayLog/actions/workflows/ci.yml/badge.svg)](https://github.com/ayumu/PlayLog/actions/workflows/ci.yml)

DJ / トラックメイカー向けの  
**「プレイ履歴を、夜ごとのログとしてまとめて残す」** デスクトップアプリ（になる予定）です。

> ⚠️ **まだ開発途中のプロジェクトです**
>
> - いまは **インストーラー（アプリ本体）は公開していません**  
> - GitHub 上のソースコード & 設計ドキュメントのみ存在します  
> - 一般ユーザーが簡単にインストールして使える状態ではありません  

---

## これは何？

**PlayLog** は、次の DJ ソフトから再生履歴を集めて、

- 夜ごと（1晩単位）に
- 人間が読みやすいテキスト / 表計算向け CSV / 機械読み取り用 JSON

として保存するツールです。

対応予定の DJ ソフト：

- Algoriddim **djay**
- AlphaTheta **rekordbox**（v5 / v6 / v7）
- **Serato DJ Pro / Serato DJ Lite**

---

## 何ができるの？

（※ すべて「予定している機能」です）

### 1. 起動すると、自動で 3 ソフトをスキャン

アプリを立ち上げると、**毎回**つぎの 3 つを自動チェックします。

- djay のライブラリ
- rekordbox のライブラリ / 履歴
- Serato の `_Serato_` フォルダ

インストールされているソフトだけが検出され、  
見つからないものは静かにスキップされます。

### 2. ボタン一発で「昨晩までのログ」を書き出し

画面には、

- どのソフトが見つかったか
- どれくらいの「夜」が見つかったか

が表示されます。

あとは **「アーカイブ開始」ボタンを押すだけ**で、

- 各ソフトの履歴を読み込み
- 夜ごと（1晩ごと）にまとめ
- テキスト / CSV / JSON をまとめて書き出します。

### 3. 「1晩＝1ファイル」でまとまる

DJ は深夜〜朝までプレイすることが多いので、  
**PlayLog では「その日の朝 8:00 まで」を前日の夜として扱います。**

- 例：2025-11-12 の 23:00〜  
  2025-11-13 の 07:40 まで → **「2025-11-12 の夜」**として 1ファイル
- 8:00 を過ぎたら → 次の日の夜としてカウント

この境界時間（カットオフ）は、設定画面から変更できるようにする予定です。

### 4. 保存される場所

デフォルトの保存先は、あなたのデスクトップ上のフォルダです：

- `デスクトップ / PlayLog Archives`

その中に、アプリごと・日付ごと・セッションごとにフォルダが作られ、

- `session.txt`（人が読む用）
- `session.csv`（Excel / スプレッドシート用）
- `session.json`（機械処理用）
- `session.log` / `session.ndjson`（詳細な動作ログ）

などが保存されます。

### 5. どんな情報が残るの？

DJ ソフト側が提供している範囲で、こんな情報を 1曲ごとに記録します（ソフトによって差があります）。

- 曲名 / アーティスト / アルバム
- 再生順番
- 再生したおおよその時間（取得 / 推定できる場合）
- 再生時間（長さ）
- BPM / Key
- 使用したデッキ（A/B など）
- 元ファイルのパス（あれば）

---

## 想定している使い方

- 自分の DJ セットを **夜ごとに振り返りたい**
- いつ・どこで・どの曲をどれくらいかけているか、  
  **長期的にアーカイブしておきたい**
- 毎回、djay / rekordbox / Serato の別々の画面で履歴を見るのが面倒
- 自分のプレイリストを **テキストベースで残しておきたい**
- 楽曲管理やレポート作成のために、**CSVでログを取りたい**

---

## プライバシーとネットワーク

PlayLog の設計方針：

- **すべての処理はローカルマシンの中だけ**で完結
- 再生履歴やトラック情報を**外部サーバーに送信しない**
- ログファイルの中で、必要ならファイルパスをマスクできるようにする  
  （例：`C:\Users\Ayumu\Music\…` → `C:\Users\***\Music\…`）

---

## いまのステータス（重要）

> 🔧 **開発中 / 未完成のプロジェクトです**

このリポジトリには、

- 設計書（`AGENTS.md`）
- コードの構成方針
- 一部の実装（今後追加予定）

が含まれますが、

- 一般ユーザー向けの **インストーラー（.dmg / .exe）**
- 「ダウンロードしてそのまま使えるアプリ」

は **まだ存在しません**。

### 一般ユーザーの方へ

- いまのところ、**PlayLog をインストールしてすぐ使うことはできません。**
- 将来的には、macOS / Windows 用のインストーラーを用意して、  
  ダウンロードしてダブルクリックするだけで使える形を目指しています。

---

## 開発者向けの情報

詳細仕様やタスク割りは `openspec/AGENTS.md` に集約済みです。以下は参画時に最低限押さえておきたい要点だけを抜粋しています。

### 最低限の構成

| パス | 役割 |
| --- | --- |
| `packages/playlog-core/` | Python 製コア（スキーマ・抽出器・Writer） |
| `packages/playlog-cli/` | Typer ベースの CLI。コアを呼び出してアーカイブを実行 |
| `packages/playlog-gui/` | Electron + React + Vite。GUI から PyInstaller 化したコアを起動 |
| `assets/fixtures/` | djay / rekordbox / Serato のサンプルデータ |
| `openspec/` | 仕様と change 管理。提案はロードマップ番号付き change-id で作成 |

### 技術スタックのざっくり整理

- Python 3.10+（pydantic / typer / pyrekordbox / plistlib など）で抽出と出力処理を実装。
- TypeScript + Electron + React + Vite で GUI を構築し、バックエンドは PyInstaller でバンドルした `playlog` バイナリを spawn。
- 配布は electron-builder（macOS `.dmg` / Windows `.exe`）を想定。

### ローカル環境の最短セットアップ

```bash
# Python (core + CLI)
python3 -m venv .venv && source .venv/bin/activate
pip install -e "packages/playlog-core[dev]" -e "packages/playlog-cli[dev]"
ruff check . && mypy packages/playlog-core/playlog packages/playlog-cli/playlog_cli && pytest

# GUI
cd packages/playlog-gui
npm install
npm run lint && npm run test
npm run dev   # Vite dev server
```

### CI の前提

`.github/workflows/ci.yml` で Ubuntu / macOS / Windows × Python 3.12 / Node 20 のマトリクスを回し、`ruff` / `mypy` / `pytest` / `npm run lint` / `npm run test` がすべて成功しないとマージできません。

---

## 今後のロードマップ（ざっくり）

1. `playlog-core` の実装

    * PlayEvent スキーマ
    * 各ソフトの抽出器（djay / rekordbox / Serato）
    * 1晩=1ファイルのセッション分割ロジック

2. `playlog-cli`

    * `playlog_cli run ...` で CLI から一括アーカイブできるようにする

3. `playlog-gui`

    * 起動時の自動スキャン
    * 「アーカイブ開始」ボタン
    * ログ＆進捗表示

4. パッケージング

    * macOS / Windows 向けインストーラー作成
    * 簡単にインストールできる形にする

5. テスト & ドキュメント整理

    * エッジケース対応
    * ユーザー向けの使い方ガイド

---

## コントリビュートについて

まだ骨組み段階ですが、

* 仕様レビュー
* DJ ソフトの履歴仕様に関する情報共有
* UI のラフ案
* サンプル履歴ファイルの提供（個人情報・実名等を含まない範囲で）

などのコントリビュートは歓迎します。

Issue / Pull Request を送る前に、`AGENTS.md` に目を通してもらえると話が早いです。

---

## ライセンス

（予定）**MIT License**

※ 変更される可能性があります。確定次第、この README に明記します。
