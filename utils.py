"""
共通ユーティリティ
- ヤフオク落札相場取得・表示（スクレイピング）
- Yahoo!ショッピング最安値取得
- Gemini 出品文自動生成
- ペイウォール表示
"""
import re
import urllib.parse
import requests
import streamlit as st


# ── ペイウォール ───────────────────────────────────────────
def _paywall_content():
    """
    ペイウォールの共通コンテンツ。
    - Stripe 決済リンク（Secrets に STRIPE_PAYMENT_LINK があれば有効）
    - streamlit-authenticator ログインフォーム（Secrets に credentials があれば表示）
    - ログイン成功時は user_id を更新して st.rerun() する
    """
    st.markdown(
        """
<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);
 color:white;border-radius:20px;padding:2rem 1.5rem;text-align:center;margin-bottom:1.2rem">
 <div style="font-size:3rem">🔒</div>
 <h2 style="margin:0.5rem 0 0.3rem;font-size:1.35rem;font-weight:900">プレミアムプラン限定機能</h2>
 <p style="font-size:0.88rem;opacity:0.8;margin:0;line-height:1.6">
  仕入れメモ帳への保存・閲覧は<br>プレミアムプラン会員専用です
 </p>
</div>
""",
        unsafe_allow_html=True,
    )

    stripe_url = str(st.secrets.get("STRIPE_PAYMENT_LINK", "")).strip()
    has_stripe = stripe_url and stripe_url != "STRIPE_PAYMENT_LINK_HERE"

    col1, col2 = st.columns(2)
    with col1:
        if has_stripe:
            st.link_button(
                "💳 プランに登録する",
                stripe_url,
                use_container_width=True,
                type="primary",
            )
        else:
            st.button("💳 準備中", disabled=True, use_container_width=True)
    with col2:
        st.page_link(
            "pages/4_📋_免責事項.py",
            label="📋 料金・利用規約",
            use_container_width=True,
        )

    # ── ログインフォーム（credentials が設定されている場合のみ表示）──
    creds = st.secrets.get("credentials", {})
    if not creds:
        return

    st.divider()
    st.markdown("**📧 登録済みの方はこちらからログイン**")

    try:
        import streamlit_authenticator as stauth

        cookie_cfg = st.secrets.get(
            "cookie",
            {"name": "sedori_tool_auth", "key": "sedori_secret_key_2026", "expiry_days": 30},
        )
        authenticator = stauth.Authenticate(
            dict(creds),
            cookie_cfg.get("name", "sedori_tool_auth"),
            cookie_cfg.get("key", "sedori_secret_key_2026"),
            int(cookie_cfg.get("expiry_days", 30)),
        )
        try:
            authenticator.login(
                location="main",
                fields={
                    "Form name": "ログイン",
                    "Username": "ユーザー名",
                    "Password": "パスワード",
                    "Login": "ログインする",
                },
            )
        except Exception:
            authenticator.login()

        status = st.session_state.get("authentication_status")
        if status is True:
            st.session_state.user_id = st.session_state.get("username", "default")
            st.rerun()
        elif status is False:
            st.error("ユーザー名またはパスワードが違います")
        else:
            st.info(_contact_msg())

    except Exception:
        st.warning("ログイン機能を初期化できませんでした。管理者にお問い合わせください。")


def _contact_msg() -> str:
    return "ご購入後にお送りしたIDとパスワードを入力してください。"


@st.dialog("🔒 プレミアムプラン限定機能")
def show_paywall_dialog():
    """
    メモボタン押下時に呼ぶポップアップ型ペイウォール。
    usage: if st.button("📝 メモに追加"): show_paywall_dialog()
    """
    _paywall_content()


def show_paywall_page():
    """
    メモ帳ページ先頭で呼ぶフルページ型ペイウォール。
    呼び出し後は必ず st.stop() すること。
    """
    _paywall_content()


