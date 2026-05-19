import streamlit as st
from datetime import datetime
from utils import generate_listing_text
import sheets as gs

CONDS = ["未使用・新品同様", "良い", "可", "不可"]
SHIP_OPTIONS = [
    "らくらくメルカリ便 60サイズ（750円）",
    "ゆうパケット（230円）",
    "ネコポス（210円）",
    "らくらくメルカリ便 80サイズ（850円）",
]
SHIP_COST_MAP = {
    "らくらくメルカリ便 60サイズ（750円）": 750,
    "ゆうパケット（230円）": 230,
    "ネコポス（210円）": 210,
    "らくらくメルカリ便 80サイズ（850円）": 850,
}

st.markdown("""
<style>
 .block-container { padding: 1.5rem 1rem 3rem; max-width: 480px; margin: 0 auto !important; }
 h1 { font-size: 1.3rem !important; }
 .memo-card {
  background: #f8f9fa; border-radius: 14px;
  padding: 1rem 1rem 0.8rem; margin-bottom: 0.4rem;
  border-left: 5px solid #ccc;
 }
 .memo-card.buy   { border-left-color: #2ecc71; }
 .memo-card.maybe { border-left-color: #f39c12; }
 .memo-card.bad   { border-left-color: #e74c3c; }
 .memo-card.listing { border-left-color: #3498db; }
 .memo-card.sold  { border-left-color: #9b59b6; }
 .memo-name { font-weight: 700; font-size: 1rem; margin-bottom: 0.25rem; }
 .memo-meta { font-size: 0.82rem; color: #555; line-height: 1.6; }
 .profit-pos { color: #27ae60; font-weight: bold; }
 .profit-neg { color: #e74c3c; font-weight: bold; }
 .profit-mid { color: #e67e22; font-weight: bold; }
 .empty-box {
  background: #f1f3f5; border-radius: 14px;
  padding: 2.5rem 1rem; text-align: center; color: #aaa;
  margin-top: 1rem;
 }
 .sell-form {
  background: #eaf4fb; border-radius: 12px;
  padding: 0.8rem 1rem; margin: 0.3rem 0 0.8rem;
  border: 1px solid #aed6f1;
 }
 .sold-diff-good { color: #27ae60; font-weight: bold; }
 .sold-diff-bad  { color: #e74c3c; }
 .stButton > button { border-radius: 10px; font-size: 0.9rem; }
 div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.6rem; }
</style>
""", unsafe_allow_html=True)

st.title("📝 仕入れメモ帳")
st.caption("仕入れ候補 → 出品中 → 売却済み の流れで管理できます")
st.divider()

# ── 保存ヘルパー ─────────────────────────────────────────
def _save():
    """変更後に呼ぶ。Sheets が有効なら保存する。"""
    if gs.is_enabled():
        ok = gs.save_memo_list(st.session_state.memo_list)
        if not ok:
            st.warning("⚠️ スプレッドシートへの保存に失敗しました")


# ── 初期化・シートからのロード ───────────────────────────
if "memo_list" not in st.session_state:
    st.session_state.memo_list = []

# セッション内でまだシートを読み込んでいない場合だけロードする
if "sheets_loaded" not in st.session_state:
    if gs.is_enabled():
        with st.spinner("📂 保存データを読み込み中..."):
            loaded = gs.load_memo_list()
        # このセッション中に追加された未保存アイテムをマージ
        loaded_keys = {(m["name"], m["jan"]) for m in loaded}
        new_items   = [m for m in st.session_state.memo_list
                       if (m["name"], m["jan"]) not in loaded_keys]
        st.session_state.memo_list = loaded + new_items
        # 未保存のアイテムがあればすぐにシートに書き込む
        if new_items:
            _save()
    st.session_state.sheets_loaded = True

# 旧データのマイグレーション
for item in st.session_state.memo_list:
    if "status" not in item:
        item["status"] = "候補"

memo_list = st.session_state.memo_list
candidates = [m for m in memo_list if m.get("status") == "候補"]
listings   = [m for m in memo_list if m.get("status") == "出品中"]
sold_items = [m for m in memo_list if m.get("status") == "売却済み"]

# ── タブ ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    f"📋 仕入れ候補　{len(candidates)}",
    f"🏪 出品中　{len(listings)}",
    f"✅ 売却済み　{len(sold_items)}",
])


