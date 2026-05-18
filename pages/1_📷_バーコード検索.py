import streamlit as st
import requests
from profit_calc import judge

st.set_page_config(page_title="バーコード検索", page_icon="📷", layout="centered")

st.title("📷 バーコード検索")
st.caption("JAN コードを入力して商品の相場と利益をチェック（スクレイピングなし・安全）")
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

# ── JAN コード入力 ──────────────────────────────────────────
jan = st.text_input("JAN コードを入力（バーコードの数字）", placeholder="例：4901777374300")

if jan:
    with st.spinner("商品情報を検索中..."):
        try:
            res = requests.get(
                f"https://api.upcitemdb.com/prod/trial/lookup?upc={jan}",
                timeout=5
            )
            data = res.json()
        except Exception:
            data = {}

    items = data.get("items", [])

    if items:
        item = items[0]
        product_name = item.get("title", "不明")
        brand        = item.get("brand", "不明")
        description  = item.get("description", "")
        images       = item.get("images", [])
        amazon_price = item.get("lowest_recorded_price", None)

        st.success("商品が見つかりました！")
        col_img, col_info = st.columns([1, 2])

        with col_img:
            if images:
                st.image(images[0], width=150)

        with col_info:
            st.subheader(product_name)
            st.write(f"ブランド：{brand}")
            if amazon_price:
                st.write(f"参考最安値：**${amazon_price}**")
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
