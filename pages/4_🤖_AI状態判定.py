import streamlit as st
import base64
import requests

st.set_page_config(page_title="AI状態判定", page_icon="🤖", layout="centered")

st.markdown("""
<style>
    .block-container { padding: 1.5rem 1rem 3rem; max-width: 480px; margin: auto; }
    h1 { font-size: 1.3rem !important; }
    .stButton > button { border-radius: 12px; height: 3rem; font-size: 1rem; font-weight: bold; width: 100%; }
    .stNumberInput input { font-size: 1.2rem; height: 3rem; }
    div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.8rem; }
    .condition-box {
        background: #f0f4ff; border-radius: 12px;
        padding: 1rem; margin: 0.8rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI状態判定")
st.caption("商品の写真を撮るだけでAIが状態を判定して売値を提案します")
st.divider()

CONDITION_RATE = {
    "未使用・新品同様": 0.80,
    "良い":             0.65,
    "可":               0.45,
    "不可":             0.25,
}

col1, col2 = st.columns(2)
with col1:
    cost = st.number_input("仕入れ値（円）", min_value=0, value=0, step=10)
with col2:
    yahoo_price = st.number_input("Yahoo!最安値（円）※わかれば", min_value=0, value=0, step=10)

photo = st.camera_input("商品の写真を撮影してください")

if photo and st.button("🤖 AIで状態を判定する", type="primary"):
    with st.spinner("AIが状態を分析中...（5〜10秒かかります）"):
        try:
            image_data = base64.b64encode(photo.getvalue()).decode("utf-8")
            api_key    = st.secrets["GEMINI_API_KEY"]

            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": """この商品の写真を見て以下の形式で回答してください。

【状態】以下の4つから1つだけ選んでください：
- 未使用・新品同様
- 良い
- 可
- 不可

【状態の理由】外観・傷・汚れ・劣化などを50文字以内で

【メルカリ出品時のコメント案】買い手に伝えるべき状態説明を1〜2文で

必ずこの形式を守って回答してください。"""
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }]
            }

            res     = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                json=payload,
                timeout=30
            )
            data = res.json()
            if "candidates" in data:
                result = data["candidates"][0]["content"]["parts"][0]["text"]
                st.session_state["ai_result"] = result
            else:
                st.error(f"APIエラー：{data.get('error', {}).get('message', str(data))}")

        except Exception as e:
            st.error(f"エラーが発生しました：{e}")

if "ai_result" in st.session_state:
    result = st.session_state["ai_result"]

    st.markdown('<div class="condition-box">', unsafe_allow_html=True)
    st.markdown(result)
    st.markdown('</div>', unsafe_allow_html=True)

    condition = None
    for c in CONDITION_RATE:
        if c in result:
            condition = c
            break

    if condition and yahoo_price > 0:
        rate        = CONDITION_RATE[condition]
        sell        = round(yahoo_price * rate)
        ship        = 750
        profit      = sell - cost - ship - round(sell * 0.10) - 200
        profit_rate = round(profit / sell * 100, 1) if sell > 0 else 0

        st.divider()
        st.markdown(f"**📌 状態：{condition}（Yahoo!価格の{int(rate*100)}%）**")

        c1, c2 = st.columns(2)
        c1.metric("推奨売値", f"¥{sell:,}")
        c2.metric("推定利益", f"¥{profit:,}（{profit_rate}%）")

        if profit >= 800 and profit_rate >= 20:
            st.success("✅ 買い！")
        elif profit >= 200 and profit_rate >= 8:
            st.warning("🤔 検討あり")
        else:
            st.error("❌ やめとこう")

    elif condition and yahoo_price == 0:
        st.info(f"状態：**{condition}**\n\nYahoo!最安値を入力すると推奨売値も計算できます。")

    if st.button("🔄 別の商品を判定する"):
        del st.session_state["ai_result"]
        st.rerun()
