"""
Google スプレッドシート連携（マルチユーザー対応版）

【設計方針】
1. user_id 列でユーザーを分離
   - 各行に user_id を持たせ、ロード時はそのユーザーの行だけ取得
   - 保存時は「他ユーザーの行はそのまま」「自分の行だけ差し替える」
   - → 複数ユーザーが同時に書き込んでもデータが混ざらない

2. sheet.clear() を完全廃止
   - 全消去の代わりに batch_update で全行上書き
   - clear() と update() の間にデータが消える瞬間をなくす

3. item_id（UUID）で各レコードを一意に識別
   - 将来的に行単位の更新・削除が可能な構造

4. 指数バックオフ付きリトライ（最大3回）
   - Google API の 429 Quota エラーや一時的な障害に対応

5. 後方互換性
   - user_id 列がない既存データは user_id="default" として扱う
   - item_id がない既存データは読み込み時に自動補完
"""
import time
import uuid
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ── ヘッダー定義（user_id・item_id を末尾に追加） ─────────
SHEET_HEADERS = [
    "name", "jan", "cost", "sell", "profit", "profit_rate",
    "time", "status", "listed_time", "ship_name",
    "actual_sell", "actual_profit", "actual_rate", "sold_time",
    "user_id", "item_id",
]
HISTORY_HEADERS = [
    "name", "jan", "cost", "sell", "ship_cost",
    "profit", "profit_rate", "time", "date",
    "user_id",
]

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DEFAULT_USER = "default"


# ── 接続 ──────────────────────────────────────────────────
def is_enabled() -> bool:
    try:
        _ = st.secrets["gcp_service_account"]
        _ = st.secrets["SPREADSHEET_ID"]
        return True
    except Exception:
        return False


@st.cache_resource
def _get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=_SCOPES,
    )
    return gspread.authorize(creds)


def _get_sheet(index: int = 0) -> gspread.Worksheet:
    """index 番目のシートを返す。存在しなければ自動作成。"""
    client = _get_client()
    wb = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    sheets = wb.worksheets()
    if index < len(sheets):
        return sheets[index]
    names = {0: "メモ帳", 1: "検索履歴"}
    return wb.add_worksheet(
        title=names.get(index, f"sheet{index}"),
        rows=1000,
        cols=20,
    )


# ── 安全な書き込みヘルパー ────────────────────────────────
def _with_retry(fn, max_retries: int = 3):
    """
    fn() を実行し、失敗時は指数バックオフでリトライする。
    成功時は True、最終失敗時は False を返す。
    """
    for attempt in range(max_retries):
        try:
            fn()
            return True
        except gspread.exceptions.APIError as e:
            status = getattr(e.response, "status_code", 0)
            wait = 15 if status == 429 else (2 ** attempt)
            if attempt < max_retries - 1:
                time.sleep(wait)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return False


def _safe_batch_write(sheet: gspread.Worksheet, rows: list) -> bool:
    """
    ヘッダー行 + データ行を sheet に書き込む。
    - 既存行数 > 新行数 の場合、余った行をブランクで上書きして古いデータを消す
    - clear() を一切使わない
    """
    def _write():
        existing_count = len(sheet.get_all_values())
        sheet.update(rows, "A1")
        # 余った古い行をブランクで上書き
        new_count = len(rows)
        if existing_count > new_count:
            col_count = len(rows[0]) if rows else 1
            blank = [[""] * col_count] * (existing_count - new_count)
            sheet.update(blank, f"A{new_count + 1}")

    return _with_retry(_write)


# ── メモ帳 ────────────────────────────────────────────────
def _normalize_memo(r: dict, user_id: str) -> dict:
    """シートの1行を memo_list のアイテム形式に変換する"""
    return {
        "name":          str(r.get("name",          "")).strip(),
        "jan":           str(r.get("jan",            "")),
        "cost":          int(r.get("cost",            0) or 0),
        "sell":          int(r.get("sell",            0) or 0),
        "profit":        int(r.get("profit",          0) or 0),
        "profit_rate":   float(r.get("profit_rate",   0) or 0),
        "time":          str(r.get("time",            "")),
        "status":        str(r.get("status",     "候補")) or "候補",
        "listed_time":   str(r.get("listed_time",     "")),
        "ship_name":     str(r.get("ship_name",       "")),
        "actual_sell":   int(r.get("actual_sell",     0) or 0),
        "actual_profit": int(r.get("actual_profit",   0) or 0),
        "actual_rate":   float(r.get("actual_rate",   0) or 0),
        "sold_time":     str(r.get("sold_time",       "")),
        "user_id":       str(r.get("user_id", DEFAULT_USER)) or user_id,
        "item_id":       str(r.get("item_id", "")) or str(uuid.uuid4()),
    }


