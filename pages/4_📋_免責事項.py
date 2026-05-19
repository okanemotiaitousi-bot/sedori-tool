import streamlit as st

st.markdown("""
<style>
 .block-container { padding: 1.5rem 1.2rem 4rem; max-width: 480px; margin: auto; }
 h1 { font-size: 1.3rem !important; }
 h3 { font-size: 1rem !important; color: #222; margin-top: 1.4rem; }
 h4 { font-size: 0.92rem !important; color: #333; margin-top: 1rem; }
 p, li { font-size: 0.88rem; color: #444; line-height: 1.85; }
 .policy-card {
  background: #f8f9fa; border-radius: 14px;
  padding: 1.2rem 1.2rem 0.8rem; margin-bottom: 1rem;
 }
 .update-badge {
  background: #e8f4fd; color: #2980b9;
  border-radius: 8px; padding: 0.2rem 0.7rem;
  font-size: 0.78rem; display: inline-block; margin-bottom: 1rem;
 }
</style>
""", unsafe_allow_html=True)

st.title("📋 利用規約・プライバシーポリシー")
st.markdown('<span class="update-badge">最終更新：2026年5月</span>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📄 利用規約", "🔒 プライバシーポリシー"])

# ══════════════════════════════════════════════
# 利用規約
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第1条（本サービスについて）
「せどり目利きツール」（以下「本サービス」）は、店舗せどり・転売における仕入れ判断の参考情報を提供することを目的とした個人開発のWebアプリです。
本サービスを利用した時点で、本規約に同意したものとみなします。
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第2条（情報の正確性と免責）
- 表示される価格・相場はYahoo!ショッピングAPIのデータをもとにした**目安**です
- 実際のメルカリ・ヤフオク・ラクマ等での売買価格とは異なる場合があります
- AIによる状態判定・出品文生成は補助的なものであり、正確性を保証しません
- 本サービスの情報をもとにした仕入れ・出品判断は**すべて自己責任**となります
- 運営者は本サービスの使用により生じた損害について一切の責任を負いません
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第3条（禁止事項）
以下の行為を禁止します。

- 違法な転売・買い占め・独占禁止法に違反する行為
- 各プラットフォーム（メルカリ・ヤフオク等）の利用規約に違反する行為
- 本サービスの無断複製・逆コンパイル・改ざん・再配布
- 本サービスへの過度な負荷をかける行為
- その他、運営者が不適切と判断する行為
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第4条（有料プランについて）
- 有料プランの料金・内容は別途定める料金ページに従います
- 決済はStripeを通じて行われます
- 月額プランは毎月自動更新されます
- 解約はいつでも可能です。解約月末までご利用いただけます
- 返金は原則として対応しておりません（サービス障害等による場合を除く）
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第5条（サービスの変更・停止）
- 本サービスは予告なく内容の変更・機能の追加・削除を行う場合があります
- サービスの停止・終了を行う場合は、可能な限り事前にお知らせします

### 第6条（準拠法・管轄）
本規約は日本法に準拠します。
""")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# プライバシーポリシー
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第1条（収集する情報）
本サービスでは以下の情報を収集・保存する場合があります。

**① ご自身で入力した情報**
- 仕入れ値・売値・商品名などの計算入力値
- メモ帳に保存した商品情報（商品名・利益・ステータス等）
- 検索履歴

**② 自動的に収集される情報**
- Streamlitの標準的なアクセスログ（IPアドレス等）
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第2条（情報の利用目的）
収集した情報は以下の目的のみに使用します。

- サービスの提供・改善
- 検索履歴・メモ帳データの表示・保存
- サービスの不正利用防止

収集した情報を第三者に販売・提供することはありません。
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第3条（データの保存）
- メモ帳・検索履歴のデータはGoogleスプレッドシートに保存されます
- データはGoogleのセキュリティポリシーに従って管理されます
- アカウント削除をご希望の場合はお問い合わせください

### 第4条（外部サービス）
本サービスは以下の外部サービスを利用しています。

- **Google Gemini API**（AI機能・写真判定・出品文生成）
- **Yahoo!ショッピングAPI**（商品検索・価格取得）
- **Google Sheets API**（データ保存）
- **Streamlit Cloud**（ホスティング）

各サービスのプライバシーポリシーもご確認ください。
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)
    st.markdown("""
### 第5条（お問い合わせ）
プライバシーに関するお問い合わせはTikTokまたは下記の方法でご連絡ください。

本ポリシーは予告なく変更される場合があります。変更後の利用をもって同意したものとみなします。
""")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("本サービスを使用した時点で利用規約・プライバシーポリシーに同意したものとみなします。")
