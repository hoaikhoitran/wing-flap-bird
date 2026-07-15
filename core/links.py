"""Cac lien ket ngoai. KHONG tu bia tai khoan donate.

Developer: dien DONATE_URL that truoc khi release neu muon bat nut donate.
Khi DONATE_URL rong, nut donate se bi disable va hien huong dan.
Moi URL chi duoc mo khi NGUOI DUNG chu dong bam (webbrowser.open),
khong bao gio tu dong mo.
"""
from __future__ import annotations

DONATE_URL = ""  # TODO(developer): dien URL donate that (VD: GitHub Sponsors, Ko-fi)
REPOSITORY_URL = "https://github.com/hoaikhoitran/wing-flap-bird"
RELEASES_URL = REPOSITORY_URL + "/releases"

# Anh QR nhan tien do developer cung cap (crop tu anh MBBank nguyen ban,
# KHONG tao lai / khong decode). Xem scripts/crop_support_qr.py.
SUPPORT_QR_RESOURCE = "assets/support/vietqr-support.png"


def donate_available() -> bool:
    return bool(DONATE_URL.strip())


def support_qr_available() -> bool:
    """Co anh QR ung ho de hien trong man Support Developer khong."""
    try:
        from core.paths import resource_path
        return resource_path(SUPPORT_QR_RESOURCE).exists()
    except Exception:
        return False
