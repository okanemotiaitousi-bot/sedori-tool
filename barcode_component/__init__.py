import os
import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
_barcode_scanner = components.declare_component("barcode_scanner", path=_FRONTEND_DIR)

def barcode_scanner(key=None):
    """リアルタイムバーコードスキャナー。検出したJANコードを返す。未検出時はNone。"""
    return _barcode_scanner(key=key, default=None)
