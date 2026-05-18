import streamlit as st
import requests
import numpy as np
from PIL import Image
from profit_calc import judge

st.set_page_config(page_title="バーコード検索", page_icon="📷", layout="centered")

st.title("📷 バーコード検索")
st.caption("JAN コードを入力または撮影して商品の相場と利益をチェック（スクレイピングなし・安全）")
st.divider()

# ── プラットフォームごとの手数料設定 ──────────────────────────
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
    """画像からバーコードを読み取る"""
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

# ── バーコード入力（カメラ or 手打ち） ───────────────────────
tab1, tab2 = st.tabs(["📷 カメラで撮影", "⌨️ 手打ちで入力"])

jan = ""

with tab1:
    st.info("バーコードをカメラで撮影してください。スマホの場合はそのままカメラが起動します。")
    photo = st.camera_input("バーコードを撮影")

    if photo:
        image = Image.open(photo)
        detected = decode_barcode_from_image(image)

        if detected:
            st.success(f"読み取り成功！JAN コード：{detected}")
            jan = detected
        else:
            st.warning("バーコードを読み取れませんでした。バーコードに近づけて再撮影するか、手打ちで入力してください。")

with tab2:
    jan_input = st.text_input("JAN コードを入力（バーコードの数字）", placeholder="例：4901777374300")
    if jan_input:
        jan = jan_input

# ── 商品検索 ─────────────────────────────────────────────────
if jan:
    with st.spinner("商品情報を検索中..."):
        try:
            app_id = st.secrets["YAHOO_APP_ID"]
            res = requests.get(
                "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
                params={
                    "appid": app_id,
                    "jan_code": jan,
                    "results": 1,
                    "sort": "-score",
                },
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
        item = hits[0]
        product_name = item.get("name", "不明")
        item_price   = item.get("price", None)
        item_url     = item.get("url", "")
        image_url    = item.get("image", {}).get("medium", "")
        description  = item.get("description", "")
        brand        = item.get("brand", {}).get("name", "")

        st.success("商品が見つかりました！")
        col_img, col_info = st.columns([1, 2])

        with col_img:
            if image_url:
                st.image(image_url, width=150)

        with col_info:
            st.subheader(product_name)
            if brand:
                st.write(f"ブランド：{brand}")
            if item_price:
                st.write(f"Yahoo!最安値：**{int(item_price):,}円**")
            if item_url:
                st.markdown(f"[Yahoo!ショッピングで見る]({item_url})")
            if description:
                st.caption(description[:100] + "...")
    else:
        product_name = "（商品名不明）"
        st.warning("商品情報が見つかりませんでした。手動で入力してください。")

    st.divider()

    # ── 仕入れ値・送料・売値 入力 ──────────────────────────
    st.subheader("💴 利益計算")

    col1, col2 = st.columns(2)
    with col1:
        cost = st.number_input("仕入れ値（円）", min_value=0, value=500, step=10)
    with col2:
        sell = st.number_input("売値（円）", min_value=0, value=2000, step=10)


    shipping_options = {
        "らくらくメルカリ便 60サイズ": 750,
        "らくらくメルカリ便 80サイズ": 850,
        "らくらくメルカリ便 100サイズ": 1050,
        "ゆうパケット（〜3cm）": 230,
        "ネコポス（〜2.5cm）": 210,
        "手入力する": None,
    }
    ship_name = st.selectbox("送料（配送方法）", list(shipping_options.keys()))
    ship_cost = shipping_options[ship_name]
    if ship_cost is None:
        ship_cost = st.number_input("送料を入力（円）", min_value=0, value=600, step=10)

    # ── おすすめ売値を自動計算して表示（送料込み） ──────────
    if cost > 0:
        with st.container(border=True):
            st.markdown("**📌 おすすめ売値（メルカリ基準・送料込み）**")
            breakeven   = round((cost + ship_cost + 200) / (1 - 0.10))
            recommended = round((cost + ship_cost + 200) / (1 - 0.10) / (1 - 0.20))

            c1, c2 = st.columns(2)
            c1.metric("損益分岐点（最低売値）", f"{breakeven:,}円", help="これ以上で売れば赤字にならない最低ライン")
            c2.metric("利益率20%のおすすめ売値", f"{recommended:,}円", help="しっかり利益を出すための目安")

            if sell < breakeven:
                st.error("⚠️ 今の売値では赤字になります！")
            elif sell < recommended:
                st.warning("△ 利益は出ますが少なめです。もう少し高く売れると良いです。")
            else:
                st.success("✅ 十分な利益が見込めます！")

    # ── プラットフォーム選択 ──────────────────────────────
    st.subheader("🏪 出品先プラットフォームを選択")
    selected = st.multiselect(
        "比較したいサービスを選んでください",
        list(PLATFORMS.keys()),
        default=["メルカリ", "ラクマ", "PayPayフリマ"]
    )

    if selected:
        st.divider()
        st.subheader("📊 比較結果")

        best_profit = -999999
        best_platform = ""

        for platform in selected:
            profit, profit_rate, fee = calc_by_platform(cost, sell, ship_cost, platform)
            verdict = judge(profit, profit_rate)

            if profit > best_profit:
                best_profit = profit
                best_platform = platform

            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                c1.metric(platform, f"{profit:,}円", f"利益率 {profit_rate}%")
                c2.metric("手数料", f"{fee:,}円")
                c3.write("")
                c3.write(verdict)

        if best_platform:
            st.success(f"✅ 一番利益が出るのは **{best_platform}** です！（{best_profit:,}円）")
