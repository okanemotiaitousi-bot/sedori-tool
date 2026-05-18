import os
import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

# allow_camera=True でiframeにカメラ許可を付与（Streamlit 1.38+）
try:
    _barcode_scanner = components.declare_component(
        "barcode_scanner",
        path=_FRONTEND_DIR,
    )
except Exception:
    _barcode_scanner = None


def barcode_scanner(key=None):
    """リアルタイムバーコードスキャナー。検出したJANコードを返す。未検出時はNone。"""
    if _barcode_scanner is None:
        return None
    return _barcode_scanner(key=key, default=None)