# ════════════════════════════════════════════════════════
# タブ1：仕入れ候補
# ════════════════════════════════════════════════════════
with tab1:
    if not candidates:
        st.markdown(
            '<div class="empty-box">'
            '<div style="font-size:2rem">📋</div>'
            '<div style="margin-top:0.5rem">まだ何もありません</div>'
            '<div style="font-size:0.85rem;margin-top:0.3rem">バーコード検索や手動検索で「メモに追加」してください</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        total_cost   = sum(m["cost"] for m in candidates)
        total_profit = sum(m["profit"] for m in candidates)
        buy_count    = sum(1 for m in candidates if m["profit"] >= 800 and m["profit_rate"] >= 20)

        c1, c2, c3 = st.columns(3)
        c1.metric("件数",       f"{len(candidates)} 件")
        c2.metric("仕入れ合計", f"¥{total_cost:,}")
        c3.metric("見込み利益", f"¥{total_profit:,}")
        if buy_count:
            st.success(f"✅ 「買い」判定が {buy_count} 件あります")

        st.divider()
        if st.button("🗑️ 候補をすべて削除", key="clear_candidates"):
            st.session_state.memo_list = [m for m in memo_list if m.get("status") != "候補"]
            _save()
            st.rerun()

        delete_idx = None
        for m in reversed(candidates):
            real_idx   = memo_list.index(m)
            profit     = m["profit"]
            rate       = m["profit_rate"]
            profit_str = f"+¥{profit:,}" if profit >= 0 else f"-¥{abs(profit):,}"

            if profit >= 800 and rate >= 20:
                card_class, icon, color = "buy",   "✅", "profit-pos"
            elif profit >= 200 and rate >= 8:
                card_class, icon, color = "maybe", "🤔", "profit-mid"
            else:
                card_class, icon, color = "bad",   "❌", "profit-neg"

            st.markdown(
                f'<div class="memo-card {card_class}">'
                f'<div class="memo-name">{icon} {m["name"][:28]}</div>'
                f'<div class="memo-meta">'
                f'仕入れ ¥{m["cost"]:,}　推定売値 ¥{m.get("sell", 0):,}<br>'
                f'利益 <span class="{color}">{profit_str}（{rate}%）</span>　{m["time"]}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            col_a, col_b, col_c = st.columns([3, 3, 1])
            with col_a:
                if st.button("🏪 出品する", key=f"to_list_{real_idx}", use_container_width=True, type="primary"):
                    st.session_state.memo_list[real_idx]["status"]      = "出品中"
                    st.session_state.memo_list[real_idx]["listed_time"] = datetime.now().strftime("%m/%d %H:%M")
                    _save()
                    st.rerun()
            with col_b:
                pass
            with col_c:
                if st.button("🗑️", key=f"del_cand_{real_idx}", use_container_width=True):
                    delete_idx = real_idx

            with st.expander("✨ 出品文をAIで作る"):
                sel_cond = st.selectbox("状態",   CONDS,        index=1, key=f"cond_{real_idx}")
                sel_ship = st.selectbox("配送方法", SHIP_OPTIONS,        key=f"ship_{real_idx}")
                cg, cr   = st.columns([3, 1])
                with cg:
                    do_gen = st.button("✨ 生成する", key=f"gen_{real_idx}",  type="primary", use_container_width=True)
                with cr:
                    do_re  = st.button("🔄",         key=f"regen_{real_idx}", use_container_width=True)
                lkey = f"listing_{real_idx}"
                if do_gen or do_re:
                    with st.spinner("作成中..."):
                        try:
                            st.session_state[lkey] = generate_listing_text(
                                m["name"], sel_cond, m.get("sell", 0), sel_ship
                            )
                        except Exception:
                            st.error("生成に失敗しました")
                if st.session_state.get(lkey):
                    st.text_area("コピーして使ってください",
                                 value=st.session_state[lkey], height=180,
                                 key=f"listing_out_{real_idx}")

        if delete_idx is not None:
            st.session_state.memo_list.pop(delete_idx)
            _save()
            st.rerun()


# ════════════════════════════════════════════════════════
# タブ2：出品中
# ════════════════════════════════════════════════════════
with tab2:
    if not listings:
        st.markdown(
            '<div class="empty-box">'
            '<div style="font-size:2rem">🏪</div>'
            '<div style="margin-top:0.5rem">出品中の商品はありません</div>'
            '<div style="font-size:0.85rem;margin-top:0.3rem">「仕入れ候補」タブの「出品する」ボタンを押してください</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        total_cost           = sum(m["cost"]   for m in listings)
        total_expected_profit = sum(m["profit"] for m in listings)

        c1, c2, c3 = st.columns(3)
        c1.metric("出品数",     f"{len(listings)} 件")
        c2.metric("在庫仕入れ額", f"¥{total_cost:,}")
        c3.metric("見込み利益", f"¥{total_expected_profit:,}")

        st.divider()

        sold_idx   = None
        sold_price = None
        sold_ship  = None
        back_idx   = None
        del_idx    = None

        # 売却確定後の祝福メッセージ
        if st.session_state.get("_sold_flash"):
            fl   = st.session_state.pop("_sold_flash")
            sign = "+" if fl["profit"] >= 0 else ""
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#2ecc71,#27ae60);color:white;'
                f'border-radius:16px;padding:1.2rem;text-align:center;margin-bottom:0.8rem">'
                f'<div style="font-size:1.5rem;font-weight:900">🎉 売却確定！</div>'
                f'<div style="font-size:1.1rem;margin-top:0.3rem"><strong>{fl["name"][:20]}</strong></div>'
                f'<div style="font-size:1.3rem;font-weight:bold;margin-top:0.4rem">{sign}¥{fl["profit"]:,} の利益</div>'
                f'<div style="font-size:0.85rem;opacity:.85;margin-top:.2rem">売値 ¥{fl["sell"]:,}　利益率 {fl["rate"]}%</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        for m in reversed(listings):
            real_idx    = memo_list.index(m)
            listed_time = m.get("listed_time", "")
            profit_str  = f"¥{m['profit']:,}" if m['profit'] >= 0 else f"-¥{abs(m['profit']):,}"

            date_line = f'<br>出品日 {listed_time}' if listed_time else ""
            st.markdown(
                f'<div class="memo-card listing">'
                f'<div class="memo-name">🏪 {m["name"][:28]}</div>'
                f'<div class="memo-meta">'
                f'仕入れ ¥{m["cost"]:,}　推定売値 ¥{m.get("sell", 0):,}　見込み利益 {profit_str}'
                f'{date_line}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            sell_form_key = f"_show_sell_{real_idx}"

            if st.session_state.get(sell_form_key):
                st.markdown('<div class="sell-form">', unsafe_allow_html=True)
                st.markdown("**💰 実際の売値を入力してください**")
                actual = st.number_input(
                    "売値（円）",
                    min_value=0,
                    value=m.get("sell", 0),
                    step=10,
                    key=f"actual_sell_{real_idx}",
                    label_visibility="collapsed",
                )
                sel_ship_sold = st.selectbox(
                    "配送方法",
                    SHIP_OPTIONS,
                    key=f"sold_ship_{real_idx}",
                )
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("✅ 売却確定", key=f"confirm_{real_idx}",
                                 type="primary", use_container_width=True):
                        sold_idx   = real_idx
                        sold_price = actual
                        sold_ship  = SHIP_COST_MAP[sel_ship_sold]
                with col_cancel:
                    if st.button("キャンセル", key=f"cancel_{real_idx}", use_container_width=True):
                        st.session_state[sell_form_key] = False
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                col_sold, col_back, col_del = st.columns([3, 3, 1])
                with col_sold:
                    if st.button("✅ 売れた！", key=f"sold_btn_{real_idx}",
                                 type="primary", use_container_width=True):
                        st.session_state[sell_form_key] = True
                        st.rerun()
                with col_back:
                    if st.button("← 候補に戻す", key=f"back_{real_idx}", use_container_width=True):
                        back_idx = real_idx
                with col_del:
                    confirm_key = f"_confirm_del_list_{real_idx}"
                    if st.session_state.get(confirm_key):
                        if st.button("✅", key=f"del_list_ok_{real_idx}",
                                     use_container_width=True, type="primary"):
                            del_idx = real_idx
                    else:
                        if st.button("🗑️", key=f"del_list_{real_idx}", use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()

            confirm_key = f"_confirm_del_list_{real_idx}"
            if st.session_state.get(confirm_key):
                ca, cb = st.columns(2)
                with ca:
                    st.caption("⚠️ 本当に削除しますか？")
                with cb:
                    if st.button("✕ キャンセル", key=f"cancel_del_list_{real_idx}",
                                 use_container_width=True):
                        st.session_state[confirm_key] = False
                        st.rerun()

        if sold_idx is not None and sold_price is not None:
            sc            = sold_ship or 750
            actual_profit = sold_price - memo_list[sold_idx]["cost"] - sc - round(sold_price * 0.10) - 200
            actual_rate   = round(actual_profit / sold_price * 100, 1) if sold_price > 0 else 0
            st.session_state.memo_list[sold_idx].update({
                "status":        "売却済み",
                "actual_sell":   sold_price,
                "actual_profit": actual_profit,
                "actual_rate":   actual_rate,
                "sold_time":     datetime.now().strftime("%m/%d %H:%M"),
            })
            st.session_state[f"_show_sell_{sold_idx}"] = False
            st.session_state["_sold_flash"] = {
                "name":   memo_list[sold_idx]["name"],
                "profit": actual_profit,
                "rate":   actual_rate,
                "sell":   sold_price,
            }
            _save()
            st.rerun()

        if back_idx is not None:
            st.session_state.memo_list[back_idx]["status"] = "候補"
            st.session_state.pop(f"_confirm_del_list_{back_idx}", None)
            _save()
            st.rerun()

        if del_idx is not None:
            st.session_state.pop(f"_confirm_del_list_{del_idx}", None)
            st.session_state.memo_list.pop(del_idx)
            _save()
            st.rerun()


# ════════════════════════════════════════════════════════
# タブ3：売却済み
# ════════════════════════════════════════════════════════
with tab3:
    if not sold_items:
        st.markdown(
            '<div class="empty-box">'
            '<div style="font-size:2rem">✅</div>'
            '<div style="margin-top:0.5rem">まだ売却済み商品はありません</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        total_sell   = sum(m.get("actual_sell",   m.get("sell",   0)) for m in sold_items)
        total_profit = sum(m.get("actual_profit", m.get("profit", 0)) for m in sold_items)
        total_cost   = sum(m["cost"] for m in sold_items)
        avg_rate     = round(
            sum(m.get("actual_rate", m.get("profit_rate", 0)) for m in sold_items) / len(sold_items), 1
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("売却数",   f"{len(sold_items)} 件")
        c2.metric("総売上",   f"¥{total_sell:,}")
        c3.metric("総利益",   f"¥{total_profit:,}")
        st.caption(f"仕入れ合計 ¥{total_cost:,}　平均利益率 {avg_rate}%")

        st.divider()

        if st.button("🗑️ 売却済みをすべて削除", key="clear_sold"):
            st.session_state.memo_list = [m for m in memo_list if m.get("status") != "売却済み"]
            _save()
            st.rerun()

        del_idx = None
        for m in reversed(sold_items):
            real_idx      = memo_list.index(m)
            actual_sell   = m.get("actual_sell",   m.get("sell",   0))
            actual_profit = m.get("actual_profit", m.get("profit", 0))
            actual_rate   = m.get("actual_rate",   m.get("profit_rate", 0))
            sold_time     = m.get("sold_time", "")
            profit_str    = f"+¥{actual_profit:,}" if actual_profit >= 0 else f"-¥{abs(actual_profit):,}"
            color         = "profit-pos" if actual_profit >= 500 else ("profit-mid" if actual_profit >= 0 else "profit-neg")

            diff = actual_sell - m.get("sell", 0)
            if m.get("sell", 0) > 0 and diff != 0:
                diff_cls = "sold-diff-good" if diff > 0 else "sold-diff-bad"
                diff_str = f'　<span class="{diff_cls}">{"▲" if diff > 0 else "▼"} ¥{abs(diff):,}</span>'
            else:
                diff_str = ""

            time_str = f"　{sold_time}" if sold_time else ""
            st.markdown(
                f'<div class="memo-card sold">'
                f'<div class="memo-name">✅ {m["name"][:28]}</div>'
                f'<div class="memo-meta">'
                f'仕入れ ¥{m["cost"]:,}　売値 ¥{actual_sell:,}{diff_str}<br>'
                f'利益 <span class="{color}">{profit_str}（{actual_rate}%）</span>{time_str}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            confirm_key = f"_confirm_del_sold_{real_idx}"
            if st.session_state.get(confirm_key):
                col_ok, col_cancel = st.columns(2)
                with col_ok:
                    if st.button("🗑️ 本当に削除", key=f"del_sold_ok_{real_idx}",
                                 type="primary", use_container_width=True):
                        del_idx = real_idx
                with col_cancel:
                    if st.button("✕ キャンセル", key=f"del_sold_cancel_{real_idx}",
                                 use_container_width=True):
                        st.session_state[confirm_key] = False
                        st.rerun()
            else:
                if st.button("🗑️ 削除", key=f"del_sold_{real_idx}"):
                    st.session_state[confirm_key] = True
                    st.rerun()

        if del_idx is not None:
            st.session_state.pop(f"_confirm_del_sold_{del_idx}", None)
            st.session_state.memo_list.pop(del_idx)
            _save()
            st.rerun()