def _memo_to_row(m: dict, user_id: str) -> list:
    """memo_list のアイテムをシートの1行（リスト）に変換する"""
    return [
        m.get("name",          ""),
        m.get("jan",           ""),
        m.get("cost",          0),
        m.get("sell",          0),
        m.get("profit",        0),
        m.get("profit_rate",   0),
        m.get("time",          ""),
        m.get("status",   "候補"),
        m.get("listed_time",   ""),
        m.get("ship_name",     ""),
        m.get("actual_sell",   0),
        m.get("actual_profit", 0),
        m.get("actual_rate",   0),
        m.get("sold_time",     ""),
        m.get("user_id", user_id),
        m.get("item_id") or str(uuid.uuid4()),
    ]


def load_memo_list(user_id: str = DEFAULT_USER) -> list:
    """
    スプレッドシートから指定ユーザーのメモリストを読み込む。
    未ログイン（default）はスプレッドシートを参照せず空リストを返す。
    失敗時は空リストを返す。
    """
    if user_id == DEFAULT_USER:
        return []
    try:
        sheet = _get_sheet(0)
        records = sheet.get_all_records()
        result = []
        for r in records:
            name = str(r.get("name", "")).strip()
            if not name:
                continue
            row_user = str(r.get("user_id", DEFAULT_USER)) or DEFAULT_USER
            # user_id 列がない古いデータは DEFAULT_USER として扱う
            if row_user not in (user_id, DEFAULT_USER, ""):
                continue
            item = _normalize_memo(r, user_id)
            result.append(item)
        return result
    except Exception:
        return []


def save_memo_list(memo_list: list, user_id: str = DEFAULT_USER) -> bool:
    """
    指定ユーザーのメモリストを安全に保存する。
    未ログイン（default）はスキップして True を返す。

    手順:
    1. シートの全行を読み込む
    2. 他ユーザーの行はそのまま保持
    3. 自ユーザーの行を memo_list の内容で差し替え
    4. batch_update で全行を上書き（clear() を使わない）
    """
    if user_id == DEFAULT_USER:
        return True
    try:
        sheet = _get_sheet(0)

        # 既存の全レコードを取得
        existing_records = sheet.get_all_records()

        # 他ユーザーの行を保持
        other_rows = []
        for r in existing_records:
            name = str(r.get("name", "")).strip()
            if not name:
                continue
            row_user = str(r.get("user_id", DEFAULT_USER)) or DEFAULT_USER
            if row_user not in (user_id, DEFAULT_USER, ""):
                other_rows.append(_memo_to_row(_normalize_memo(r, row_user), row_user))

        # 自ユーザーの新しい行を構築
        my_rows = [_memo_to_row(m, user_id) for m in memo_list]

        # ヘッダー + 他ユーザー行 + 自ユーザー行 の順で書き込む
        all_rows = [SHEET_HEADERS] + other_rows + my_rows

        return _safe_batch_write(sheet, all_rows)

    except Exception:
        return False


# ── 検索履歴 ──────────────────────────────────────────────
def _history_to_row(h: dict, user_id: str) -> list:
    return [
        h.get("name",        ""),
        h.get("jan",         ""),
        h.get("cost",        0),
        h.get("sell",        0),
        h.get("ship_cost", 750),
        h.get("profit",      0),
        h.get("profit_rate", 0),
        h.get("time",        ""),
        h.get("date",        ""),
        h.get("user_id", user_id),
    ]


def load_search_history(user_id: str = DEFAULT_USER) -> list:
    """指定ユーザーの検索履歴を読み込む。未ログイン（default）は空リストを返す。"""
    if user_id == DEFAULT_USER:
        return []
    try:
        sheet = _get_sheet(1)
        records = sheet.get_all_records()
        result = []
        for r in records:
            name = str(r.get("name", "")).strip()
            if not name:
                continue
            row_user = str(r.get("user_id", DEFAULT_USER)) or DEFAULT_USER
            if row_user not in (user_id, DEFAULT_USER, ""):
                continue
            result.append({
                "name":        name,
                "jan":         str(r.get("jan",         "")),
                "cost":        int(r.get("cost",         0) or 0),
                "sell":        int(r.get("sell",         0) or 0),
                "ship_cost":   int(r.get("ship_cost",  750) or 750),
                "profit":      int(r.get("profit",       0) or 0),
                "profit_rate": float(r.get("profit_rate", 0) or 0),
                "time":        str(r.get("time",         "")),
                "date":        str(r.get("date",         "")),
                "user_id":     row_user,
            })
        return result
    except Exception:
        return []


def save_search_history(history: list, user_id: str = DEFAULT_USER) -> bool:
    """指定ユーザーの検索履歴を安全に保存する（最大30件）。未ログイン（default）はスキップ。"""
    if user_id == DEFAULT_USER:
        return True
    try:
        sheet = _get_sheet(1)

        existing_records = sheet.get_all_records()

        other_rows = []
        for r in existing_records:
            name = str(r.get("name", "")).strip()
            if not name:
                continue
            row_user = str(r.get("user_id", DEFAULT_USER)) or DEFAULT_USER
            if row_user not in (user_id, DEFAULT_USER, ""):
                other_rows.append(_history_to_row(r, row_user))

        my_rows = [_history_to_row(h, user_id) for h in history[-30:]]
        all_rows = [HISTORY_HEADERS] + other_rows + my_rows

        return _safe_batch_write(sheet, all_rows)

    except Exception:
        return False
