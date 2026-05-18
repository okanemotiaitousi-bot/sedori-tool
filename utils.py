"""
ヤフオク落札相場取得ユーティリティ
Yahoo! Auction Web Service API（無料枠）を使用
"""
import requests
import streamlit as st


def _fetch_auction_history(query: str, app_id: str, results: int = 20):
    """ヤフオク落札済みオークションを検索してデータを返す"""
    res = requests.get(
        "https://auctions.yahooapis.jp/AuctionWebService/V2/json/searchCompletedAuctions",
        params={
            "appid": app_id,
            "query": query,
            "results": results,
            "sort": "end",
            "order": "d",
        },
        timeout=8,
    )
    data = res.json()

    if "Error" in data:
        return None

    result_data = data.get("ResultSet", {}).get("Result", {})
    items_raw = result_data.get("Item", [])
    if not items_raw:
        return None
    # 1件の場合はlistではなくdictになるため統一
    if isinstance(items_raw, dict):
        items_raw = [items_raw]

    items = []
    prices = []
    for item in items_raw:
        try:
            raw_price = item.get("Price") or item.get("CurrentPrice") or "0"
            price = int(str(raw_price).replace(",", ""))
            if price <= 0:
                continue
            end_time = item.get("EndTime", "")
            end_short = end_time[5:10].replace("-", "/") if len(end_time) >= 10 else ""
            items.append({
                "title": item.get("Title", ""),
                "price": price,
                "end": end_short,
            })
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
        "items": items[:5],
    }


def show_auction_prices(product_name: str, cache_key: str):
    """
    ヤフオク落札相場をStreamlitウィジェットで表示する。

    product_name : APIに渡す検索キーワード（商品名）
    cache_key    : session_stateのキャッシュ識別子（JAN / 商品名 等）
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

    if data is None:
        st.caption("ヤフオクのデータが取得できませんでした")
        return

    # ── サマリ ──────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("平均落札価格", f"¥{data['avg']:,}")
    c2.metric("最低落札", f"¥{data['min']:,}")
    c3.metric("最高落札", f"¥{data['max']:,}")
    st.caption(f"直近 {data['count']} 件の落札データ（ヤフオク）")

    # ── 最近の落札リスト ──────────────────────
    if data["items"]:
        for item in data["items"]:
            c1, c2 = st.columns([4, 1])
            c1.caption(item["title"][:35])
            c2.caption(f"¥{item['price']:,}　{item['end']}")
