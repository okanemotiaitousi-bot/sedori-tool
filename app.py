import streamlit as st

st.set_page_config(
    page_title="せどり目利きツール",
    page_icon="💰",
    layout="centered",
)

# ── 全ページ共有のsession state初期化 ─────────────────────
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# ログインしていない場合はデフォルトユーザー
if "user_id" not in st.session_state:
    st.session_state.user_id = "default"

# ── ログイン機能（REQUIRE_LOGIN=true のときのみ有効）─────
def _run_with_auth():
    """認証ありでアプリを実行する"""
    try:
        import streamlit_authenticator as stauth
        import yaml
    except ImportError:
        st.error("streamlit-authenticator が必要です: pip install streamlit-authenticator")
        st.stop()

    # Secretsからユーザー情報を読み込む
    creds = st.secrets.get("credentials", {})
    if not creds:
        st.error("Secretsに credentials が設定されていません。管理者にお問い合わせください。")
        st.stop()

    cookie_cfg = st.secrets.get("cookie", {
        "name": "sedori_tool_auth",
        "key": "sedori_secret_key_2026",
        "expiry_days": 30,
    })

    authenticator = stauth.Authenticate(
        dict(creds),
        cookie_cfg.get("name", "sedori_tool_auth"),
        cookie_cfg.get("key", "sedori_secret_key_2026"),
        cookie_cfg.get("expiry_days", 30),
    )

    # ログインUI
    if st.session_state.get("authentication_status") is not True:
        st.markdown("""
<style>
 .block-container { max-width: 380px !important; margin: 2rem auto !important; padding: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)
        st.markdown("""
<div style="text-align:center;margin-bottom:2rem">
 <div style="font-size:3rem">💰</div>
 <h1 style="font-size:1.4rem;font-weight:900;margin:0.3rem 0">せどり目利きツール</h1>
 <p style="font-size:0.85rem;color:#888">プレミアムプランへようこそ</p>
</div>
""", unsafe_allow_html=True)

    try:
        authenticator.login(location="main", fields={
            "Form name": "ログイン",
            "Username": "ユーザー名",
            "Password": "パスワード",
            "Login": "ログインする",
        })
    except Exception:
        authenticator.login()

    status = st.session_state.get("authentication_status")

    if status is True:
        # ── ログイン成功：user_idをusernameに設定してアプリを表示 ──
        st.session_state.user_id = st.session_state.get("username", "default")
        with st.sidebar:
            st.markdown(f"👤 **{st.session_state.get('name', '')}** さん")
            authenticator.logout("ログアウト")
        _run_pages()

    elif status is False:
        st.error("ユーザー名またはパスワードが違います")
        _show_contact()

    else:
        st.info("ユーザー名とパスワードを入力してください")
        _show_contact()


def _show_contact():
    st.markdown("""
<div style="background:#f8f9fa;border-radius:12px;padding:1rem;margin-top:1rem;font-size:0.85rem;color:#555;text-align:center">
  ご購入後にお送りしたIDとパスワードでログインしてください。<br>
  ご不明な点はTikTok DMにてお問い合わせください。
</div>
""", unsafe_allow_html=True)


def _run_pages():
    """ページナビゲーションを実行する（認証不要モードでも使用）"""
    pg = st.navigation([
        st.Page("pages/home.py",                    title="ホーム",         icon="💰", default=True),
        st.Page("pages/1_📷_バーコード検索.py",      title="バーコード検索", icon="📷"),
        st.Page("pages/2_🔍_手動検索.py",            title="手動検索",       icon="🔍"),
        st.Page("pages/3_🏷️_状態別売値計算.py",     title="状態別売値計算", icon="🏷️"),
        st.Page("pages/5_📝_メモ帳.py",              title="仕入れメモ帳",   icon="📝"),
        st.Page("pages/4_📋_免責事項.py",            title="免責事項",       icon="📋"),
    ])
    pg.run()


# ── メイン処理 ─────────────────────────────────────────
require_login = str(st.secrets.get("REQUIRE_LOGIN", "false")).lower() == "true"

if require_login:
    _run_with_auth()
else:
    _run_pages()
