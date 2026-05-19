import streamlit as st
import requests
from datetime import datetime
from utils import show_auction_prices
import sheets as gs

# ── 検索履歴のロード（セッション初回のみ）────────────────
if "search_history" not in st.session_state:
    if gs.is_enabled():
        st.session_state.search_history = gs.load_search_history()
    else:
        st.session_state.search_history = []


st.markdown("""
<style>
    .block-container { padding: 1.5rem 1rem 3rem; max-width: 480px; margin: auto; }
    h1 { font-size: 1.3rem !important; }
    .stButton > button { border-radius: 12px; height: 3rem; font-size: 1rem; font-weight: bold; width: 100%; }
    .stNumberInput input { font-size: 1.2rem; height: 3rem; }
    div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.8rem; }
    .price-red { color: #e74c3c; font-weight: bold; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 手動検索")
st.divider()

# ── 入力を上に全部まとめる ────────────────────────────────
keyword = st.text_input("商品名を入力", placeholder="例：ビオレ 洗顔フォーム")

col1, col2 = st.columns(2)
with col1:
    cost = st.number_input("仕入れ値（円）", min_value=0, value=0, step=10)
with col2:
    sell_input = st.number_input("売値（円）※空白で自動推定", min_value=0, value=0, step=10)

ship_name = st.selectbox("配送方法", [
    "らくらくメルカリ便 60サイズ（750円）",
    "ゆうパケット（230円）",
    "ネコポス（210円）",
    "らくらくメルカリ便 80サイズ（850円）",
])
ship_map = {
    "らくらくメルカリ便 60サイズ（750円）": 750,
    "ゆうパケット（230円）": 230,
    "ネコポス（210円）": 210,
    "らくらくメルカリ便 80サイズ（850円）": 850,
}
ship_cost = ship_map[ship_name]

if st.button("🔍 検索する", type="primary"):
    st.session_state["search_keyword"]  = keyword
    st.session_state["search_cost"]     = cost
    st.session_state["search_sell"]     = sell_input
    st.session_state["search_ship"]     = ship_cost
    st.session_state["search_results"]  = None

# ── 検索実行 ──────────────────────────────────────────────
if st.session_state.get("search_keyword") and st.session_state.get("search_results") is None:
    with st.spinner("検索中..."):
        try:
            res = requests.get(
                "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
                params={
                    "appid":   st.secrets["YAHOO_APP_ID"],
                    "query":   st.session_state["search_keyword"],
                    "results": 5,
                    "sort":    "-score",
                },
                timeout=5
            )
            hits_data = res.json().get("hits", [])
            st.session_state["search_results"] = hits_data

            # 履歴への保存はここ（API取得直後）で1回だけ実行する
            cost_at_search = st.session_state.get("search_cost", 0)
            ship_at_search = st.session_state.get("search_ship", 750)
            sell_at_search = st.session_state.get("search_sell", 0)
            if cost_at_search > 0:
                if "search_history" not in st.session_state:
                    st.session_state.search_history = []
                new_history = list(st.session_state.search_history)
                for item in hits_data:
                    name  = item.get("name", "不明")
                    price = item.get("price", None)
                    sell  = sell_at_search if sell_at_search > 0 else (
                        round(int(price) * 0.62) if price else 0
                    )
                    if sell > 0:
                        profit      = sell - cost_at_search - ship_at_search - round(sell * 0.10) - 200
                        profit_rate = round(profit / sell * 100, 1)
                        new_history = [h for h in new_history if h.get("name") != name]
                        new_history.append({
                            "name": name,
                            "jan": "",
                            "cost": cost_at_search,
                            "sell": sell,
                            "ship_cost": ship_at_search,
                            "profit": profit,
                            "profit_rate": profit_rate,
                            "time": datetime.now().strftime("%H:%M"),
                            "date": datetime.now().strftime("%Y-%m-%d"),
                        })
                st.session_state.search_history = new_history[-30:]
                if gs.is_enabled():
                    gs.save_search_history(st.session_state.search_history)

        except Exception as e:
            st.error(f"通信エラー：{e}")
            st.session_state["search_results"] = []

# ── 結果表示 ──────────────────────────────────────────────
hits       = st.session_state.get("search_results", [])
cost_used  = st.session_state.get("search_cost", 0)
sell_used  = st.session_state.get("search_sell", 0)
ship_used  = st.session_state.get("search_ship", 750)

if hits:
    st.divider()
    st.markdown(f"**{len(hits)}件の結果**")

    for item in hits:
        name      = item.get("name", "不明")
        price     = item.get("price", None)
        image_url = item.get("image", {}).get("small", "")
        url       = item.get("url", "")
        brand     = item.get("brand", {}).get("name", "")

        with st.container(border=True):
            col_img, col_info = st.columns([1, 3])
            with col_img:
                if image_url:
                    st.image(image_url, use_container_width=True)
            with col_info:
                st.markdown(f"**{name[:35]}**")
                if brand:
                    st.caption(f"🏷 {brand}")
                if price:
                    st.markdown(f'<span class="price-red">¥{int(price):,}</span>', unsafe_allow_html=True)
                    st.caption("Yahoo!最安値")
                if url:
                    st.markdown(f"[Yahoo!で見る ↗]({url})")

            if cost_used > 0:
                sell = sell_used if sell_used > 0 else (round(int(price) * 0.62) if price else 0)
                if sell > 0:
                    profit      = sell - cost_used - ship_used - round(sell * 0.10) - 200
                    profit_rate = round(profit / sell * 100, 1)

                    sell_label = f"¥{sell:,}（自動推定）" if sell_used == 0 else f"¥{sell:,}"
                    st.caption(f"売値：{sell_label}")

                    c1, c2 = st.columns(2)
                    c1.metric("利益", f"¥{profit:,}")
                    c2.metric("利益率", f"{profit_rate}%")

                    if profit >= 800 and profit_rate >= 20:
                        st.success("✅ 買い！")
                    elif profit >= 200 and profit_rate >= 8:
                        st.warning("🤔 検討あり")
                    else:
                        st.error("❌ やめとこう")

                    with st.expander("📦 ヤフオク落札相場を見る"):
                        show_auction_prices(name, name[:30])

                    # メモに追加ボタン
                    if "memo_list" not in st.session_state:
                        st.session_state.memo_list = []
                    already = any(m.get("name") == name for m in st.session_state.memo_list)
                    if already:
                        st.info("📝 メモ帳に保存済み")
                        st.page_link("pages/5_📝_メモ帳.py", label="📋 メモ帳を開く", use_container_width=True)
                    else:
                        if st.button("📝 仕入れ候補にメモ", key=f"memo_{name[:20]}"):
                            st.session_state.memo_list.append({
                                "name": name,
                                "jan": "",
                                "cost": cost_used,
                                "sell": sell,
                                "profit": profit,
                                "profit_rate": profit_rate,
                                "time": datetime.now().strftime("%H:%M"),
                                "status": "候補",
                                "ship_name": ship_name,
                            })
                            if gs.is_enabled():
                                gs.save_memo_list(st.session_state.memo_list)
                            st.rerun()


elif st.session_state.get("search_results") is not None:
    st.warning("商品が見つかりませんでした。別のキーワードで試してください。")
