"""
Google スプレッドシート連携
・sheet1（メモ帳）: 仕入れメモリストを永続化
・sheet2（検索履歴）: 検索履歴・統計を永続化
Streamlit Secrets に gcp_service_account と SPREADSHEET_ID が
設定されていない場合は何もしない（session_state のみで動く）。
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SHEET_HEADERS = [
    "name", "jan", "cost", "sell", "profit", "profit_rate",
    "time", "status", "listed_time", "ship_name",
    "actual_sell", "actual_profit", "actual_rate", "sold_time",
]

HISTORY_HEADERS = ["name", "jan", "cost", "sell", "ship_cost", "profit", "profit_rate", "time", "date"]

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


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


def _get_sheet():
    client = _get_client()
    return client.open_by_key(st.secrets["SPREADSHEET_ID"]).sheet1


def _get_history_sheet():
    """検索履歴シート（2枚目）を取得。なければ自動作成。"""
    client = _get_client()
    wb = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    sheets = wb.worksheets()
    if len(sheets) >= 2:
        return sheets[1]
    return wb.add_worksheet(title="検索履歴", rows=200, cols=len(HISTORY_HEADERS))


def load_memo_list() -> list:
    """スプレッドシートからメモリストを読み込む。失敗時は空リストを返す。"""
    try:
        sheet   = _get_sheet()
        records = sheet.get_all_records()
        result  = []
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
    """メモリストをスプレッドシートに全書き込みする。成功で True を返す。"""
    try:
        sheet = _get_sheet()
        rows  = [SHEET_HEADERS]
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
        sheet.clear()
        sheet.update(rows, "A1")
        return True
    except Exception:
        return False


def load_search_history() -> list:
    """検索履歴シートから履歴を読み込む。失敗時は空リストを返す。"""
    try:
        sheet   = _get_history_sheet()
        records = sheet.get_all_records()
        result  = []
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
    """検索履歴シートに全書き込みする（最大30件）。成功で True を返す。"""
    try:
        sheet = _get_history_sheet()
        rows  = [HISTORY_HEADERS]
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
        sheet.clear()
        sheet.update(rows, "A1")
        return True
    except Exception:
        return False
