import streamlit as st

st.set_page_config(page_title="状態別売値計算", page_icon="🏷️", layout="centered")

st.markdown("""
<style>
    .block-container { padding: 1.5rem 1rem 3rem; max-width: 480px; margin: auto; }
    h1 { font-size: 1.3rem !important; }
    .stButton > button { border-radius: 12px; height: 3rem; font-size: 1rem; font-weight: bold; width: 100%; }
    .stNumberInput input { font-size: 1.2rem; height: 3rem; }
    div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.8rem; }
    .condition-tip {
        background: #f0f4ff; border-radius: 12px;
        padding: 1rem; margin: 0.8rem 0;
        border-left: 4px solid #667eea;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏷️ 状態別売値計算")
st.caption("商品の状態を選ぶだけで適正売値と利益を計算します")
st.divider()

CONDITION_INFO = {
    "未使用・新品同様": {
        "rate": 0.80,
        "tip": "開封・使用の形跡がない。タグ付き・シュリンク未開封など。",
        "example": "【状態】未使用品です。購入後一度も使用しておりません。"
    },
    "良い": {
        "rate": 0.65,
        "tip": "数回使用。目立つ傷・汚れなし。丁寧に使用・保管されていた状態。",
        "example": "【状態】数回使用しましたが、目立った傷や汚れはございません。"
    },
    "可": {
        "rate": 0.45,
        "tip": "使用感あり。小傷・汚れ・日焼けなどがある状態。",
        "example": "【状態】使用感があります。小傷・汚れがございますが使用に問題ありません。"
    },
    "不可": {
        "rate": 0.25,
        "tip": "目立つ傷・破損・動作不良など。ジャンク品扱い。",
        "example": "【状態】目立つ傷・汚れがあります。現状渡しとなります。"
    },
}

col1, col2 = st.columns(2)
with col1:
    cost = st.number_input("仕入れ値（円）", min_value=0, value=0, step=10)
with col2:
    yahoo_price = st.number_input("Yahoo!最安値（円）", min_value=0, value=0, step=10)

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

st.divider()
st.markdown("### 📋 商品の状態を選んでください")

condition = st.radio(
    "状態",
    list(CONDITION_INFO.keys()),
    label_visibility="collapsed"
)

info = CONDITION_INFO[condition]

st.markdown(f'<div class="condition-tip">📌 <b>{condition}</b>とは：{info["tip"]}</div>', unsafe_allow_html=True)

if yahoo_price > 0:
    sell        = round(yahoo_price * info["rate"])
    profit      = sell - cost - ship_cost - round(sell * 0.10) - 200
    profit_rate = round(profit / sell * 100, 1) if sell > 0 else 0

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("推奨売値", f"¥{sell:,}")
    c2.metric("利益", f"¥{profit:,}")
    c3.metric("利益率", f"{profit_rate}%")

    if profit >= 800 and profit_rate >= 20:
        st.success("✅ 買い！")
    elif profit >= 200 and profit_rate >= 8:
        st.warning("🤔 検討あり")
    else:
        st.error("❌ やめとこう")

    st.divider()
    st.markdown("**📝 メルカリ出品コメント例**")
    st.code(info["example"], language=None)

else:
    st.info("Yahoo!最安値を入力すると推奨売値と利益が表示されます")
