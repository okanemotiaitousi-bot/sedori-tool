import streamlit as st

st.set_page_config(
    page_title="せどり目利きツール",
    page_icon="💰",
    layout="centered",
)

# 全ページ共有のsession state初期化
if "search_history" not in st.session_state:
    st.session_state.search_history = []

pg = st.navigation([
    st.Page("pages/home.py",                    title="ホーム",         icon="💰", default=True),
    st.Page("pages/1_📷_バーコード検索.py",      title="バーコード検索", icon="📷"),
    st.Page("pages/2_🔍_手動検索.py",            title="手動検索",       icon="🔍"),
    st.Page("pages/3_🏷️_状態別売値計算.py",     title="状態別売値計算", icon="🏷️"),
    st.Page("pages/4_📋_免責事項.py",            title="免責事項",       icon="📋"),
])
pg.run()
