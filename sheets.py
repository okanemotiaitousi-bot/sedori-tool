"""
Google スプレッドシート連携
・sheet1（メモ帳）: 仕入れメモリストを永続化
・sheet2（検索履歴）: 検索履歴・統計を永続化

【設計方針】
- Streamlit Secrets に gcp_service_account と SPREADSHEET_ID がない場合は
  session_state のみで動作する（ローカル開発・テスト用）
- 書き込みは clear() を使わず batch_update() で全行上書きする
  → clear() と update() の間にデータが消える瞬間をなくす
- 書き込み失敗時は指数バックオフで最大3回リトライする
- 将来の複数ユーザー対応：シート名をユーザーIDにすることで
  ユーザーごとにシートを分離できる構造にしてある（_get_sheet(user_id)）
"""
import time
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SHEET_HEADERS = [
    "name", "jan", "cost", "sell", "profit", "profit_rate",
    "time", "status", "listed_time", "ship_name",
    "actual_sell", "actual_profit", "actual_rate", "sold_time",
]
HISTORY_HEADERS = [
    "name", "jan", "cost", "sell", "ship_cost",
    "profit", "profit_rate", "time", "date",
]

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ── 接続 ──────────────────────────────────────────────────
def is_enabled() -> bool:
    """Secrets に必要なキーが揃っているか確認"""
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


def _get_sheet(sheet_index: int = 0):
    """sheet_index 番目のシートを返す（0=メモ帳, 1=検索履歴）"""
    client = _get_client()
    wb = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    sheets = wb.worksheets()
    if sheet_index < len(sheets):
        return sheets[sheet_index]
    # 存在しなければ自動作成
    titles = {0: "メモ帳", 1: "検索履歴"}
    return wb.add_worksheet(
        title=titles.get(sheet_index, f"sheet{sheet_index}"),
        rows=500,
        cols=20,
    )


# ── 安全な書き込みヘルパー ────────────────────────────────
def _safe_update(sheet, rows: list, max_retries: int = 3) -> bool:
    """
    clear() を使わずに batch_update で全行を上書きする。
    - 既存データ行数 >= 新データ行数 の場合、余った行をブランクで上書きして
      古いデータが残らないようにする。
    - 書き込み失敗時は指数バックオフでリトライする。
    """
    for attempt in range(max_retries):
        try:
            # 現在のシート行数を取得（不要な行を消すため）
            existing = sheet.get_all_values()
            existing_rows = len(existing)

            # 新データで上書き
            sheet.update(rows, "A1")

            # 余った古い行をブランクで上書き（データ残留防止）
            new_rows = len(rows)
            if existing_rows > new_rows:
                blank = [[""] * len(SHEET_HEADERS)] * (existing_rows - new_rows)
                start = new_rows + 1
                sheet.update(blank, f"A{start}")

            return True

        except gspread.exceptions.APIError as e:
            # 429 = Quota exceeded → 長めに待つ
            status = getattr(e.response, "status_code", 0)
            wait = 10 if status == 429 else (2 ** attempt)
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                return False
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return False

    return False


# ── メモ帳 ────────────────────────────────────────────────
def load_memo_list() -> list:
    """スプレッドシートからメモリストを読み込む。失敗時は空リストを返す。"""
    try:
        sheet = _get_sheet(0)
        records = sheet.get_all_records()
        result = []
        for r in records:
            name = str(r.get("name", "")).strip()
            if not name:
                continue
            result.append({
                "name":          name,
                "jan":           str(r.get("jan",   "")),
                "cost":          int(r.get("cost",   0) or 0),
                "sell":          int(r.get("sell",   0) or 0),
                "profit":        int(r.get("profit", 0) or 0),
                "profit_rate":   float(r.get("profit_rate", 0) or 0),
                "time":          str(r.get("time",   "")),
                "status":        str(r.get("status", "候補")) or "候補",
                "listed_time":   str(r.get("listed_time",   "")),
                "ship_name":     str(r.get("ship_name",     "")),
                "actual_sell":   int(r.get("actual_sell",   0) or 0),
                "actual_profit": int(r.get("actual_profit", 0) or 0),
                "actual_rate":   float(r.get("actual_rate", 0) or 0),
                "sold_time":     str(r.get("sold_time", "")),
            })
        return result
    except Exception:
        return []


def save_memo_list(memo_list: list) -> bool:
    """メモリストをスプレッドシートに安全に書き込む。成功で True を返す。"""
    try:
        sheet = _get_sheet(0)
        rows = [SHEET_HEADERS]
        for m in memo_list:
            rows.append([
                m.get("name",          ""),
                m.get("jan",           ""),
                m.get("cost",          0),
                m.get("sell",          0),
                m.get("profit",        0),
                m.get("profit_rate",   0),
                m.get("time",          ""),
                m.get("status",        "候補"),
                m.get("listed_time",   ""),
                m.get("ship_name",     ""),
                m.get("actual_sell",   0),
                m.get("actual_profit", 0),
                m.get("actual_rate",   0),
                m.get("sold_time",     ""),
            ])
        return _safe_update(sheet, rows)
    except Exception:
        return False


# ── 検索履歴 ──────────────────────────────────────────────
def load_search_history() -> list:
    """検索履歴シートから履歴を読み込む。失敗時は空リストを返す。"""
    try:
        sheet = _get_sheet(1)
        records = sheet.get_all_records()
        result = []
        for r in records:
            name = str(r.get("name", "")).strip()
            if not name:
                continue
            result.append({
                "name":        name,
                "jan":         str(r.get("jan",         "")),
                "cost":        int(r.get("cost",         0) or 0),
                "sell":        int(r.get("sell",         0) or 0),
                "ship_cost":   int(r.get("ship_cost",    750) or 750),
                "profit":      int(r.get("profit",       0) or 0),
                "profit_rate": float(r.get("profit_rate", 0) or 0),
                "time":        str(r.get("time",         "")),
                "date":        str(r.get("date",         "")),
            })
        return result
    except Exception:
        return []


def save_search_history(history: list) -> bool:
    """検索履歴シートに安全に書き込む（最大30件）。成功で True を返す。"""
    try:
        sheet = _get_sheet(1)
        rows = [HISTORY_HEADERS]
        for h in history[-30:]:
            rows.append([
                h.get("name",        ""),
                h.get("jan",         ""),
                h.get("cost",        0),
                h.get("sell",        0),
                h.get("ship_cost",   750),
                h.get("profit",      0),
                h.get("profit_rate", 0),
                h.get("time",        ""),
                h.get("date",        ""),
            ])
        return _safe_update(sheet, rows)
    except Exception:
        return False
