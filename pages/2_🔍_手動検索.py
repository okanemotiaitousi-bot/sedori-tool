import streamlit as st
import requests

st.set_page_config(page_title="手動検索", page_icon="🔍", layout="centered")

st.markdown("""
<style>
    .block-container { padding: 1.5rem 1rem 3rem; max-width: 480px; margin: auto; }
    h1 { font-size: 1.3rem !important; }
    .stButton > button { border-radius: 12px; height: 3rem; font-size: 1rem; font-weight: bold; width: 100%; }
    .stNumberInput input { font-size: 1.2rem; height: 3rem; }
    div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.8rem; }
    .item-card {
        background: #f8f9fa; border-radius: 12px;
        padding: 0.8rem; margin: 0.5rem 0;
        cursor: pointer;
    }
    .price-red { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 手動検索")
st.caption("商品名で検索して相場と利益を確認")
st.divider()

keyword = st.text_input("商品名を入力", placeholder="例：ビオレ 洗顔フォーム")

if st.button("🔍 検索する", type="primary"):
    if keyword:
        with st.spinner("検索中..."):
            try:
                res = requests.get(
                    "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
                    params={
                        "appid": st.secrets["YAHOO_APP_ID"],
                        "query": keyword,
                        "results": 5,
                        "sort": "-score",
                    },
                    timeout=5
                )
                data = res.json()
            except Exception as e:
                st.error(f"通信エラー：{e}")
                data = {}

        hits = data.get("hits", [])

        if hits:
            st.markdown(f"**{len(hits)}件見つかりました**")
            st.divider()

            for i, item in enumerate(hits):
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
                        if url:
                            st.markdown(f"[Yahoo!で見る ↗]({url})")

                    if price:
                        st.divider()
                        cost2 = st.number_input(f"仕入れ値（円）", min_value=0, value=0, step=10, key=f"cost_{i}")
                        if cost2 > 0:
                            ship  = 750
                            sell2 = round(int(price) * 0.62)
                            profit = sell2 - cost2 - ship - round(sell2 * 0.10) - 200
                            profit_rate = round(profit / sell2 * 100, 1) if sell2 > 0 else 0

                            c1, c2 = st.columns(2)
                            c1.metric("推定利益", f"¥{profit:,}")
                            c2.metric("利益率", f"{profit_rate}%")

                            if profit >= 800 and profit_rate >= 20:
                                st.success("✅ 買い！")
                            elif profit >= 200 and profit_rate >= 8:
                                st.warning("🤔 検討あり")
                            else:
                                st.error("❌ やめとこう")
        else:
            st.warning("商品が見つかりませんでした。別のキーワードで試してください。")
    else:
        st.warning("商品名を入力してください。")
