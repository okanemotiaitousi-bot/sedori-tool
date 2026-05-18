"""
共通ユーティリティ
- ヤフオク落札相場取得・表示
- Yahoo!ショッピング最安値取得
- Gemini 出品文自動生成
"""
import urllib.parse
import requests
import streamlit as st
import google.generativeai as genai


# ── Gemini 出品文自動生成 ─────────────────────────────────
def generate_listing_text(product_name: str, condition: str, sell_price: int, ship_name: str) -> str:
    """
    Gemini で メルカリ出品文を自動生成する。
    condition : 未使用・新品同様 / 良い / 可 / 不可
    """
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
def fetch_yahoo_lowest_price(query: str, app_id: str) -> int | None:
    """
    Yahoo!ショッピングAPIで商品名から最安値を取得する。
    見つからない場合は None を返す。
    """
    try:
        res = requests.get(
            "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
            params={
                "appid": app_id,
                "query": query,
                "results": 1,
                "sort": "+price",
            },
            timeout=5,
        )
        hits = res.json().get("hits", [])
        if hits and hits[0].get("price"):
            return int(hits[0]["price"])
        return None
    except Exception:
        return None


# ── ヤフオク落札相場取得 ──────────────────────────────────
def _parse_items(items_raw: list | dict, completed: bool) -> tuple[list, list]:
    """APIレスポンスのItemリストをパースしてitemsとpricesを返す"""
    if isinstance(items_raw, dict):
        items_raw = [items_raw]

    items, prices = [], []
    for item in items_raw:
        try:
            if completed:
                raw = item.get("Price") or "0"
            else:
                raw = item.get("CurrentPrice") or item.get("Price") or "0"
            price = int(str(raw).replace(",", ""))
            if price <= 0:
                continue
            end_time = item.get("EndTime", "")
            end_short = end_time[5:10].replace("-", "/") if len(end_time) >= 10 else ""
            items.append({"title": item.get("Title", ""), "price": price, "end": end_short})
            prices.append(price)
        except Exception:
            continue
    return items, prices


def _call_auction_api(endpoint: str, params: dict) -> dict | None:
    """ヤフオクAPIを呼び出してJSONを返す。エラー時はNone"""
    try:
        res = requests.get(endpoint, params=params, timeout=8)
        data = res.json()
        if "Error" in data:
            return None
        return data
    except Exception:
        return None


def _fetch_auction_history(query: str, app_id: str, results: int = 20) -> dict | None:
    """
    ヤフオク落札済み検索 → 失敗時は現在出品中にフォールバックして返す。
    """
    base_params = {"appid": app_id, "query": query, "results": results}

    # ① 落札済み検索
    data = _call_auction_api(
        "https://auctions.yahooapis.jp/AuctionWebService/V2/json/searchCompletedAuctions",
        {**base_params, "sort": "end", "order": "d"},
    )
    if data:
        items_raw = data.get("ResultSet", {}).get("Result", {}).get("Item", [])
        if items_raw:
            items, prices = _parse_items(items_raw, completed=True)
            if prices:
                return _build_result(items, prices, completed=True)

    # ② フォールバック：現在出品中検索
    data = _call_auction_api(
        "https://auctions.yahooapis.jp/AuctionWebService/V2/json/search",
        {**base_params, "sort": "cbids", "order": "d"},
    )
    if data:
        items_raw = data.get("ResultSet", {}).get("Result", {}).get("Item", [])
        if items_raw:
            items, prices = _parse_items(items_raw, completed=False)
            if prices:
                return _build_result(items, prices, completed=False)

    return None


def _build_result(items: list, prices: list, completed: bool) -> dict:
    return {
        "avg": round(sum(prices) / len(prices)),
        "min": min(prices),
        "max": max(prices),
        "count": len(prices),
        "items": items[:5],
        "completed": completed,
    }


# ── Streamlit表示 ─────────────────────────────────────────
def show_auction_prices(product_name: str, cache_key: str):
    """
    ヤフオク落札相場をStreamlitウィジェットで表示する。
    product_name : APIに渡す検索キーワード
    cache_key    : session_stateのキャッシュ識別子
    """
    field = f"_auction_{cache_key}"

    if field not in st.session_state:
        with st.spinner("📦 ヤフオク相場を取得中..."):
            try:
                st.session_state[field] = _fetch_auction_history(
                    product_name, st.secrets["YAHOO_APP_ID"]
                )
            except Exception:
                st.session_state[field] = None

    data = st.session_state[field]

    # ヤフオクで直接検索するリンク（常に表示）
    yauction_url = (
        "https://auctions.yahoo.co.jp/search/search?p="
        + urllib.parse.quote(product_name)
        + "&auccat=0&s1=cbids&o1=d"
    )
    st.markdown(f"[🔗 ヤフオクで検索する →]({yauction_url})")

    if data is None:
        st.caption("APIからのデータ取得に失敗しました。上のリンクから直接確認してください。")
        return

    label = "落札済み" if data.get("completed", True) else "現在出品中（参考価格）"
    c1, c2, c3 = st.columns(3)
    c1.metric("平均価格", f"¥{data['avg']:,}")
    c2.metric("最低", f"¥{data['min']:,}")
    c3.metric("最高", f"¥{data['max']:,}")
    st.caption(f"直近 {data['count']} 件・{label}（ヤフオク）")

    if data["items"]:
        for item in data["items"]:
            c1, c2 = st.columns([4, 1])
            c1.caption(item["title"][:35])
            c2.caption(f"¥{item['price']:,}　{item['end']}")
