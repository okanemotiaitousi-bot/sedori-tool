import streamlit as st
from datetime import datetime
import sheets as gs

st.markdown("""
<style>
 .block-container {
  padding-top: 0 !important;
  padding-bottom: 3rem !important;
  max-width: 480px !important;
  margin: 0 auto !important;
 }

 /* ヒーローバナー：左右パディングを打ち消して端まで伸ばす */
 .hero {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: white;
  padding: 2.5rem 1.5rem 2rem;
  text-align: center;
  margin: 0 -1rem 1.5rem;
 }
 .hero .badge {
  background: rgba(255,255,255,0.15);
  border-radius: 20px;
  padding: 0.2rem 0.8rem;
  font-size: 0.75rem;
  display: inline-block;
  margin-bottom: 0.8rem;
  letter-spacing: 0.05em;
 }
 .hero h1 {
  font-size: 1.9rem !important;
  font-weight: 900;
  margin: 0.2rem 0 0.5rem;
  letter-spacing: -0.02em;
 }
 .hero p { font-size: 0.9rem; color: rgba(255,255,255,0.75); margin: 0; line-height: 1.6; }

 /* クイックアクセスボタンエリア */
 .quick-area { padding: 0 1rem; margin-bottom: 1.2rem; }

 /* 計算カード */
 .calc-area { padding: 0 1rem; }

 /* 判定バナー */
 .verdict-buy {
  background: linear-gradient(135deg, #2ecc71, #27ae60);
  color: white; border-radius: 16px; padding: 1.5rem 1rem;
  text-align: center; margin: 0.8rem 0;
 }
 .verdict-maybe {
  background: linear-gradient(135deg, #f39c12, #e67e22);
  color: white; border-radius: 16px; padding: 1.5rem 1rem;
  text-align: center; margin: 0.8rem 0;
 }
 .verdict-bad {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  color: white; border-radius: 16px; padding: 1.5rem 1rem;
  text-align: center; margin: 0.8rem 0;
 }
 .verdict-empty {
  background: #f1f3f5; border-radius: 16px; padding: 1.5rem 1rem;
  text-align: center; margin: 0.8rem 0; color: #aaa;
 }
 .verdict-title { font-size: 1.8rem; font-weight: 900; }
 .verdict-sub { font-size: 0.9rem; margin-top: 0.3rem; opacity: 0.9; }

 /* ランキング */
 .rank-area { padding: 0 1rem; margin-top: 1.5rem; }
 .rank-item {
  display: flex; align-items: center; gap: 0.7rem;
  background: #f8f9fa; border-radius: 10px;
  padding: 0.7rem 0.9rem; margin-bottom: 0.5rem;
  font-size: 0.9rem;
 }
 .rank-badge { font-size: 1.3rem; width: 1.6rem; text-align: center; flex-shrink: 0; }
 .rank-name { flex: 1; font-weight: 600; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
 .rank-profit { font-weight: bold; white-space: nowrap; }
 .rank-rate { color: #888; font-size: 0.78rem; white-space: nowrap; }

 /* 履歴カード */
 .history-area { padding: 0 1rem; margin-top: 1.5rem; }
 .history-item {
  display: flex; align-items: center; gap: 0.6rem;
  background: #f8f9fa; border-radius: 10px;
  padding: 0.7rem 0.9rem; margin-bottom: 0.5rem;
  font-size: 0.9rem;
 }
 .history-item .hname { flex: 1; font-weight: 600; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
 .history-item .hprofit { font-weight: bold; white-space: nowrap; }
 .history-item .htime { color: #aaa; font-size: 0.78rem; white-space: nowrap; }
 .profit-pos { color: #2ecc71; }
 .profit-neg { color: #e74c3c; }
 .profit-mid { color: #f39c12; }

 .stButton > button { border-radius: 12px; height: 3rem; font-size: 1rem; font-weight: bold; width: 100%; }
 .stNumberInput input { font-size: 1.2rem; height: 3rem; }
 div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.8rem; }
 .section-title { font-size: 1rem; font-weight: 700; color: #333; margin: 0.5rem 0 0.8rem; padding: 0 1rem; }
</style>
""", unsafe_allow_html=True)

