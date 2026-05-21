import streamlit as st
import sheets as gs

st.set_page_config(
    page_title="せどり目利きツール",
    page_icon="💰",
    layout="centered",
)

# ── セッション state 初期化（全ページ共有）──────────────────
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# ── ニックネーム入力（初回のみ・user_id として使用）─────────
if "user_id" not in st.session_state:
    st.markdown("""
<style>
 .block-container { max-width: 400px !important; margin: 3rem auto !important; padding: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="text-align:center;margin-bottom:2rem">
 <div style="font-size:3.5rem">💰</div>
 <h1 style="font-size:1.5rem;font-weight:900;margin:0.4rem 0 0.2rem">せどり目利きツール</h1>
 <p style="font-size:0.85rem;color:#888;margin:0">テスター限定ベータ版</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("#### あなたのニックネームを入力してください")
    st.caption("メモ帳・検索履歴をブラウザをまたいで保存するために使います。\nすでに使ったことがある方は同じニックネームを入力すると前回の続きから使えます。")

    with st.form("nickname_form"):
        nickname = st.text_input(
            "ニックネーム",
            placeholder="例：たろう、せどりマスターなど",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("はじめる 🚀", type="primary", use_container_width=True)

    if submitted:
        name = nickname.strip()
        if name:
            st.session_state.user_id = name
            st.rerun()
        else:
            st.warning("ニックネームを入力してください")

    st.markdown("""
<div style="background:#fff8e1;border-radius:10px;padding:0.8rem 1rem;font-size:0.82rem;color:#7d6608;margin-top:1rem">
 ⚠️ <strong>注意</strong>：同じニックネームを使う人がいると、メモが混ざる可能性があります。<br>
 できるだけ他の人と被らないニックネームを使ってください。
</div>
""", unsafe_allow_html=True)

    st.stop()

# ── REQUIRE_LOGIN フラグをページ間で共有 ─────────────────────
_require_login = str(st.secrets.get("REQUIRE_LOGIN", "false")).lower() == "true"
st.session_state["_require_login"] = _require_login

# ── 認証状態に応じて user_id を同期 ──────────────────────────
if _require_login:
    if st.session_state.get("authentication_status") is True:
        # ── ログイン済み：user_id をユーザー名に設定 ──────────
        st.session_state.user_id = st.session_state.get("username", "default")

        with st.sidebar:
            name = st.session_state.get("name") or st.session_state.user_id
            st.markdown(
                f'<div style="font-size:0.9rem;padding:0.4rem 0">👤 <strong>{name}</strong> さん</div>',
                unsafe_allow_html=True,
            )
            if st.button("ログアウト", key="_sidebar_logout", use_container_width=True):
                # cookie を削除してセッションをリセット
                try:
                    import streamlit_authenticator as stauth

                    cookie_cfg = st.secrets.get(
                        "cookie",
                        {"name": "sedori_tool_auth", "key": "sedori_secret_key_2026", "expiry_days": 30},
                    )
                    _auth = stauth.Authenticate(
                        dict(st.secrets.get("credentials", {})),
                        cookie_cfg.get("name", "sedori_tool_auth"),
                        cookie_cfg.get("key", "sedori_secret_key_2026"),
                        int(cookie_cfg.get("expiry_days", 30)),
                    )
                    _auth.logout(location="unrendered")
                except Exception:
                    pass
                for _k in ("authentication_status", "username", "name", "logout"):
                    st.session_state.pop(_k, None)
                st.session_state.user_id = "default"
                st.rerun()
    else:
        # ── 未ログイン：user_id は常に default ──────────────────
        st.session_state.user_id = "default"
        with st.sidebar:
            st.caption("🔒 メモ帳はプレミアム限定")

else:
    # ── ログイン不要モード：サイドバーにニックネームを表示 ──────
    with st.sidebar:
        st.caption(f"👤 {st.session_state.user_id} さん")
        if st.button("別の名前で使う", key="_change_nick", use_container_width=True):
            for _k in list(st.session_state.keys()):
                del st.session_state[_k]
            st.rerun()


# ── ページナビゲーション（常に全ページを表示）─────────────────
def _run_pages():
    pg = st.navigation([
        st.Page("pages/home.py",                    title="ホーム",         icon="💰", default=True),
        st.Page("pages/1_📷_バーコード検索.py",      title="バーコード検索", icon="📷"),
        st.Page("pages/2_🔍_手動検索.py",            title="手動検索",       icon="🔍"),
        st.Page("pages/3_🏷️_状態別売値計算.py",     title="状態別売値計算", icon="🏷️"),
        st.Page("pages/5_📝_メモ帳.py",              title="仕入れメモ帳",   icon="📝"),
        st.Page("pages/4_📋_免責事項.py",            title="免責事項",       icon="📋"),
    ])
    pg.run()


# ── 検索履歴をシートから読み込む（セッション内1回のみ）────────
if not st.session_state.get("_history_loaded"):
    _load_uid = st.session_state.get("user_id", "default")
    if gs.is_enabled() and _load_uid != "default":
        _loaded_h = gs.load_search_history(_load_uid)
        if _loaded_h:
            st.session_state.search_history = _loaded_h
    st.session_state["_history_loaded"] = True

_run_pages()
