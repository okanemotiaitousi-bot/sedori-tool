import streamlit as st

st.markdown("""
<style>
 .block-container { padding: 2rem 1.5rem 3rem; max-width: 480px; margin: auto; }
 .title-area { text-align: center; padding: 2rem 0 1rem; }
 .title-area .icon { font-size: 3rem; }
 .title-area h1 { font-size: 1.8rem; font-weight: bold; margin: 0.3rem 0 0.2rem; color: #1a1a2e; }
 .title-area p { font-size: 0.95rem; color: #555; margin: 0; line-height: 1.6; }
 .divider { height: 1px; background: #eee; margin: 1.5rem 0; }
 .stButton > button { border-radius: 12px; height: 3rem; font-size: 1rem; font-weight: bold; width: 100%; }
 .stNumberInput input { font-size: 1.2rem; height: 3rem; }
 div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.8rem; }
 .result-good { background:#f0fff4; border-left: 4px solid #2ecc71; border-radius:8px; padding:0.8rem; margin:0.5rem 0; }
 .result-warn { background:#fffbf0; border-left: 4px solid #f39c12; border-radius:8px; padding:0.8rem; margin:0.5rem 0; }
 .result-bad { background:#fff5f5; border-left: 4px solid #e74c3c; border-radius:8px; padding:0.8rem; margin:0.5rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-area">
 <div class="icon">💰</div>
 <h1>せどり目利きツール</h1>
 <p>店頭でバーコードをスキャンするだけで<br>仕入れ判断・利益計算・相場確認が<br>その場でできるせどり専用ツールです</p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

st.subheader("⚡ かんたん利益計算")

col1, col2 = st.columns(2)
with col1:
    cost = st.number_input("仕入れ値（円）", min_value=0, value=0, step=10)
with col2:
    sell = st.number_input("売値（円）", min_value=0, value=0, step=10)

shipping = st.selectbox("配送方法", [
    "らくらくメルカリ便 60サイズ（750円）",
    "らくらくメルカリ便 80サイズ（850円）",
    "ゆうパケット（230円）",
    "ネコポス（210円）",
])
ship_map = {
    "らくらくメルカリ便 60サイズ（750円）": 750,
    "らくらくメルカリ便 80サイズ（850円）": 850,
    "ゆうパケット（230円）": 230,
    "ネコポス（210円）": 210,
}
ship_cost = ship_map[shipping]

mercari_fee = round(sell * 0.10)
profit = sell - cost - ship_cost - mercari_fee - 200
profit_rate = round((profit / sell * 100), 1) if sell > 0 else 0

col3, col4 = st.columns(2)
col3.metric("利益", f"¥{profit:,}")
col4.metric("利益率", f"{profit_rate}%")

if profit >= 1000 and profit_rate >= 20:
    st.markdown('<div class="result-good">◎ 優良物件！買い！</div>', unsafe_allow_html=True)
elif profit >= 500 and profit_rate >= 10:
    st.markdown('<div class="result-warn">○ 悪くない。検討あり</div>', unsafe_allow_html=True)
elif profit >= 0:
    st.markdown('<div class="result-warn">△ 利益薄い。慎重に</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="result-bad">✕ 赤字。やめとこう</div>', unsafe_allow_html=True)

with st.expander("📊 詳細・おすすめ売値を見る"):
    breakeven = round((cost + ship_cost + 200) / (1 - 0.10))
    recommended = round((cost + ship_cost + 200) / (1 - 0.10) / (1 - 0.20))
    c1, c2 = st.columns(2)
    c1.metric("最低売値（損益分岐点）", f"¥{breakeven:,}")
    c2.metric("おすすめ売値（利益率20%）", f"¥{recommended:,}")

    st.markdown("**プラットフォーム別利益**")
    best_profit = -999999
    best_platform = ""
    for name, fee_rate, transfer in [
        ("メルカリ", 0.10, 200),
        ("ラクマ", 0.06, 0),
        ("PayPayフリマ", 0.05, 0),
        ("ヤフオク", 0.10, 0),
    ]:
        pr = sell - cost - ship_cost - round(sell * fee_rate) - transfer
        pr_rate = round(pr / sell * 100, 1) if sell > 0 else 0
        if pr > best_profit:
            best_profit = pr
            best_platform = name
        c1, c2 = st.columns([2, 1])
        c1.write(f"**{name}**")
        c2.write(f"¥{pr:,}（{pr_rate}%）")
    if best_platform:
        st.success(f"✅ 最も利益が出るのは **{best_platform}**（¥{best_profit:,}）")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.caption("バーコードスキャン・複数サイト比較は左メニューの「バーコード検索」から")