# ── ヒーローバナー ──────────────────────────────────────
st.markdown("""
<div class="hero">
 <div class="badge">🛒 せどり専用ツール</div>
 <h1>💰 せどり目利きツール</h1>
 <p>店頭でその場で仕入れ判断。<br>バーコードをスキャンするだけで利益が分かる。</p>
</div>
""", unsafe_allow_html=True)

# ── 検索履歴のロード（セッション初回のみ）────────────────
if "search_history" not in st.session_state:
    if gs.is_enabled():
        loaded_h = gs.load_search_history()
        st.session_state.search_history = loaded_h
    else:
        st.session_state.search_history = []

# ── 統計データ計算 ────────────────────────────────────────
_h     = st.session_state.get("search_history", [])
_best  = max((h["profit"] for h in _h), default=0)
_avg_r = round(sum(h["profit_rate"] for h in _h) / len(_h), 1) if _h else 0.0
_best_item = max(_h, key=lambda x: x["profit"]) if _h else None

RANK_ICONS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

# ── 統計カード（タップで詳細） ────────────────────────────
if not _h:
    st.markdown(
        '<div style="background:#f8f9fa;border-radius:14px;padding:1.5rem;text-align:center;color:#aaa;margin-bottom:1rem">'
        '<div style="font-size:2rem">🔍</div>'
        '<div style="font-size:0.95rem;margin-top:0.4rem;font-weight:600;color:#666">まだ検索履歴がありません</div>'
        '<div style="font-size:0.82rem;margin-top:0.3rem">バーコード検索か手動検索で仕入れ値を入力して検索してみよう</div>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    # 検索件数
    with st.expander(f"🔍　検索件数　**{len(_h)} 件**　▼ タップで一覧"):
        st.caption("商品をタップすると手動検索で再検索できます")
        for hi, item in enumerate(reversed(_h[-10:])):
            p    = item["profit"]
            icon = "✅" if p >= 500 else ("🤔" if p >= 0 else "❌")
            ps   = f"+¥{p:,}" if p >= 0 else f"-¥{abs(p):,}"
            hc1, hc2 = st.columns([3, 1])
            hc1.markdown(f"**{item['name'][:22]}**  \n{icon} {ps}（{item['profit_rate']}%）　{item['time']}")
            with hc2:
                if st.button("🔍", key=f"re_search_{hi}",
                             use_container_width=True, help="この商品を再検索"):
                    st.session_state["_prefill_kw"]    = item["name"]
                    st.session_state["search_keyword"] = item["name"]
                    st.session_state["search_cost"]    = item.get("cost", 0)
                    st.session_state["search_ship"]    = item.get("ship_cost", 750)
                    st.session_state["search_results"] = None
                    st.switch_page("pages/2_🔍_手動検索.py")
        if st.button("🗑️ 履歴を消す", key="clear_history"):
            st.session_state.search_history = []
            st.rerun()

    # 最高利益
    _best_color = "#2ecc71" if _best >= 800 else ("#f39c12" if _best >= 0 else "#e74c3c")
    with st.expander(f"💰　最高利益　**¥{_best:,}**　▼ タップで詳細"):
        if _best_item:
            bsell  = _best_item.get("sell", 0)
            bcost  = _best_item.get("cost", 0)
            bship  = _best_item.get("ship_cost", 750)
            brate  = _best_item.get("profit_rate", 0)
            st.markdown(f"**{_best_item['name']}**")
            bc1, bc2, bc3 = st.columns(3)
            bc1.metric("仕入れ値", f"¥{bcost:,}")
            bc2.metric("売値",     f"¥{bsell:,}")
            bc3.metric("利益率",   f"{brate}%")
            if bsell > 0:
                st.markdown("**プラットフォーム別利益**")
                best_p, best_n = -999999, ""
                for pname, fee_rate, transfer in [
                    ("メルカリ", 0.10, 200), ("ラクマ", 0.066, 0),
                    ("PayPayフリマ", 0.05, 0), ("ヤフオク", 0.088, 0),
                ]:
                    pr = bsell - bcost - bship - round(bsell * fee_rate) - transfer
                    pr_rate = round(pr / bsell * 100, 1)
                    if pr > best_p:
                        best_p, best_n = pr, pname
                    pc1, pc2 = st.columns([2, 1])
                    pc1.write(f"**{pname}**")
                    pc2.write(f"¥{pr:,}（{pr_rate}%）")
                st.success(f"✅ 最も利益が出るのは **{best_n}**（¥{best_p:,}）")

    # 平均利益率
    _rate_color = "#2ecc71" if _avg_r >= 20 else ("#f39c12" if _avg_r >= 8 else "#e74c3c")
    with st.expander(f"📈　平均利益率　**{_avg_r}%**　▼ タップでランキング"):
        ranked = sorted(_h, key=lambda x: x["profit_rate"], reverse=True)[:5]
        for i, item in enumerate(ranked):
            p   = item["profit"]
            clr = "profit-pos" if p >= 500 else ("profit-mid" if p >= 0 else "profit-neg")
            ps  = f"+¥{p:,}" if p >= 0 else f"-¥{abs(p):,}"
            st.markdown(
                f'<div class="rank-item">'
                f'<span class="rank-badge">{RANK_ICONS[i]}</span>'
                f'<span class="rank-name">{item["name"][:20]}</span>'
                f'<span class="rank-profit {clr}">{ps}</span>'
                f'<span class="rank-rate">{item["profit_rate"]}%</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.divider()

# ── クイックアクセス ────────────────────────────────────
st.markdown('<div class="quick-area">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/1_📷_バーコード検索.py", label="📷 バーコード検索", use_container_width=True)
with c2:
    st.page_link("pages/2_🔍_手動検索.py", label="🔍 手動検索", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── かんたん利益計算 ────────────────────────────────────
st.markdown('<div class="calc-area">', unsafe_allow_html=True)
st.markdown('<div class="section-title">⚡ かんたん利益計算</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    cost = st.number_input("仕入れ値（円）", min_value=0, value=0, step=10, key="home_cost")
with col2:
    sell = st.number_input("売値（円）", min_value=0, value=0, step=10, key="home_sell")

shipping = st.selectbox("配送方法", [
    "らくらくメルカリ便 60サイズ（750円）",
    "らくらくメルカリ便 80サイズ（850円）",
    "ゆうパケット（230円）",
    "ネコポス（210円）",
], key="home_shipping")
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

# 判定バナー
if sell == 0 and cost == 0:
    st.markdown('<div class="verdict-empty"><div class="verdict-title">仕入れ値と売値を入力</div></div>', unsafe_allow_html=True)
elif profit >= 1000 and profit_rate >= 20:
    st.markdown(f'<div class="verdict-buy"><div class="verdict-title">✅ 買い！</div><div class="verdict-sub">利益 ¥{profit:,} ／ 利益率 {profit_rate}%</div></div>', unsafe_allow_html=True)
elif profit >= 500 and profit_rate >= 10:
    st.markdown(f'<div class="verdict-maybe"><div class="verdict-title">🤔 検討あり</div><div class="verdict-sub">利益 ¥{profit:,} ／ 利益率 {profit_rate}%</div></div>', unsafe_allow_html=True)
elif profit >= 0:
    st.markdown(f'<div class="verdict-maybe"><div class="verdict-title">△ 利益薄い</div><div class="verdict-sub">利益 ¥{profit:,} ／ 利益率 {profit_rate}%</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="verdict-bad"><div class="verdict-title">❌ やめとこう</div><div class="verdict-sub">赤字 ¥{abs(profit):,}</div></div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)
col3.metric("利益", f"¥{profit:,}")
col4.metric("利益率", f"{profit_rate}%")

with st.expander("📊 詳細・おすすめ売値を見る"):
    if sell > 0:
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
            ("ラクマ", 0.066, 0),
            ("PayPayフリマ", 0.05, 0),
            ("ヤフオク", 0.088, 0),
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
    else:
        st.caption("売値を入力すると詳細が表示されます")

st.markdown('</div>', unsafe_allow_html=True)
