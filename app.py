import streamlit as st

st.set_page_config(
    page_title="せどり目利きツール",
    page_icon="💰",
    layout="centered"
)

st.markdown("""
<style>
    .block-container { padding: 1.5rem 1rem 3rem; }
    
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2rem 1.5rem;
        text-align: center;
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 { font-size: 2rem; margin: 0 0 0.5rem; }
    .hero p  { font-size: 1rem; margin: 0; opacity: 0.9; }

    .feature-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .feature-icon { font-size: 2rem; }
    .feature-text h3 { margin: 0 0 0.2rem; font-size: 1rem; }
    .feature-text p  { margin: 0; font-size: 0.85rem; color: #666; }

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
    
    .calc-box {
        background: #f8f9ff;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── ヒーロー ──────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>💰 せどり目利きツール</h1>
    <p>バーコードをスキャンするだけで<br>利益が一瞬でわかる</p>
</div>
""", unsafe_allow_html=True)

# ── 機能紹介 ──────────────────────────────────────────────
st.markdown("""
<div class="feature-card">
    <div class="feature-icon">📷</div>
    <div class="feature-text">
        <h3>バーコードスキャン</h3>
        <p>JANコードを読み取って商品情報を自動取得</p>
    </div>
</div>
<div class="feature-card">
    <div class="feature-icon">📊</div>
    <div class="feature-text">
        <h3>複数サイト一括比較</h3>
        <p>メルカリ・ラクマ・ヤフオク・PayPayフリマの利益を同時計算</p>
    </div>
</div>
<div class="feature-card">
    <div class="feature-icon">💡</div>
    <div class="feature-text">
        <h3>おすすめ売値を提案</h3>
        <p>Yahoo!相場から推定したメルカリ相場とおすすめ売値を表示</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── かんたん利益計算 ──────────────────────────────────────
st.subheader("⚡ かんたん利益計算")
st.caption("バーコードなしで素早く計算したいときに")

col1, col2 = st.columns(2)
with col1:
    cost = st.number_input("仕入れ値（円）", min_value=0, value=500, step=10)
with col2:
    sell = st.number_input("売値（円）", min_value=0, value=2000, step=10)

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
profit      = sell - cost - ship_cost - mercari_fee - 200
profit_rate = round((profit / sell * 100), 1) if sell > 0 else 0

st.markdown('<div class="calc-box">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
c1.metric("利益", f"{profit:,}円")
c2.metric("利益率", f"{profit_rate}%")

if profit >= 1000 and profit_rate >= 20:
    st.success("◎ 優良物件！買い！")
elif profit >= 500 and profit_rate >= 10:
    st.warning("○ 悪くない。検討あり")
elif profit >= 0:
    st.warning("△ 利益薄い。慎重に")
else:
    st.error("✕ 赤字。やめとこう")
st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("バーコードスキャン・詳細な利益計算は左のメニューから「バーコード検索」を開いてください")
