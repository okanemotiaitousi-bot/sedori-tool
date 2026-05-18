import hashlib
import streamlit as st
import google.generativeai as genai
from PIL import Image
from utils import show_auction_prices, fetch_yahoo_lowest_price


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
 .ai-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white; border-radius: 8px;
  padding: 0.3rem 0.7rem; font-size: 0.8rem;
  display: inline-block; margin-bottom: 0.5rem;
 }
 .photo-badge {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: white; border-radius: 8px;
  padding: 0.3rem 0.7rem; font-size: 0.8rem;
  display: inline-block; margin-bottom: 0.5rem;
 }
</style>
""", unsafe_allow_html=True)

st.title("🏷️ 状態別売値計算")
st.caption("写真 or 説明文でAIが状態を判定 → 適正売値と利益を計算します")
st.divider()

CONDITION_INFO = {
    "未使用・新品同様": {
        "rate": 0.80,
        "tip": "開封・使用の形跡がない。タグ付き・シュリンク未開封など。",
        "example": "【状態】未使用品です。購入後一度も使用しておりません。",
    },
    "良い": {
        "rate": 0.65,
        "tip": "数回使用。目立つ傷・汚れなし。丁寧に使用・保管されていた状態。",
        "example": "【状態】数回使用しましたが、目立った傷や汚れはございません。",
    },
    "可": {
        "rate": 0.45,
        "tip": "使用感あり。小傷・汚れ・日焼けなどがある状態。",
        "example": "【状態】使用感があります。小傷・汚れがございますが使用に問題ありません。",
    },
    "不可": {
        "rate": 0.25,
        "tip": "目立つ傷・破損・動作不良など。ジャンク品扱い。",
        "example": "【状態】目立つ傷・汚れがあります。現状渡しとなります。",
    },
}

# ── 入力欄 ─────────────────────────────────────────────
col_name, col_btn = st.columns([3, 1])
with col_name:
    product_name = st.text_input(
        "商品名",
        placeholder="例：ニンテンドースイッチ　有機EL",
        key="condition_product_name",
    )
with col_btn:
    st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    if st.button("🔍 価格取得", key="fetch_price_btn", use_container_width=True):
        if product_name.strip():
            with st.spinner("検索中..."):
                price = fetch_yahoo_lowest_price(product_name.strip(), st.secrets["YAHOO_APP_ID"])
            if price:
                st.session_state.condition_yahoo_price = price
                st.rerun()
            else:
                st.warning("価格を取得できませんでした")
        else:
            st.warning("商品名を入力してください")

col1, col2 = st.columns(2)
with col1:
    cost = st.number_input("仕入れ値（円）", min_value=0, value=0, step=10)
with col2:
    yahoo_price = st.number_input(
        "Yahoo!最安値（円）",
        min_value=0,
        step=10,
        key="condition_yahoo_price",
    )

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

# ── セッション初期化 ───────────────────────────────────
for key, default in [
    ("auto_condition", None),
    ("used_ai", False),
    ("ai_method", None),
    ("last_description", ""),
    ("last_photo_hash", ""),
    ("condition_yahoo_price", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── AI判定関数 ─────────────────────────────────────────
def keyword_guess(text: str):
    t = text.lower()
    if any(w in t for w in ["未使用", "新品", "未開封", "デッドストック", "新品同様"]):
        return "未使用・新品同様"
    if any(w in t for w in ["ジャンク", "動作不良", "不動", "破損", "割れ", "欠品", "難あり"]):
        return "不可"
    if any(w in t for w in ["傷あり", "汚れあり", "使用感", "使用済み", "やや", "若干"]):
        return "可"
    if any(w in t for w in ["美品", "綺麗", "良好", "目立つ傷なし", "ほぼ", "きれい"]):
        return "良い"
    return None


def gemini_text_guess(text: str):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""以下のメルカリ商品説明文を読んで、商品の状態を判定してください。
「未使用・新品同様」「良い」「可」「不可」の4つのどれか1つだけ答えてください。
余計な説明は不要です。状態名だけ答えてください。

商品説明：
{text}"""
        response = model.generate_content(prompt)
        result = response.text.strip()
        for cond in CONDITION_INFO.keys():
            if cond in result:
                return cond
        return None
    except Exception:
        return None


def gemini_vision_guess(photo):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")
        img = Image.open(photo)
        prompt = """この商品の画像を見て、メルカリで出品する場合の状態を判定してください。
傷・汚れ・使用感の有無をよく確認してください。
「未使用・新品同様」「良い」「可」「不可」の4つのどれか1つだけ答えてください。
余計な説明は一切不要です。4択の状態名だけを答えてください。"""
        response = model.generate_content([prompt, img])
        result = response.text.strip()
        for cond in CONDITION_INFO.keys():
            if cond in result:
                return cond
        return None
    except Exception:
        return None


