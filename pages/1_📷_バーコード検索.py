import streamlit as st
import requests
import numpy as np
from PIL import Image
from profit_calc import judge

st.set_page_config(page_title="せどり目利きツール", page_icon="📷", layout="centered")

st.markdown("""
<style>
    .block-container { padding: 1rem 1rem 3rem; max-width: 480px; margin: auto; }

    .verdict-buy {
        background: linear-gradient(135deg, #2ecc71, #27ae60);
        color: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .verdict-maybe {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .verdict-bad {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .product-box {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.8rem 0;
        display: flex;
        gap: 0.8rem;
        align-items: center;
    }
    .price-red { color: #e74c3c; font-size: 1.3rem; font-weight: bold; }
    div[data-testid="metric-container"] {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.8rem;
    }
    .stNumberInput input { font-size: 1.4rem; height: 3.5rem; font-weight: bold; }
    h1 { font-size: 1.3rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("📷 せどり目利きツール")

# ── バーコード入力 ────────────────────────────────────────
tab1, tab2 = st.tabs(["📷 カメラ", "⌨️ 手打ち"])
jan = ""

with tab1:
    photo = st.camera_input("バーコードを撮影", label_visibility="collapsed")
    if photo:
        from pyzbar import pyzbar as _pyzbar
        try:
            barcodes = _pyzbar.decode(Image.open(photo))
            if barcodes:
                jan = barcodes[0].data.decode("utf-8")
                st.success(f"✅ {jan}")
            else:
                st.warning("読み取れませんでした。もう一度試すか手打ちで入力してください。")
        except Exception:
            st.warning("読み取れませんでした。手打ちで入力してください。")

with tab2:
    jan_input = st.text_input("JANコード", placeholder="例：4901777374300", label_visibility="collapsed")
    if jan_input:
        jan = jan_input

# ── 商品検索 ──────────────────────────────────────────────
item_price = None
product_name = ""

if jan:
    with st.spinner("🔍 検索中..."):
        try:
            res = requests.get(
                "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
                params={"appid": st.secrets["YAHOO_APP_ID"], "jan_code": jan, "results": 1},
                timeout=5
            )
            data = res.json()
        except Exception:
            data = {}

    hits = data.get("hits", [])
    if hits:
        item         = hits[0]
        product_name = item.get("name", "")
        item_price   = item.get("price", None)
        item_url     = item.get("url", "")
        image_url    = item.get("image", {}).get("medium", "")
        brand        = item.get("brand", {}).get("name", "")

        col_img, col_info = st.columns([1, 2])
        with col_img:
            if image_url:
                st.image(image_url, use_container_width=True)
        with col_info:
            st.markdown(f"**{product_name[:40]}**")
            if brand:
                st.caption(f"🏷 {brand}")
            if item_price:
                st.markdown(f'<span class="price-red">¥{int(item_price):,}</span>', unsafe_allow_html=True)
                st.caption("Yahoo!最安値")
            if item_url:
                st.markdown(f"[Yahoo!で見る ↗]({item_url})")
    else:
        st.warning("商品が見つかりませんでした")

    st.divider()

    # ── 仕入れ値（メインの入力） ──────────────────────────
    st.markdown("### 💴 仕入れ値を入力")
    cost = st.number_input("仕入れ値（円）", min_value=0, value=500, step=10, label_visibility="collapsed")

    # 送料は自動設定（商品価格から推定）
    if item_price and int(item_price) < 1000:
        auto_ship = 210   # ネコポス
        ship_label = "ネコポス"
    elif item_price and int(item_price) < 3000:
        auto_ship = 750   # 60サイズ
        ship_label = "らくらく60"
    else:
        auto_ship = 850   # 80サイズ
        ship_label = "らくらく80"

    # ── 即時判定（メイン） ────────────────────────────────
    if cost > 0:
        breakeven   = round((cost + auto_ship + 200) / (1 - 0.10))
        recommended = round((cost + auto_ship + 200) / (1 - 0.10) / (1 - 0.20))

        if item_price:
            sell = round(int(item_price) * 0.62)
        else:
            sell = recommended

        profit      = sell - cost - auto_ship - round(sell * 0.10) - 200
        profit_rate = round((profit / sell * 100), 1) if sell > 0 else 0

        if profit >= 800 and profit_rate >= 20:
            st.markdown(f'<div class="verdict-buy">✅ 買い！<br><small>推定利益 ¥{profit:,}</small></div>', unsafe_allow_html=True)
        elif profit >= 300 and profit_rate >= 10:
            st.markdown(f'<div class="verdict-maybe">🤔 検討あり<br><small>推定利益 ¥{profit:,}</small></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-bad">❌ やめとこう<br><small>推定利益 ¥{profit:,}</small></div>', unsafe_allow_html=True)

        st.caption(f"※ 売値：¥{sell:,}（推定）　送料：{ship_label}（¥{auto_ship}）で計算")

        # ── 詳細（折りたたみ） ────────────────────────────
        with st.expander("📊 詳細・売値を変更する"):
            sell2 = st.number_input("売値（円）", min_value=0, value=sell, step=10)
            ship_name = st.selectbox("配送方法", [
                f"{ship_label}（自動・¥{auto_ship}）",
                "らくらくメルカリ便 60サイズ（750円）",
                "らくらくメルカリ便 80サイズ（850円）",
                "らくらくメルカリ便 100サイズ（1,050円）",
                "ゆうパケット（230円）",
                "ネコポス（210円）",
            ])
            ship_map = {
                f"{ship_label}（自動・¥{auto_ship}）": auto_ship,
                "らくらくメルカリ便 60サイズ（750円）": 750,
                "らくらくメルカリ便 80サイズ（850円）": 850,
                "らくらくメルカリ便 100サイズ（1,050円）": 1050,
                "ゆうパケット（230円）": 230,
                "ネコポス（210円）": 210,
            }
            ship2 = ship_map[ship_name]

            if item_price and int(item_price) > 0:
                mercari_low  = round(int(item_price) * 0.55)
                mercari_high = round(int(item_price) * 0.70)
                st.info(f"📌 メルカリ推定相場：**¥{mercari_low:,}〜¥{mercari_high:,}**\n\n※ Yahoo!価格をもとにした目安です")

            c1, c2 = st.columns(2)
            c1.metric("最低売値", f"¥{breakeven:,}")
            c2.metric("おすすめ売値", f"¥{recommended:,}")

            st.markdown("**プラットフォーム別利益**")
            platforms = {
                "メルカリ":     {"fee_rate": 0.10, "transfer_fee": 200},
                "ラクマ":       {"fee_rate": 0.06, "transfer_fee": 0},
                "PayPayフリマ": {"fee_rate": 0.05, "transfer_fee": 0},
                "ヤフオク":     {"fee_rate": 0.10, "transfer_fee": 0},
            }
            best_p = -999999
            best_n = ""
            for name, p in platforms.items():
                pr = sell2 - cost - ship2 - round(sell2 * p["fee_rate"]) - p["transfer_fee"]
                pr_rate = round(pr / sell2 * 100, 1) if sell2 > 0 else 0
                if pr > best_p:
                    best_p = pr
                    best_n = name
                c1, c2 = st.columns([2, 1])
                c1.write(f"**{name}**")
                c2.write(f"¥{pr:,}（{pr_rate}%）")
            if best_n:
                st.success(f"✅ 最も利益：**{best_n}**（¥{best_p:,}）")
