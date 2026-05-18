import streamlit as st
from profit_calc import calculate_profit, judge

st.set_page_config(
    page_title="せどり利益計算ツール",
    page_icon="💰",
    layout="centered"
)

st.title("💰 せどり利益計算ツール")
st.caption("店舗で即チェック！送料・手数料込みの利益を自動計算")

st.divider()

col1, col2 = st.columns(2)

with col1:
    cost_price = st.number_input("仕入れ値（円）", min_value=0, value=500, step=10)

with col2:
    sell_price = st.number_input("売値（円）", min_value=0, value=2000, step=10)

shipping_options = {
    "らくらくメルカリ便 60サイズ": 750,
    "らくらくメルカリ便 80サイズ": 850,
    "らくらくメルカリ便 100サイズ": 1050,
    "ゆうパケット（〜3cm）": 230,
    "ネコポス（〜2.5cm）": 210,
    "手入力する": None,
}

shipping_name = st.selectbox("送料（配送方法）", list(shipping_options.keys()))
shipping_cost = shipping_options[shipping_name]

if shipping_cost is None:
    shipping_cost = st.number_input("送料を入力（円）", min_value=0, value=600, step=10)

st.divider()

result = calculate_profit(cost_price, sell_price, shipping_cost)
verdict = judge(result["利益"], result["利益率"])

profit = result["利益"]
profit_rate = result["利益率"]

if profit >= 1000 and profit_rate >= 20:
    color = "🟢"
    box_color = "success"
elif profit >= 500 and profit_rate >= 10:
    color = "🟡"
    box_color = "warning"
elif profit >= 0:
    color = "🟠"
    box_color = "warning"
else:
    color = "🔴"
    box_color = "error"

if box_color == "success":
    st.success(f"判定　{color} {verdict}")
elif box_color == "error":
    st.error(f"判定　{color} {verdict}")
else:
    st.warning(f"判定　{color} {verdict}")

col3, col4 = st.columns(2)

with col3:
    st.metric("利益", f"{profit:,}円")

with col4:
    st.metric("利益率", f"{profit_rate}%")

with st.expander("内訳を見る"):
    st.write(f"- 売値：{result['売値']:,}円")
    st.write(f"- 仕入れ値：{result['仕入れ値']:,}円")
    st.write(f"- 送料（{shipping_name}）：{result['送料']:,}円")
    st.write(f"- メルカリ手数料（10%）：{result['メルカリ手数料']:,}円")
    st.write(f"- 振込手数料：{result['振込手数料']:,}円")
