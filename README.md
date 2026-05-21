# 💰 せどり目利きツール｜仕入れ判断業務を自動化するWebアプリ

> **「店頭でスマホをかざすだけで、仕入れ可否が即座にわかる」**  
> API連携・スクレイピング・AI活用・クラウドDB構築を組み合わせた業務自動化ツール

**🔗 デモ：https://sedori-tool-ynjp2vaw6aydxakeevos4d.streamlit.app**  
**📂 対象：クラウドソーシング案件獲得用ポートフォリオ**

---

## 解決した課題（ビジネス視点）

せどり（転売）業者が店頭で直面する課題は「**仕入れ判断に時間がかかりすぎる**」こと。

従来は「商品を見る → スマホで相場を手動検索 → 計算 → 判断」という手順に1商品あたり数分かかっていた。  
本ツールはこの全工程を自動化し、**バーコードをスキャンするだけで利益・相場・AI判定が10秒以内に揃う**状態を実現した。

| 課題 | 解決手段 |
|------|------|
| 相場調査に時間がかかる | Yahoo!ショッピングAPI・ヤフオクスクレイピングで自動取得 |
| プラットフォームごとの利益計算が面倒 | 4社（メルカリ・ラクマ・PayPay・ヤフオク）を同時に自動計算 |
| 商品状態の判断が主観的でバラつく | Gemini Vision APIが画像から客観的に状態を判定 |
| 出品文の作成に時間がかかる | Gemini APIが商品情報から出品文を自動生成 |
| 仕入れ候補の管理が煩雑 | クラウドDB（Google Sheets）でステータス管理を自動化 |

---

## 技術スタック

| レイヤー | 使用技術 |
|----------|------|
| フロントエンド／バックエンド | Python 3 / Streamlit |
| インフラ | Streamlit Cloud（ゼロコスト・CI/CD自動デプロイ） |
| 外部API | Yahoo!ショッピング API v3 |
| スクレイピング | BeautifulSoup4 / Requests |
| AI・自然言語処理 | Google Gemini API（gemini-1.5-flash）|
| 画像処理 | Pillow / pyzbar（バーコードデコード） |
| クラウドデータベース | Google Sheets API v4 / gspread |
| 認証・決済 | streamlit-authenticator / Stripe（実装済み） |

---

## 技術的工夫（アピールポイント）

### 1. 403エラーを回避するスクレイピング実装

Yahoo!オークション APIはアプリIDへのオークション権限付与が制限されており、正規APIでは**403エラー**が返り続ける状況だった。

これを回避するため、落札済み検索ページ（`mode=2`）をBeautifulSoup4で直接スクレイピングする方式に切り替え、平均・最高・最低・直近5件の落札データを取得する独自実装を構築した。

```python
url = (
    "https://auctions.yahoo.co.jp/search/search"
    f"?p={urllib.parse.quote(query)}&auccat=0&s1=end&o1=d&mode=2"
)
# モバイルUAを設定してブロックを回避
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (iPhone...)"}, timeout=10)
```

- `@st.cache_data(ttl=1800)` で30分キャッシュし、サーバー負荷と取得コストを最小化
- スクレイピング失敗時は外部リンクにフォールバックする冗長設計

---

### 2. 複数ユーザーの同時アクセスによるデータ競合を防ぐDB設計

Google Sheetsをクラウドデータベースとして使用する際、複数ユーザーが同時に書き込むと**データが上書き・消失するリスク**がある。

これを防ぐため、以下の設計を採用した。

**① `sheet.clear()` の完全廃止**  
全消去 → 再書き込みの間にデータが消える瞬間をなくすため、`batch_update` による差分上書き方式に変更。

**② `user_id` 列によるユーザーデータの行単位分離**  
書き込み前に全行を取得し、「他ユーザーの行はそのまま保持」「自ユーザーの行のみ差し替え」というロジックで競合を防止。

**③ 指数バックオフ付きリトライ（最大3回）**  
Google APIの `429 Quota Exceeded` エラーに対応し、15秒待機→再試行を自動で実行。

```python
def _safe_batch_write(sheet, rows):
    def _write():
        existing_count = len(sheet.get_all_values())
        sheet.update(rows, "A1")
        if existing_count > len(rows):
            blank = [[""] * len(rows[0])] * (existing_count - len(rows))
            sheet.update(blank, f"A{len(rows) + 1}")
    return _with_retry(_write)  # 指数バックオフで最大3回リトライ
```

---

### 3. Gemini APIを活用した画像判定・出品文の自動生成

**画像による商品状態の自動判定（Gemini Vision）**

ユーザーが商品を撮影すると、画像をそのままGemini APIに渡して「未使用・新品同様／良い／可／不可」の4段階を自動判定。

- 同一画像への重複APIコールを防ぐため、`hashlib.md5` で画像のハッシュ値を比較し、新しい撮影時のみAPIを呼び出す設計
- API失敗時はキーワードマッチングによるフォールバック判定を実装

**自然言語による出品文の自動生成**

商品名・状態・価格・配送方法を渡すと、Gemini APIがメルカリ向けの出品文を自動生成。プロンプトエンジニアリングで文体・絵文字・文字数を制御している。

```python
prompt = f"""メルカリに出品するための商品説明文を作成してください。
商品名: {product_name} / 状態: {condition} / 販売価格: ¥{sell_price:,}
条件：ですます調・{condition}の特徴を具体的に・絵文字を適度に・400文字以内"""
```

---

## システム構成

```
app.py                      エントリーポイント・認証制御・ルーティング
utils.py                    外部API・スクレイピング・Gemini処理の共通モジュール
sheets.py                   Google Sheets永続化層（マルチユーザー・競合制御）
pages/
  home.py                   ダッシュボード・統計・利益計算
  1_📷_バーコード検索.py      バーコードスキャン → 判定 → AI出品文
  2_🔍_手動検索.py            キーワード検索 → 複数商品の利益一覧
  3_🏷️_状態別売値計算.py      Gemini Vision判定 → 推奨売値算出
  4_📋_免責事項.py            利用規約・プライバシーポリシー
  5_📝_メモ帳.py              仕入れ管理（候補→出品中→売却済み）
lp/index.html               Stripe決済ランディングページ
```

---

## 有料化・認証の実装状況

Stripe決済・ログイン認証はコードに完全実装済み。  
Streamlit Secretsに以下を追加するだけで即時有料化が可能な設計。

```toml
REQUIRE_LOGIN = "true"
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/..."
```

現在はテスター向けに全機能を無料公開中。

---

## 開発背景

業務自動化・API連携・AIを活用したWebアプリ開発のポートフォリオとして制作。  
**「実際に使われるプロダクト」**を目標に、設計・実装・デプロイまでを一人で完結させた。
