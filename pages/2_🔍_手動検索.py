import streamlit as st

st.set_page_config(page_title="手動検索（スクレイピング）", page_icon="🔍", layout="centered")

st.title("🔍 手動検索")
st.caption("商品名やURLを手打ちで入力してAmazon・メルカリ等の価格を取得します")

st.warning("""
⚠️ このページはスクレイピング（自動価格取得）を使用します。
- 各サービスの利用規約によりサービスが制限される場合があります
- 個人の学習・研究目的の使用にとどめてください
""")

st.divider()
st.info("🚧 このページは現在開発中です。近日公開予定！")
