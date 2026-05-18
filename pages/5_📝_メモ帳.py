import streamlit as st

st.markdown("""
<style>
 .block-container { padding: 1.5rem 1rem 3rem; max-width: 480px; margin: 0 auto !important; }
 h1 { font-size: 1.3rem !important; }
 .memo-card {
  background: #f8f9fa; border-radius: 14px;
  padding: 1rem 1rem 0.8rem; margin-bottom: 0.8rem;
  border-left: 5px solid #ccc;
 }
 .memo-card.buy  { border-left-color: #2ecc71; }
 .memo-card.maybe{ border-left-color: #f39c12; }
 .memo-card.bad  { border-left-color: #e74c3c; }
 .memo-name { font-weight: 700; font-size: 1rem; margin-bottom: 0.3rem; }
 .memo-meta { font-size: 0.82rem; color: #666; }
 .profit-pos { color: #2ecc71; font-weight: bold; }
 .profit-neg { color: #e74c3c; font-weight: bold; }
 .profit-mid { color: #f39c12; font-weight: bold; }
 .empty-box {
  background: #f1f3f5; border-radius: 14px;
  padding: 2.5rem 1rem; text-align: center; color: #aaa;
  margin-top: 1rem;
 }
 .stButton > button { border-radius: 10px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("📝 仕入れメモ帳")
st.caption("バーコード検索・手動検索から「メモに追加」した商品が並びます")
st.divider()

if "memo_list" not in st.session_state:
    st.session_state.memo_list = []

memo_list = st.session_state.memo_list

# ── 空の場合 ─────────────────────────────────────────
if not memo_list:
    st.markdown("""
    <div class="empty-box">
     <div style="font-size:2rem">📋</div>
     <div style="margin-top:0.5rem">まだ何もありません</div>
     <div style="font-size:0.85rem;margin-top:0.3rem">
      バーコード検索や手動検索で「メモに追加」してください
     </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── サマリ ───────────────────────────────────────────
total_cost   = sum(m["cost"]   for m in memo_list)
total_profit = sum(m["profit"] for m in memo_list)
buy_count    = sum(1 for m in memo_list if m["profit"] >= 800 and m["profit_rate"] >= 20)

c1, c2, c3 = st.columns(3)
c1.metric("件数",     f"{len(memo_list)} 件")
c2.metric("仕入れ合計", f"¥{total_cost:,}")
c3.metric("利益合計",  f"¥{total_profit:,}")

if buy_count:
    st.success(f"✅ 「買い」判定が {buy_count} 件あります")

st.divider()

# ── 一括削除 ─────────────────────────────────────────
if st.button("🗑️ すべて削除", key="clear_all_memo"):
    st.session_state.memo_list = []
    st.rerun()

st.markdown("")

# ── メモリスト ───────────────────────────────────────
delete_idx = None

for i, m in enumerate(reversed(memo_list)):
    idx = len(memo_list) - 1 - i   # 元のインデックス

    profit = m["profit"]
    rate   = m["profit_rate"]

    if profit >= 800 and rate >= 20:
        card_class, icon, color = "buy",   "✅", "profit-pos"
    elif profit >= 200 and rate >= 8:
        card_class, icon, color = "maybe", "🤔", "profit-mid"
    else:
        card_class, icon, color = "bad",   "❌", "profit-neg"

    profit_str = f"+¥{profit:,}" if profit >= 0 else f"-¥{abs(profit):,}"

    st.markdown(f"""
    <div class="memo-card {card_class}">
     <div class="memo-name">{icon} {m['name'][:28]}</div>
     <div class="memo-meta">
      仕入れ ¥{m['cost']:,}　
      推定売値 ¥{m.get('sell', 0):,}　
      <span class="{color}">{profit_str}（{rate}%）</span>
      　{m['time']}
     </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ 削除", key=f"del_memo_{idx}"):
        delete_idx = idx

if delete_idx is not None:
    st.session_state.memo_list.pop(delete_idx)
    st.rerun()
