import streamlit as st
import requests
from PIL import Image
from datetime import datetime
from utils import show_auction_prices, generate_listing_text
import sheets as gs

st.markdown("""
<style>
 .block-container { padding: 1rem 1rem 2rem; max-width: 460px; margin: auto; }
 h1 { font-size: 1.3rem !important; }
 .verdict-buy {
 background: linear-gradient(135deg, #2ecc71, #27ae60);
 color: white; border-radius: 20px; padding: 2rem 1rem;
 text-align: center; font-size: 2.2rem; font-weight: bold;
 }
 .verdict-maybe {
 background: linear-gradient(135deg, #f39c12, #e67e22);
 color: white; border-radius: 20px; padding: 2rem 1rem;
 text-align: center; font-size: 2.2rem; font-weight: bold;
 }
 .verdict-bad {
 background: linear-gradient(135deg, #e74c3c, #c0392b);
 color: white; border-radius: 20px; padding: 2rem 1rem;
 text-align: center; font-size: 2.2rem; font-weight: bold;
 }
 .product-card { background: #f8f9fa; border-radius: 12px; padding: 0.8rem; margin: 0.5rem 0; }
 .price-tag { color: #e74c3c; font-size: 1.4rem; font-weight: bold; }
 .stNumberInput input { font-size: 1.4rem; height: 3.5rem; font-weight: bold; }
 .stButton > button { border-radius: 12px; height: 3rem; font-size: 1rem; font-weight: bold; width: 100%; }
 div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 10px; padding: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ── セッション初期化（存在しない場合のみ設定）──────────────
for key, default in [
    ("barcode_screen", "scan"),
    ("barcode_jan", ""),
    ("barcode_product", None),
    ("barcode_cost", 0),
    ("barcode_sell", 0),
    ("barcode_ship_cost", 750),
    ("barcode_listing", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ════════════════════════════════════════════════════════
# 画面1：スキャン
# ════════════════════════════════════════════════════════
if st.session_state.barcode_screen == "scan":
    st.title("📷 バーコードをスキャン")

    # カメラ許可のトグル
    if "camera_allowed" not in st.session_state:
        st.session_state.camera_allowed = True

    tab1, tab2 = st.tabs(["📷 カメラ", "⌨️ 手打ち"])

    with tab1:
        if st.session_state.camera_allowed:
            st.caption("バーコードにカメラを向けて撮影ボタンを押してください")
            photo = st.camera_input("バーコード撮影", label_visibility="collapsed", key="camera_input")
            if photo:
                decoded = False
                try:
                    from pyzbar import pyzbar
                    barcodes = pyzbar.decode(Image.open(photo))
                    if barcodes:
                        st.session_state.barcode_jan = barcodes[0].data.decode("utf-8")
                        st.session_state.barcode_product = None
                        st.session_state.barcode_screen = "result"
                        decoded = True
                        st.rerun()
                except Exception:
                    pass
                if not decoded:
                    st.warning("読み取れませんでした。もう一度試すか「手打ち」タブを使ってください。")

            st.markdown("---")
            if st.button("🚫 カメラが使えない・キャンセルしてしまった場合はここ", key="btn_camera_off"):
                st.session_state.camera_allowed = False
                st.rerun()
        else:
            st.markdown("""
            ### 📷 カメラを使う方法
            ブラウザがカメラをブロックしている状態です。
            以下の手順で許可を変更してください。

            **Chromeの場合（スマホ）**
            1. ブラウザのアドレスバー左の 🔒 をタップ
            2. 「権限」または「カメラ」をタップ
            3. 「許可」に変更
            4. ページを再読み込み（↺）

            **Safariの場合（iPhone）**
            1. 設定アプリ → Safari → カメラ
            2. 「許可」または「確認」に変更
            3. ページを再読み込み
            """)
            if st.button("✅ カメラを許可した → カメラ画面に戻る", type="primary", key="btn_camera_on"):
                st.session_state.camera_allowed = True
                st.rerun()

    with tab2:
        jan_input = st.text_input(
            "JANコード（13桁の数字）",
            placeholder="例：4901777374300",
            label_visibility="collapsed",
            key="jan_text_input",
        )
        if st.button("🔍 検索する", type="primary", key="btn_search_jan"):
            if jan_input.strip():
                st.session_state.barcode_jan = jan_input.strip()
                st.session_state.barcode_product = None
                st.session_state.barcode_screen = "result"
                st.rerun()
            else:
                st.warning("JANコードを入力してください")

# ════════════════════════════════════════════════════════
# 画面2：判定
# ════════════════════════════════════════════════════════
elif st.session_state.barcode_screen == "result":

    # 商品情報を取得（まだなければAPI呼び出し）
    if st.session_state.barcode_product is None:
        with st.spinner("🔍 検索中..."):
            try:
                res = requests.get(
                    "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch",
                    params={
                        "appid": st.secrets["YAHOO_APP_ID"],
                        "jan_code": st.session_state.barcode_jan,
                        "results": 1,
                    },
                    timeout=5,
                )
                hits = res.json().get("hits", [])
                if hits:
                    item = hits[0]
                    st.session_state.barcode_product = {
                        "name": item.get("name", "不明"),
                        "price": item.get("price", None),
                        "url": item.get("url", ""),
                        "image_url": item.get("image", {}).get("medium", ""),
                        "brand": item.get("brand", {}).get("name", ""),
                    }
                else:
                    st.session_state.barcode_product = {
                        "name": "（商品名不明）",
                        "price": None,
                        "url": "",
                        "image_url": "",
                        "brand": "",
                    }
            except Exception:
                st.session_state.barcode_product = {
                    "name": "（取得失敗）",
                    "price": None,
                    "url": "",
                    "image_url": "",
                    "brand": "",
                }

    p = st.session_state.barcode_product

    # 商品カード
    col_img, col_info = st.columns([1, 2])
    with col_img:
        if p["image_url"]:
            st.image(p["image_url"], use_container_width=True)
    with col_info:
        st.markdown(f"**{p['name'][:35]}**")
        if p["brand"]:
            st.caption(f"🏷 {p['brand']}")
        if p["price"]:
            st.markdown(f'<span class="price-tag">¥{int(p["price"]):,}</span>', unsafe_allow_html=True)
            st.caption("Yahoo!最安値")

    st.divider()
    st.markdown("### 💴 仕入れ値を入力")

    # 仕入れ値：前回入力値を復元する
    cost = st.number_input(
        "仕入れ値（円）",
        min_value=0,
        value=st.session_state.barcode_cost,
        step=10,
        label_visibility="collapsed",
        key="result_cost_input",
    )
    # 入力するたびにsession stateに保存
    st.session_state.barcode_cost = cost

    # 仕入れ値が未入力（0）でも計算・表示する（0円仕入れも有効な入力として扱う）
    if p["price"] and int(p["price"]) < 1500:
        ship_cost, ship_name = 230, "ゆうパケット（230円）"
    else:
        ship_cost, ship_name = 750, "らくらくメルカリ便 60サイズ（750円）"

    if p["price"] and int(p["price"]) > 0:
        sell = round(int(p["price"]) * 0.62)
    else:
        sell = round((cost + ship_cost + 200) / (1 - 0.10) / (1 - 0.20))

    profit = sell - cost - ship_cost - round(sell * 0.10) - 200
    profit_rate = round(profit / sell * 100, 1) if sell > 0 else 0

    # 履歴に追加（仕入れ値が入力済みのときのみ）
    if cost > 0:
        if "search_history" not in st.session_state:
            st.session_state.search_history = []
        jan = st.session_state.barcode_jan
        history = st.session_state.search_history
        history = [h for h in history if h.get("jan") != jan]
        history.append({
            "name": p["name"],
            "jan": jan,
            "cost": cost,
            "sell": sell,
            "ship_cost": ship_cost,
            "profit": profit,
            "profit_rate": profit_rate,
            "time": datetime.now().strftime("%H:%M"),
            "date": datetime.now().strftime("%Y-%m-%d"),
        })
        st.session_state.search_history = history[-30:]
        if gs.is_enabled():
            gs.save_search_history(st.session_state.search_history, st.session_state.get("user_id", "default"))

    if cost == 0:
        st.info("仕入れ値を入力すると判定が更新されます（0円のまま計算することも可能です）")

    if profit >= 800 and profit_rate >= 20:
        st.markdown(
            f'<div class="verdict-buy">✅ 買い！<br><small>推定 ¥{profit:,} 利益</small></div>',
            unsafe_allow_html=True,
        )
    elif profit >= 200 and profit_rate >= 8:
        st.markdown(
            f'<div class="verdict-maybe">🤔 検討あり<br><small>推定 ¥{profit:,} 利益</small></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="verdict-bad">❌ やめとこう<br><small>推定 ¥{profit:,}</small></div>',
            unsafe_allow_html=True,
        )

    st.caption(f"推定売値 ¥{sell:,}　送料 ¥{ship_cost} で計算")

    # ── ヤフオク落札相場 ────────────────────────────
    with st.expander("📦 ヤフオク落札相場を見る"):
        cache_key = st.session_state.barcode_jan or p["name"][:30]
        show_auction_prices(p["name"], cache_key)

    # ── メモに追加 ──────────────────────────────
    if "memo_list" not in st.session_state:
        st.session_state.memo_list = []
    jan = st.session_state.barcode_jan
    _uid = st.session_state.get("user_id", "default")
    already = any(m.get("jan") == jan for m in st.session_state.memo_list)
    if already:
        st.info("📝 メモ帳に保存済み")
        st.page_link("pages/5_📝_メモ帳.py", label="📋 メモ帳を開く", use_container_width=True)
    else:
        if st.button("📝 仕入れ候補にメモ", key="btn_add_memo"):
            st.session_state.memo_list.append({
                "name": p["name"],
                "jan": jan,
                "cost": cost,
                "sell": sell,
                "profit": profit,
                "profit_rate": profit_rate,
                "time": datetime.now().strftime("%H:%M"),
                "status": "候補",
                "ship_name": ship_name,
                "user_id": _uid,
            })
            if gs.is_enabled():
                gs.save_memo_list(st.session_state.memo_list, _uid)
            st.rerun()

    st.markdown("")
    if st.button("📊 詳細を見る", key="btn_to_detail"):
        st.session_state.barcode_sell = sell
        st.session_state.barcode_ship_cost = ship_cost
        st.session_state.barcode_screen = "detail"
        st.rerun()

    st.markdown("")
    if st.button("🔄 別の商品を検索", key="btn_back_to_scan"):
        st.session_state.barcode_screen = "scan"
        st.session_state.barcode_product = None
        st.session_state.barcode_jan = ""
        st.session_state.barcode_cost = 0
        st.rerun()

# ════════════════════════════════════════════════════════
# 画面3：詳細
# ════════════════════════════════════════════════════════
elif st.session_state.barcode_screen == "detail":
    p = st.session_state.barcode_product or {}
    cost = st.session_state.barcode_cost
    sell = st.session_state.barcode_sell
    ship_cost = st.session_state.barcode_ship_cost

    st.title("📊 詳細計算")

    sell2 = st.number_input("売値（円）", min_value=0, value=sell, step=10, key="detail_sell_input")
    ship2 = st.selectbox(
        "配送方法",
        [
            "らくらくメルカリ便 60サイズ（750円）",
            "らくらくメルカリ便 80サイズ（850円）",
            "ゆうパケット（230円）",
            "ネコポス（210円）",
        ],
        key="detail_ship_select",
    )
    ship_map2 = {
        "らくらくメルカリ便 60サイズ（750円）": 750,
        "らくらくメルカリ便 80サイズ（850円）": 850,
        "ゆうパケット（230円）": 230,
        "ネコポス（210円）": 210,
    }
    sc2 = ship_map2[ship2]

    price = p.get("price")
    if price and int(price) > 0:
        ml = round(int(price) * 0.55)
        mh = round(int(price) * 0.70)
        st.info(f"📌 メルカリ推定相場：**¥{ml:,}〜¥{mh:,}**\n\n※ Yahoo!価格をもとにした目安です")

    breakeven = round((cost + sc2 + 200) / (1 - 0.10))
    recommended = round((cost + sc2 + 200) / (1 - 0.10) / (1 - 0.20))
    c1, c2 = st.columns(2)
    c1.metric("最低売値", f"¥{breakeven:,}")
    c2.metric("おすすめ売値", f"¥{recommended:,}")

    st.markdown("**プラットフォーム別利益**")
    best_profit = -999999
    best_platform = ""
    for name, fee_rate, transfer in [
        ("メルカリ", 0.10, 200),
        ("ラクマ", 0.066, 0),
        ("PayPayフリマ", 0.05, 0),
        ("ヤフオク", 0.088, 0),
    ]:
        pr = sell2 - cost - sc2 - round(sell2 * fee_rate) - transfer
        pr_rate = round(pr / sell2 * 100, 1) if sell2 > 0 else 0
        if pr > best_profit:
            best_profit = pr
            best_platform = name
        c1, c2 = st.columns([2, 1])
        c1.write(f"**{name}**")
        c2.write(f"¥{pr:,}（{pr_rate}%）")

    if best_platform:
        st.success(f"✅ 最も利益が出るのは **{best_platform}**（¥{best_profit:,}）")

    # ── 出品文AI自動生成 ────────────────────────────
    st.divider()
    st.markdown("**✨ AIで出品文を自動生成**")
    p2 = st.session_state.barcode_product or {}
    pname = p2.get("name", "")
    if pname:
        CONDS = ["未使用・新品同様", "良い", "可", "不可"]
        sel_cond = st.selectbox("状態を選んでください", CONDS, index=1,
                                key="detail_cond_select")
        col_g, col_r = st.columns([3, 1])
        with col_g:
            gen = st.button("✨ 出品文を生成する", key="detail_gen_btn",
                            type="primary", use_container_width=True)
        with col_r:
            regen = st.button("🔄 作り直す", key="detail_regen_btn",
                              use_container_width=True)
        if gen or regen:
            with st.spinner("🤖 Geminiが出品文を作成中..."):
                try:
                    st.session_state.barcode_listing = generate_listing_text(
                        pname, sel_cond, sell2, ship2
                    )
                except Exception:
                    st.error("生成に失敗しました。もう一度お試しください。")
        if st.session_state.barcode_listing:
            st.text_area("↓ コピーしてメルカリに貼り付けてください",
                         value=st.session_state.barcode_listing,
                         height=200, key="detail_listing_out")

    st.markdown("")
    if st.button("← 戻る", key="btn_detail_back"):
        st.session_state.barcode_screen = "result"
        st.session_state.barcode_listing = ""
        st.rerun()
