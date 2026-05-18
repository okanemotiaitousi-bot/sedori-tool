import streamlit as st
import requests
import numpy as np
from PIL import Image
from profit_calc import judge

st.set_page_config(page_title="バーコード検索", page_icon="📷", layout="centered")

st.markdown("""
<style>
    .block-container { padding: 1rem 1rem 3rem; }

    .product-card {
        background: linear-gradient(135deg, #f5f7fa, #e8ecf1);
        border-radius: 16px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    .product-name {
        font-size: 1rem;
        font-weight: bold;
        margin-bottom: 0.3rem;
    }
    .price-big {
        font-size: 1.5rem;
        font-weight: bold;
        color: #e74c3c;
    }

    .result-card {
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    .result-good  { background: #f0fff4; border-color: #2ecc71; }
    .result-warn  { background: #fffbf0; border-color: #f39c12; }
    .result-bad   { background: #fff5f5; border-color: #e74c3c; }

    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 12px;
        height: 3.5rem;
        font-size: 1.1rem;
        font-weight: bold;
        width: 100%;
    }
    .stNumberInput input { font-size: 1.2rem; height: 3rem; }
    div[data-testid="metric-container"] {
        background: white;
        border-radius: 10px;
        padding: 0.8rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

st.title("📷 バーコード検索")
st.divider()

PLATFORMS = {
    "メルカリ":      {"fee_rate": 0.10, "transfer_fee": 200},
    "ラクマ":        {"fee_rate": 0.06, "transfer_fee": 0},
    "PayPayフリマ":  {"fee_rate": 0.05, "transfer_fee": 0},
    "ヤフオク（通常）": {"fee_rate": 0.10, "transfer_fee": 0},
    "ヤフオク（プレミアム会員）": {"fee_rate": 0.088, "transfer_fee": 0},
}

def calc_by_platform(cost, sell, shipping, platform_key):
    p = PLATFORMS[platform_key]
    fee = sell * p["fee_rate"]
    transfer = p["transfer_fee"]
    profit = sell - cost - shipping - fee - transfer
    profit_rate = (profit / sell * 100) if sell > 0 else 0
    return round(profit), round(profit_rate, 1), round(fee)

def decode_barcode_from_image(pil_image):
    try:
        from pyzbar import pyzbar
        barcodes = pyzbar.decode(pil_image)
        for barcode in barcodes:
            return barcode.data.decode("utf-8")
    except Exception:
        pass
    try:
        import cv2
        img_array = np.array(pil_image.convert("RGB"))
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        detector = cv2.barcode_BarcodeDetector()
        retval, decoded_info, _, _ = detector.detectAndDecode(img_bgr)
        if retval:
            for info in decoded_info:
                if info:
                    return info
    except Exception:
        pass
    return None

# ── バーコード入力 ────────────────────────────────────────
tab1, tab2 = st.tabs(["📷 カメラで撮影", "⌨️ 手打ちで入力"])
jan = ""

with tab1:
    photo = st.camera_input("バーコードを撮影")
    if photo:
        image = Image.open(photo)
        detected = decode_barcode_from_image(image)
        if detected:
            st.success(f"✅ 読み取り成功！　{detected}")
            jan = detected
        else:
            st.warning("読み取れませんでした。もう一度撮影するか手打ちで入力してください。")

with tab2:
    jan_input = st.text_input("JANコードを入力", placeholder="例：4901777374300")
    if jan_input:
        jan = jan_input

# ── 商品検索 ──────────────────────────────────────────────
item_price = None

if jan:
    with st.spinner("🔍 検索中..."):
        try:
            app_id = st.secrets["YAHOO_APP_ID"]
            res = requests.get(
                "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
                params={"appid": app_id, "jan_code": jan, "results": 1, "sort": "-score"},
                timeout=5
            )
            data = res.json()
            if "error" in data:
                st.error(f"APIエラー：{data.get('message', data.get('error'))}")
        except Exception as e:
            st.error(f"通信エラー：{e}")
            data = {}

    hits = data.get("hits", [])

    if hits:
        item         = hits[0]
        product_name = item.get("name", "不明")
        item_price   = item.get("price", None)
        item_url     = item.get("url", "")
        image_url    = item.get("image", {}).get("medium", "")
        brand        = item.get("brand", {}).get("name", "")

        col_img, col_info = st.columns([1, 2])
        with col_img:
            if image_url:
                st.image(image_url, use_container_width=True)
        with col_info:
            st.markdown(f'<div class="product-name">{product_name}</div>', unsafe_allow_html=True)
            if brand:
                st.caption(f"🏷 {brand}")
            if item_price:
                st.markdown(f'<div class="price-big">¥{int(item_price):,}</div>', unsafe_allow_html=True)
                st.caption("Yahoo!最安値")
            if item_url:
                st.markdown(f"[Yahoo!で見る ↗]({item_url})")
    else:
        st.warning("商品が見つかりませんでした。手動で入力してください。")

    st.divider()

    # ── 仕入れ値・売値 ────────────────────────────────────
    st.subheader("💴 利益計算")

    col1, col2 = st.columns(2)
    with col1:
        cost = st.number_input("仕入れ値（円）", min_value=0, value=500, step=10)
    with col2:
        sell = st.number_input("売値（円）", min_value=0, value=2000, step=10)

    ship_name = st.selectbox("配送方法", [
        "らくらくメルカリ便 60サイズ（750円）",
        "らくらくメルカリ便 80サイズ（850円）",
        "らくらくメルカリ便 100サイズ（1,050円）",
        "ゆうパケット（230円）",
        "ネコポス（210円）",
        "手入力する",
    ])
    ship_map = {
        "らくらくメルカリ便 60サイズ（750円）": 750,
        "らくらくメルカリ便 80サイズ（850円）": 850,
        "らくらくメルカリ便 100サイズ（1,050円）": 1050,
        "ゆうパケット（230円）": 230,
        "ネコポス（210円）": 210,
        "手入力する": None,
    }
    ship_cost = ship_map[ship_name]
    if ship_cost is None:
        ship_cost = st.number_input("送料（円）", min_value=0, value=600, step=10)

    # ── 推定相場・おすすめ売値 ────────────────────────────
    if cost > 0:
        breakeven   = round((cost + ship_cost + 200) / (1 - 0.10))
        recommended = round((cost + ship_cost + 200) / (1 - 0.10) / (1 - 0.20))

        with st.container(border=True):
            st.markdown("**📌 推定相場・おすすめ売値**")

            if item_price and int(item_price) > 0:
                mercari_low  = round(int(item_price) * 0.55)
                mercari_high = round(int(item_price) * 0.70)
                st.markdown(f"**メルカリ推定相場：約{mercari_low:,}〜{mercari_high:,}円**")
                st.caption("※ Yahoo!価格をもとにした目安です")

            c1, c2 = st.columns(2)
            c1.metric("最低売値", f"{breakeven:,}円", help="これ未満だと赤字")
            c2.metric("おすすめ売値", f"{recommended:,}円", help="利益率20%の目安")

            if sell < breakeven:
                st.markdown('<div class="result-card result-bad">⚠️ <b>赤字になります！</b></div>', unsafe_allow_html=True)
            elif sell < recommended:
                st.markdown('<div class="result-card result-warn">△ <b>利益は出ますが少なめです</b></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="result-card result-good">✅ <b>十分な利益が見込めます！</b></div>', unsafe_allow_html=True)

    # ── プラットフォーム比較 ──────────────────────────────
    st.divider()
    st.subheader("🏪 プラットフォーム比較")

    selected = st.multiselect(
        "出品先を選んでください",
        list(PLATFORMS.keys()),
        default=["メルカリ", "ラクマ", "PayPayフリマ"]
    )

    if selected:
        best_profit   = -999999
        best_platform = ""

        for platform in selected:
            profit, profit_rate, fee = calc_by_platform(cost, sell, ship_cost, platform)
            verdict = judge(profit, profit_rate)
            if profit > best_profit:
                best_profit   = profit
                best_platform = platform

            css_class = "result-good" if profit >= 500 and profit_rate >= 10 else ("result-warn" if profit >= 0 else "result-bad")
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                c1.metric(platform, f"{profit:,}円", f"{profit_rate}%")
                c2.metric("手数料", f"{fee:,}円")
                c3.write("")
                c3.write(verdict)

        if best_platform:
            st.success(f"✅ 最も利益が出るのは **{best_platform}**（{best_profit:,}円）")