# ── Gemini 出品文自動生成 ─────────────────────────────────
def generate_listing_text(product_name: str, condition: str, sell_price: int, ship_name: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""メルカリに出品するための商品説明文を作成してください。

商品名: {product_name}
状態: {condition}
販売価格: ¥{sell_price:,}
配送方法: {ship_name}

条件：
- ですます調で自然な文体
- 状態を具体的に説明（{condition}の場合の一般的な特徴を書く）
- 購入者が安心できる丁寧な内容
- 絵文字を適度に使う
- 400文字以内
- 最後は「よろしくお願いします🙇」で締める

出品文だけを出力してください。"""
    response = model.generate_content(prompt)
    return response.text.strip()


# ── Yahoo!ショッピング最安値取得 ──────────────────────────
@st.cache_data(ttl=1800)  # 30分キャッシュ：同一クエリの重複リクエストを防ぐ
def fetch_yahoo_lowest_price(query: str, app_id: str) -> int | None:
    try:
        res = requests.get(
            "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
            params={"appid": app_id, "query": query, "results": 10, "sort": "-score"},
            timeout=5,
        )
        hits = res.json().get("hits", [])
        prices = [int(h["price"]) for h in hits if h.get("price") and int(h["price"]) > 0]
        return min(prices) if prices else None
    except Exception:
        return None


# ── ヤフオク落札相場スクレイピング ────────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    )
}


@st.cache_data(ttl=1800)  # 30分キャッシュ：ヤフオクへの重複スクレイピングを防ぐ
def _scrape_auction_prices(query: str, results: int = 20) -> dict | None:
    """
    Yahoo!オークションの落札済み検索ページをスクレイピングして
    落札相場データを返す。取得できなかった場合は None。
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    url = (
        "https://auctions.yahoo.co.jp/search/search"
        f"?p={urllib.parse.quote(query)}&auccat=0&s1=end&o1=d&mode=2"
    )

    try:
        res = requests.get(url, headers=_HEADERS, timeout=10)
        if res.status_code != 200:
            return None
    except Exception:
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    li_items = soup.find_all("li", class_="Item")

    parsed, prices = [], []
    for li in li_items:
        if len(parsed) >= results:
            break
        try:
            a = li.find("a", class_="Item__imageLink")
            if not a:
                continue
            price_raw = a.get("data-auction-price", "").strip()
            if not price_raw:
                continue
            price = int(price_raw)
            if price <= 0:
                continue

            # タイトルは複数のクラス候補から取得
            title_el = (
                li.find("p", class_="Item__title")
                or li.find("h3", class_="Item__title")
                or li.find(class_=lambda c: c and "title" in c.lower())
            )
            title = title_el.get_text(strip=True) if title_el else ""

            parsed.append({"title": title, "price": price, "end": ""})
            prices.append(price)
        except Exception:
            continue

    if not prices:
        return None

    return {
        "avg": round(sum(prices) / len(prices)),
        "min": min(prices),
        "max": max(prices),
        "count": len(prices),
        "items": parsed[:5],
        "completed": True,
        "source": "scrape",
    }


# ── Streamlit表示 ─────────────────────────────────────────
def show_auction_prices(product_name: str, cache_key: str):
    """
    ヤフオク落札相場をStreamlitウィジェットで表示する。
    まずスクレイピングで取得し、失敗時は直リンクを表示する。
    """
    q = urllib.parse.quote(product_name)
    completed_url = (
        f"https://auctions.yahoo.co.jp/search/search?p={q}&auccat=0&s1=end&o1=d&mode=2"
    )

    # _scrape_auction_prices は @st.cache_data で30分キャッシュ済み。
    # session_state への二重保存は不要になったが、3_状態別売値計算.py が
    # st.session_state[f"_auction_{cache_key}"] を参照しているため互換のため残す。
    field = f"_auction_{cache_key}"

    if field not in st.session_state:
        with st.spinner("ヤフオク落札相場を取得中..."):
            st.session_state[field] = _scrape_auction_prices(product_name)

    data = st.session_state[field]

    if data is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("平均落札", f"¥{data['avg']:,}")
        c2.metric("最低",     f"¥{data['min']:,}")
        c3.metric("最高",     f"¥{data['max']:,}")
        st.caption(f"直近 {data['count']} 件の落札価格（ヤフオク）")

        if data["items"]:
            for item in data["items"]:
                c1, c2 = st.columns([4, 1])
                c1.caption(item["title"][:36] if item["title"] else "（タイトル取得不可）")
                c2.caption(f"¥{item['price']:,}")

        st.markdown(
            f'<a href="{completed_url}" target="_blank" '
            f'style="font-size:0.82rem;color:#888">🔗 ヤフオクで詳細を確認する →</a>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
<div style="background:#f8f9fa;border-radius:12px;padding:1rem 1.2rem;margin:0.3rem 0">
  <div style="font-size:0.85rem;color:#555;margin-bottom:0.7rem">
    📦 <strong>ヤフオク落札相場</strong>
  </div>
  <a href="{completed_url}" target="_blank"
     style="display:block;background:#ff6b35;color:white;padding:0.55rem 1rem;
            border-radius:10px;text-decoration:none;font-size:0.9rem;
            font-weight:bold;text-align:center">
    🏷️ 落札済み価格を確認する →
  </a>
</div>
""",
            unsafe_allow_html=True,
        )
