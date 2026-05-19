"""
Google スプレッドシート連携
仕入れメモ帳のデータを永続化する。
Streamlit Secrets に gcp_service_account と SPREADSHEET_ID が
設定されていない場合は何もしない（session_state のみで動く）。
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SHEET_HEADERS = [
    "name", "jan", "cost", "sell", "profit", "profit_rate",
    "time", "status", "listed_time",
    "actual_sell", "actual_profit", "actual_rate", "sold_time",
]

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
