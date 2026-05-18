import streamlit as st
import requests
from PIL import Image

st.set_page_config(page_title="せどり目利きツール", page_icon="📷", layout="centered")

st.markdown("""
<style>
    .block-container { padding: 1rem 1rem 2rem; max-width: 460px; margin: auto; }
    h1 { font-size: 1.3rem !important; }

    .verdict-buy {
        background: linear-gradient(135deg, #2ecc71, #27ae60);
        color: white; border-radius: 20px; padding: 2rem 1rem;
        text-align: center; font-size: 2.2rem; font-weight: bold;
    }
    .verdict-maybe {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white; border-radius: 20px; padding: 2rem 1rem;
        text-align: center; font-size: 2.2rem; font-weight: bold;
    }
    .verdict-bad {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white; border-radius: 20px; padding: 2rem 1rem;
        text-align: center; font-size: 2.2rem; font-weight: bold;
    }
    .product-card {
        background: #f8f9fa; border-radius: 12px;
        padding: 0.8rem; margin: 0.5rem 0;
    }
    .price-tag { color: #e74c3c; font-size: 1.4rem; font-weight: bold; }
    .stNumberInput input { font-size: 1.4rem; height: 3.5rem; font-weight: bold; }
    .stButton > button {
        border-radius: 12px; height: 3rem;
        font-size: 1rem; font-weight: bold; width: 100%;
    }
    div[data-testid="metric-container"] {
        background: #f8f9fa; border-radius: 10px; padding: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ── セッション初期化 ──────────────────────────────────────
if "screen" not in st.session_state:
    st.session_state.screen = "scan"
if "jan" not in st.session_state:
    st.session_state.jan = ""
if "product" not in st.session_state:
    st.session_state.product = None

# ════════════════════════════════════════════════════════
# 画面1：スキャン
# ════════════════════════════════════════════════════════
if st.session_state.screen == "scan":
    st.title("📷 バーコードをスキャン")

    tab1, tab2 = st.tabs(["📷 カメラ", "⌨️ 手打ち"])

    with tab1:
        photo = st.camera_input("撮影", label_visibility="collapsed")
        if photo:
            try:
                from pyzbar import pyzbar
                barcodes = pyzbar.decode(Image.open(photo))
                if barcodes:
                    st.session_state.jan = barcodes[0].data.decode("utf-8")
                    st.session_state.screen = "result"
                    st.rerun()
                else:
                    st.warning("読み取れませんでした。もう一度試してください。")
            except Exception:
                st.warning("読み取れませんでした。手打ちで入力してください。")

    with tab2:
        jan_input = st.text_input("JANコード", placeholder="例：4901777374300", label_visibility="collapsed")
        if st.button("🔍 検索する", type="primary"):
            if jan_input:
                st.session_state.jan = jan_input
                st.session_state.screen = "result"
                st.rerun()

# ════════════════════════════════════════════════════════
# 画面2：判定
# ════════════════════════════════════════════════════════
elif st.session_state.screen == "result":

    # 商品情報を取得（まだなければ）
    if st.session_state.product is None:
        with st.spinner("🔍 検索中..."):
            try:
                res = requests.get(
                    "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
                    params={"appid": st.secrets["YAHOO_APP_ID"], "jan_code": st.session_state.jan, "results": 1},
                    timeout=5
                )
                hits = res.json().get("hits", [])
                if hits:
                    item = hits[0]
                    st.session_state.product = {
                        "name":      item.get("name", "不明"),
                        "price":     item.get("price", None),
                        "url":       item.get("url", ""),
                        "image_url": item.get("image", {}).get("medium", ""),
                        "brand":     item.get("brand", {}).get("name", ""),
                    }
                else:
                    st.session_state.product = {"name": "（商品名不明）", "price": None, "url": "", "image_url": "", "brand": ""}
            except Exception:
                st.session_state.product = {"name": "（取得失敗）", "price": None, "url": "", "image_url": "", "brand": ""}

    p = st.session_state.product

    # 商品カード
    col_img, col_info = st.columns([1, 2])
    with col_img:
        if p["image_url"]:
            st.image(p["image_url"], use_container_width=True)
    with col_info:
        st.markdown(f"**{p['name'][:35]}**")
        if p["brand"]:
            st.caption(f"🏷 {p['brand']}")
        if p["price"]:
            st.markdown(f'<span class="price-tag">¥{int(p["price"]):,}</span>', unsafe_allow_html=True)
            st.caption("Yahoo!最安値")

    st.divider()

    # 仕入れ値入力
    st.markdown("### 💴 仕入れ値")
    cost = st.number_input("仕入れ値", min_value=0, value=0, step=10, label_visibility="collapsed")

    if cost > 0:
        # 送料自動設定
        if p["price"] and int(p["price"]) < 1500:
            ship_cost, ship_name = 230, "ゆうパケット"
        else:
            ship_cost, ship_name = 750, "らくらく60"

        # 売値を相場から推定
        if p["price"] and int(p["price"]) > 0:
            sell = round(int(p["price"]) * 0.62)
        else:
            sell = round((cost + ship_cost + 200) / (1 - 0.10) / (1 - 0.20))

        profit      = sell - cost - ship_cost - round(sell * 0.10) - 200
        profit_rate = round(profit / sell * 100, 1) if sell > 0 else 0

        # 大きな判定表示
        if profit >= 800 and profit_rate >= 20:
            st.markdown(f'<div class="verdict-buy">✅ 買い！<br><small style="font-size:1rem">推定 ¥{profit:,} 利益</small></div>', unsafe_allow_html=True)
        elif profit >= 200 and profit_rate >= 8:
            st.markdown(f'<div class="verdict-maybe">🤔 検討あり<br><small style="font-size:1rem">推定 ¥{profit:,} 利益</small></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-bad">❌ やめとこう<br><small style="font-size:1rem">推定 ¥{profit:,}</small></div>', unsafe_allow_html=True)

        st.caption(f"推定売値 ¥{sell:,}　送料 {ship_name}（¥{ship_cost}）で計算")

        # 詳細ボタン
        if st.button("📊 詳細を見る"):
            st.session_state.screen = "detail"
            st.session_state.cost = cost
            st.session_state.sell = sell
            st.session_state.ship_cost = ship_cost
            st.rerun()

    if st.button("🔄 別の商品を検索"):
        st.session_state.screen = "scan"
        st.session_state.product = None
        st.session_state.jan = ""
        st.rerun()

# ════════════════════════════════════════════════════════
# 画面3：詳細
# ════════════════════════════════════════════════════════
elif st.session_state.screen == "detail":
    p         = st.session_state.product
    cost      = st.session_state.get("cost", 500)
    sell      = st.session_state.get("sell", 2000)
    ship_cost = st.session_state.get("ship_cost", 750)

    st.title("📊 詳細計算")

    sell2 = st.number_input("売値（円）", min_value=0, value=sell, step=10)
    ship2 = st.selectbox("配送方法", [
        "らくらくメルカリ便 60サイズ（750円）",
        "らくらくメルカリ便 80サイズ（850円）",
        "ゆうパケット（230円）",
        "ネコポス（210円）",
    ])
    ship_map2 = {
        "らくらくメルカリ便 60サイズ（750円）": 750,
        "らくらくメルカリ便 80サイズ（850円）": 850,
        "ゆうパケット（230円）": 230,
        "ネコポス（210円）": 210,
    }
    sc2 = ship_map2[ship2]

    if p["price"] and int(p["price"]) > 0:
        ml = round(int(p["price"]) * 0.55)
        mh = round(int(p["price"]) * 0.70)
        st.info(f"📌 メルカリ推定相場：**¥{ml:,}〜¥{mh:,}**\n\n※ Yahoo!価格をもとにした目安です")

    breakeven   = round((cost + sc2 + 200) / (1 - 0.10))
    recommended = round((cost + sc2 + 200) / (1 - 0.10) / (1 - 0.20))
    c1, c2 = st.columns(2)
    c1.metric("最低売値", f"¥{breakeven:,}")
    c2.metric("おすすめ売値", f"¥{recommended:,}")

    st.markdown("**プラットフォーム別利益**")
    best_profit   = -999999
    best_platform = ""
    for name, fee_rate, transfer in [
        ("メルカリ", 0.10, 200),
        ("ラクマ", 0.06, 0),
        ("PayPayフリマ", 0.05, 0),
        ("ヤフオク", 0.10, 0),
    ]:
        pr = sell2 - cost - sc2 - round(sell2 * fee_rate) - transfer
        pr_rate = round(pr / sell2 * 100, 1) if sell2 > 0 else 0
        if pr > best_profit:
            best_profit   = pr
            best_platform = name
        c1, c2 = st.columns([2, 1])
        c1.write(f"**{name}**")
        c2.write(f"¥{pr:,}（{pr_rate}%）")

    if best_platform:
        st.success(f"✅ 最も利益が出るのは **{best_platform}**（¥{best_profit:,}）")

    if st.button("← 戻る"):
        st.session_state.screen = "result"
        st.rerun()
