# 💰 せどり目利きツール

店頭でその場で仕入れ判断できる、せどり業者向けWebアプリ。  
バーコードをスキャンするだけで利益計算・ヤフオク相場・AI判定が一度にできる。

**🔗 公開URL：https://sedori-tool-ynjp2vaw6aydxakeevos4d.streamlit.app**

---

## 主な機能

| 機能 | 概要 |
|------|------|
| 📷 バーコード検索 | カメラでスキャン or JANコード手入力 → Yahoo!APIで商品情報取得 → 利益を自動計算して「買い／やめとこう」を判定 |
| 🔍 手動検索 | 商品名で検索 → 上位5件の利益をまとめて表示 |
| 🏷️ 状態別売値計算 | 商品の写真 or 説明文をAIに渡すと状態（新品同様／良い／可）を自動判定 → 状態に応じた推奨売値を算出 |
| ✍️ AI出品文生成 | Gemini APIが商品名・状態・価格から出品文を自動生成。コピペするだけで使える |
| 📦 ヤフオク落札相場 | 落札済みページをスクレイピングして平均・最高・最低・直近5件を表示 |
| 📝 仕入れメモ帳 | 仕入れ候補 → 出品中 → 売却済みの3ステータスで管理。Google Sheetsに永続保存 |
| 💰 かんたん利益計算 | メルカリ・ラクマ・PayPayフリマ・ヤフオクのプラットフォーム別利益を同時計算 |

---

## 使用技術

| 分類 | 技術 |
|------|------|
| フロントエンド／バックエンド | Python / Streamlit |
| ホスティング | Streamlit Cloud（無料枠） |
| 商品検索・価格取得 | Yahoo!ショッピング API |
| ヤフオク相場取得 | BeautifulSoup4（スクレイピング） |
| AI状態判定・出品文生成 | Google Gemini API（gemini-1.5-flash） |
| データ永続化 | Google Sheets API / gspread |
| バーコード読み取り | pyzbar / Pillow |
| 認証・有料化制御 | streamlit-authenticator / Stripe（実装済み・未有効化） |

---

## 工夫した点

**マルチユーザー対応の設計**  
ニックネームを `user_id` として使い、Google Sheets 上で複数ユーザーのデータを行単位で分離。`sheet.clear()` を使わず `batch_update` で差分書き込みすることで、同時書き込み時のデータ消失を防いでいる。

**有料化の仕組みをコードに組み込み済み**  
Streamlit Secrets に `REQUIRE_LOGIN = "true"` と Stripe の決済リンクを追加するだけでペイウォールが有効になる設計。コードを変更せずに無料 ↔ 有料を切り替えられる。

**ヤフオクAPIの代替実装**  
Yahoo!オークション APIは App ID にオークション権限が付与されず 403 エラーが返るため、落札済みページ（mode=2）をスクレイピングして相場データを取得する方式に切り替えた。

**Gemini API の連打防止**  
写真判定は撮影時のハッシュ値を比較して同一写真では再呼び出しをしない。説明文判定はボタン押下時のみ API を呼ぶ設計にして、不要なリクエストを抑制している。

---

## ローカルで動かす方法

```bash
pip install -r requirements.txt
```

`.streamlit/secrets.toml` を作成して以下を設定：

```toml
YAHOO_APP_ID = "your_yahoo_app_id"
GEMINI_API_KEY = "your_gemini_api_key"
SPREADSHEET_ID = "your_spreadsheet_id"

[gcp_service_account]
type = "service_account"
# ... Google サービスアカウントの JSON を展開して記載
```

```bash
streamlit run app.py
```

---

## 開発背景

高校2年生がプログラミング知識ゼロの状態から、AIを活用して開発。  
実際のせどり業者に使ってもらうことを目的にポートフォリオ兼月額販売ツールとして制作した。

---

## ファイル構成

```
app.py                      エントリーポイント・認証制御・ナビゲーション
utils.py                    共通関数（スクレイピング・API・Gemini・ペイウォール）
sheets.py                   Google Sheets連携（マルチユーザー対応）
pages/
  home.py                   ホーム・統計・かんたん利益計算
  1_📷_バーコード検索.py      バーコードスキャン → 判定 → 詳細
  2_🔍_手動検索.py            キーワード検索 → 利益計算
  3_🏷️_状態別売値計算.py      AI状態判定 → 推奨売値
  4_📋_免責事項.py            利用規約・プライバシーポリシー
  5_📝_メモ帳.py              仕入れ管理（3ステータス）
lp/index.html               Stripe決済LP
```