# ════════════════════════════════════════════════════════
# 状態判定タブ
# ════════════════════════════════════════════════════════
st.markdown("### 🔍 状態の判定方法を選んでください")
tab_photo, tab_text = st.tabs(["📷 写真で判定（おすすめ）", "📝 説明文で判定"])

# ── 写真タブ ──────────────────────────────────────────
with tab_photo:
    st.caption("商品をカメラで撮影するだけで、AIが状態を自動判定します")

    photo = st.camera_input("撮影", label_visibility="collapsed", key="condition_camera")

    if photo is not None:
        photo_hash = hashlib.md5(photo.getvalue()).hexdigest()
        if photo_hash != st.session_state.last_photo_hash:
            st.session_state.last_photo_hash = photo_hash
            with st.spinner("🤖 AIが写真を解析中..."):
                result = gemini_vision_guess(photo)
            if result:
                st.session_state.auto_condition = result
                st.session_state.used_ai = True
                st.session_state.ai_method = "photo"
            else:
                st.warning("写真から判定できませんでした。説明文タブか手動選択を使ってください。")

    if st.session_state.ai_method == "photo" and st.session_state.auto_condition:
        st.markdown('<span class="photo-badge">📷 AIが写真から判定</span>', unsafe_allow_html=True)
        st.success(f"「**{st.session_state.auto_condition}**」と判定しました")

# ── 説明文タブ ────────────────────────────────────────
with tab_text:
    st.caption("商品説明文を貼り付けると、AIが状態を自動判定します")

    description_input = st.text_area(
        "商品の説明文",
        placeholder="例：動作確認済み　傷・汚れあり　付属品なし　ジャンク",
        height=90,
        label_visibility="collapsed",
        key="description_input",
    )

    if description_input and description_input != st.session_state.last_description:
        with st.spinner("🤖 AIが状態を判定中..."):
            result = gemini_text_guess(description_input)
            if result:
                st.session_state.auto_condition = result
                st.session_state.used_ai = True
            else:
                auto_kw = keyword_guess(description_input)
                st.session_state.auto_condition = auto_kw
                st.session_state.used_ai = False
            st.session_state.ai_method = "text"
        st.session_state.last_description = description_input

    if description_input:
        if st.session_state.auto_condition and st.session_state.ai_method == "text":
            label = "🤖 AIが判定" if st.session_state.used_ai else "🔍 キーワード判定"
            st.markdown(f'<span class="ai-badge">{label}</span>', unsafe_allow_html=True)
            st.success(f"「**{st.session_state.auto_condition}**」と判定しました")
        elif st.session_state.ai_method == "text":
            st.warning("判定できませんでした。下から手動で選んでください。")

# ════════════════════════════════════════════════════════
# 状態選択・計算結果
# ════════════════════════════════════════════════════════
st.markdown("### 📋 商品の状態を選んでください")

default_index = list(CONDITION_INFO.keys()).index(st.session_state.auto_condition) \
    if st.session_state.auto_condition else 0

condition = st.radio(
    "状態",
    list(CONDITION_INFO.keys()),
    index=default_index,
    label_visibility="collapsed",
)

info = CONDITION_INFO[condition]
st.markdown(
    f'<div class="condition-tip">📌 <strong>{condition}</strong> とは：{info["tip"]}</div>',
    unsafe_allow_html=True,
)

# ── 計算結果 ────────────────────────────────────────────
if yahoo_price > 0:
    sell = round(yahoo_price * info["rate"])
    profit = sell - cost - ship_cost - round(sell * 0.10) - 200
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

    # ── ヤフオク落札相場 ────────────────────────────
    search_query = product_name.strip() or st.session_state.get("last_description", "").strip()
    if search_query:
        with st.expander("📦 ヤフオク落札相場を見る"):
            cache_key = search_query[:40]
            show_auction_prices(search_query, cache_key)
            auction_data = st.session_state.get(f"_auction_{cache_key}")
            if auction_data:
                diff = auction_data["avg"] - yahoo_price
                if diff > 0:
                    st.info(f"📊 ヤフオク平均はYahoo!より **¥{diff:,} 高め** → 相場は強い")
                elif diff < 0:
                    st.warning(f"📊 ヤフオク平均はYahoo!より **¥{abs(diff):,} 安め** → 相場は弱い")
                else:
                    st.caption("📊 ヤフオク平均とYahoo!価格がほぼ同じです")

    st.divider()
    st.markdown("**📝 メルカリ出品コメント例**")
    st.code(info["example"], language=None)

else:
    st.info("Yahoo!最安値を入力すると推奨売値と利益が表示されます")
