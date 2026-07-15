"""Da ngon ngu toi gian (vi/en) cho UI.

Su dung:
    from game import i18n
    i18n.set_language("vi")
    label = i18n.tr("menu.play")
Key thieu -> tra ve chinh key do (de phat hien nhanh khi dev).
"""
from __future__ import annotations

_LANG = "vi"

STRINGS: dict[str, dict[str, str]] = {
    # ---------------- Menu chinh ----------------
    "menu.play": {"vi": "CHƠI", "en": "PLAY"},
    "menu.settings": {"vi": "CÀI ĐẶT", "en": "SETTINGS"},
    "menu.how_to_play": {"vi": "CÁCH CHƠI", "en": "HOW TO PLAY"},
    "menu.support": {"vi": "ỦNG HỘ NHÀ PHÁT TRIỂN", "en": "SUPPORT DEVELOPER"},
    "menu.credits": {"vi": "GIỚI THIỆU", "en": "CREDITS"},
    "menu.quit": {"vi": "THOÁT", "en": "QUIT"},
    "menu.tagline": {"vi": "Vỗ hai tay như chim để bay lên!",
                     "en": "Flap your arms like a bird to fly!"},
    "menu.high_score": {"vi": "Kỷ lục: {score}", "en": "Best: {score}"},

    # ---------------- Privacy notice ----------------
    "privacy.title": {"vi": "QUYỀN RIÊNG TƯ WEBCAM", "en": "WEBCAM PRIVACY"},
    "privacy.body1": {
        "vi": "Wing Flap Bird xử lý hình ảnh webcam trực tiếp trên máy.",
        "en": "Wing Flap Bird processes webcam images locally on your device."},
    "privacy.body2": {
        "vi": "Game không ghi, lưu hoặc tải video của bạn lên Internet.",
        "en": "The game does not record, store or upload your video."},
    "privacy.body3": {
        "vi": "Bạn có thể chơi không cần camera bằng phím SPACE.",
        "en": "You can play without a camera using the SPACE key."},
    "privacy.more": {"vi": "Chi tiết: xem file PRIVACY.txt kèm theo game.",
                     "en": "Details: see PRIVACY.txt shipped with the game."},
    "privacy.accept": {"vi": "TÔI ĐÃ HIỂU", "en": "I UNDERSTAND"},

    # ---------------- Settings ----------------
    "settings.title": {"vi": "CÀI ĐẶT", "en": "SETTINGS"},
    "settings.camera": {"vi": "Camera", "en": "Camera"},
    "settings.camera_item": {"vi": "Camera {index}", "en": "Camera {index}"},
    "settings.camera_test": {"vi": "Thử camera", "en": "Test camera"},
    "settings.camera_stop_test": {"vi": "Dừng thử", "en": "Stop test"},
    "settings.camera_refresh": {"vi": "Quét lại", "en": "Refresh"},
    "settings.camera_scanning": {"vi": "Đang quét camera...",
                                 "en": "Scanning cameras..."},
    "settings.camera_none": {"vi": "Không tìm thấy camera",
                             "en": "No camera found"},
    "settings.camera_busy": {
        "vi": "Không mở được - camera có thể đang bị app khác dùng",
        "en": "Cannot open - camera may be in use by another app"},
    "settings.difficulty": {"vi": "Độ khó", "en": "Difficulty"},
    "settings.diff_easy": {"vi": "Dễ", "en": "Easy"},
    "settings.diff_normal": {"vi": "Thường", "en": "Normal"},
    "settings.sensitivity": {"vi": "Độ nhạy cử chỉ", "en": "Gesture sensitivity"},
    "settings.sound": {"vi": "Hiệu ứng âm thanh", "en": "Sound effects"},
    "settings.music": {"vi": "Nhạc nền", "en": "Music"},
    "settings.volume": {"vi": "Âm lượng", "en": "Volume"},
    "settings.fullscreen": {"vi": "Toàn màn hình", "en": "Fullscreen"},
    "settings.webcam_preview": {"vi": "Khung webcam trong game",
                                "en": "Webcam preview in game"},
    "settings.show_fps": {"vi": "Hiện FPS", "en": "Show FPS"},
    "settings.language": {"vi": "Ngôn ngữ", "en": "Language"},
    "settings.debug": {"vi": "Debug (nâng cao)", "en": "Debug (advanced)"},
    "settings.data": {"vi": "DỮ LIỆU", "en": "DATA"},
    "settings.reset_high_score": {"vi": "Xóa kỷ lục", "en": "Reset high score"},
    "settings.reset_calibration": {"vi": "Xóa hiệu chỉnh",
                                   "en": "Reset calibration"},
    "settings.reset_all": {"vi": "Khôi phục mặc định", "en": "Reset all settings"},
    "settings.back": {"vi": "QUAY LẠI", "en": "BACK"},
    "settings.on": {"vi": "BẬT", "en": "ON"},
    "settings.off": {"vi": "TẮT", "en": "OFF"},
    "settings.confirm": {"vi": "Bạn có chắc không?", "en": "Are you sure?"},
    "settings.yes": {"vi": "CÓ", "en": "YES"},
    "settings.no": {"vi": "KHÔNG", "en": "NO"},

    # ---------------- How to play ----------------
    "howto.title": {"vi": "CÁCH CHƠI", "en": "HOW TO PLAY"},
    "howto.step1": {"vi": "1. Đứng trước webcam, cách 1.5-2.5 m",
                    "en": "1. Stand 1.5-2.5 m in front of the webcam"},
    "howto.step2": {"vi": "2. Camera phải thấy vai, khuỷu tay và cổ tay",
                    "en": "2. Shoulders, elbows and wrists must be visible"},
    "howto.step3": {"vi": "3. Nâng hai tay lên cao qua vai",
                    "en": "3. Raise both arms above your shoulders"},
    "howto.step4": {"vi": "4. Hạ hai tay xuống dứt khoát",
                    "en": "4. Bring both arms down quickly"},
    "howto.step5": {"vi": "5. Mỗi chu kỳ tạo một lần bay",
                    "en": "5. Each full cycle gives one flap"},
    "howto.step6": {"vi": "6. Né các chướng ngại vật để ghi điểm",
                    "en": "6. Dodge the obstacles to score"},
    "howto.fallback": {"vi": "SPACE: bay (dự phòng)   ESC: tạm dừng/quay lại",
                       "en": "SPACE: flap (fallback)   ESC: pause/back"},
    "howto.run_calibration": {"vi": "Chạy hiệu chỉnh", "en": "Run calibration"},
    "howto.test_gesture": {"vi": "Test cử chỉ", "en": "Test gesture"},
    "howto.stop_test": {"vi": "Dừng test", "en": "Stop test"},
    "howto.flap_count": {"vi": "Số lần vỗ: {n}", "en": "Flaps: {n}"},

    # ---------------- Credits / Donate ----------------
    "credits.title": {"vi": "GIỚI THIỆU", "en": "CREDITS"},
    "credits.developer": {"vi": "Phát triển bởi", "en": "Developed by"},
    "credits.open_repo": {"vi": "Mở trang GitHub", "en": "Open GitHub page"},
    "credits.tech": {"vi": "Công nghệ sử dụng", "en": "Built with"},
    "credits.licenses": {
        "vi": "Giấy phép bên thứ ba: xem THIRD_PARTY_NOTICES.txt",
        "en": "Third-party licenses: see THIRD_PARTY_NOTICES.txt"},
    "donate.title": {"vi": "ỦNG HỘ NHÀ PHÁT TRIỂN", "en": "SUPPORT DEVELOPER"},
    "donate.body1": {
        "vi": "Wing Flap Bird được phát hành miễn phí.",
        "en": "Wing Flap Bird is free to play."},
    "donate.body2": {
        "vi": "Nếu bạn thích trò chơi, bạn có thể ủng hộ để hỗ trợ các bản cập nhật tiếp theo.",
        "en": "If you enjoy the game, you can support future development."},
    "donate.body3": {
        "vi": "Việc ủng hộ hoàn toàn tự nguyện và không mở khóa lợi thế trong game.",
        "en": "Donations are optional and do not unlock gameplay advantages."},
    "donate.open": {"vi": "Mở trang ủng hộ", "en": "Open donate page"},
    "donate.missing": {
        "vi": "(Chưa cấu hình link ủng hộ - developer cần điền DONATE_URL trong core/links.py)",
        "en": "(Donate link not configured - developer must set DONATE_URL in core/links.py)"},
    "donate.scan_hint": {
        "vi": "Quét mã bằng ứng dụng ngân hàng để ủng hộ",
        "en": "Scan with your banking app to support"},

    # ---------------- Pause ----------------
    "pause.title": {"vi": "TẠM DỪNG", "en": "PAUSED"},
    "pause.resume": {"vi": "TIẾP TỤC", "en": "RESUME"},
    "pause.restart": {"vi": "CHƠI LẠI", "en": "RESTART"},
    "pause.settings": {"vi": "CÀI ĐẶT", "en": "SETTINGS"},
    "pause.main_menu": {"vi": "VỀ MENU CHÍNH", "en": "MAIN MENU"},
    "pause.quit": {"vi": "THOÁT GAME", "en": "QUIT"},

    # ---------------- HUD / gameplay ----------------
    "hud.no_pose": {"vi": "KHÔNG NHẬN DIỆN ĐƯỢC", "en": "NO BODY DETECTED"},
    "hud.arms_down": {"vi": "TAY THẤP", "en": "ARMS DOWN"},
    "hud.arms_up": {"vi": "TAY CAO", "en": "ARMS UP"},
    "hud.flap": {"vi": "VỖ CÁNH!", "en": "FLAP!"},
    "hud.no_webcam": {"vi": "KHÔNG CÓ WEBCAM", "en": "NO WEBCAM"},
    "hud.no_signal": {"vi": "KHÔNG CÓ TÍN HIỆU", "en": "NO SIGNAL"},
    "hud.ready": {"vi": "SẴN SÀNG", "en": "READY"},
    "hud.cooling": {"vi": "HỒI...", "en": "COOLING..."},
    "hud.camera_warning": {
        "vi": "{msg} - Dùng phím SPACE để vỗ cánh",
        "en": "{msg} - Use SPACE to flap"},
    "hud.best": {"vi": "Kỷ lục: {score}", "en": "Best: {score}"},
    "hud.fps": {"vi": "FPS game: {game:>4.0f}   FPS camera: {cam:>4.0f}",
                "en": "Game FPS: {game:>4.0f}   Camera FPS: {cam:>4.0f}"},

    "ready.title": {"vi": "CHUẨN BỊ...", "en": "GET READY..."},
    "ready.instruction": {"vi": "Vỗ hai tay để bay", "en": "Flap your arms to fly"},

    "over.title": {"vi": "GAME OVER", "en": "GAME OVER"},
    "over.score": {"vi": "Điểm: {score}", "en": "Score: {score}"},
    "over.new_record": {"vi": "★ KỶ LỤC MỚI! ★", "en": "★ NEW RECORD! ★"},
    "over.restart": {"vi": "R  -  Chơi lại  (hoặc vỗ cánh)",
                     "en": "R  -  Restart  (or flap)"},
    "over.menu": {"vi": "M  -  Về menu chính", "en": "M  -  Main menu"},
    "over.esc": {"vi": "ESC  -  Về menu chính", "en": "ESC  -  Main menu"},

    # ---------------- Calibration ----------------
    "calib.title": {"vi": "HIỆU CHỈNH CAMERA", "en": "CAMERA CALIBRATION"},
    "calib.detect": {"vi": "Đang nhận diện cơ thể... Hãy đứng giữa khung hình",
                     "en": "Detecting body... Stand in the middle of the frame"},
    "calib.hold_low": {"vi": "Giữ hai tay THẤP (dọc theo thân người)",
                       "en": "Hold both arms DOWN (along your body)"},
    "calib.raise_high": {"vi": "Nâng hai tay LÊN CAO qua vai",
                         "en": "Raise both arms UP above shoulders"},
    "calib.done": {"vi": "Hiệu chỉnh hoàn tất!", "en": "Calibration complete!"},
    "calib.failed": {"vi": "Hiệu chỉnh thất bại - dùng thiết lập mặc định",
                     "en": "Calibration failed - using defaults"},
    "calib.hints": {"vi": "S - bỏ qua (dùng mặc định)     R - làm lại     ESC - quay lại",
                    "en": "S - skip (use defaults)     R - retry     ESC - back"},
    "calib.too_close": {"vi": "Bạn đứng quá gần - hãy lùi lại",
                        "en": "Too close - please step back"},
    "calib.too_far": {"vi": "Bạn đứng quá xa - hãy tiến lại gần",
                      "en": "Too far - please step closer"},
    "calib.low_visibility": {
        "vi": "Không thấy rõ hai tay - kiểm tra ánh sáng và khung hình",
        "en": "Arms not clearly visible - check lighting and framing"},

    # ---------------- Loi camera ----------------
    "cam.retry": {"vi": "Thử lại camera", "en": "Retry camera"},
    "cam.keyboard": {"vi": "Chơi bằng bàn phím", "en": "Continue with keyboard"},

    # ---------------- Bo sung ----------------
    "settings.recalib_hint": {
        "vi": "Đã đổi camera - nên chạy lại hiệu chỉnh (mục CÁCH CHƠI)",
        "en": "Camera changed - please re-run calibration (HOW TO PLAY)"},
    "sens.low": {"vi": "Thấp", "en": "Low"},
    "sens.normal": {"vi": "Vừa", "en": "Normal"},
    "sens.high": {"vi": "Cao", "en": "High"},
    "error.title": {"vi": "RẤT TIẾC - GAME GẶP LỖI", "en": "SORRY - THE GAME CRASHED"},
    "error.body": {"vi": "Chi tiết lỗi đã được ghi vào file log:",
                   "en": "Error details were written to the log file:"},
    "error.open_log": {"vi": "O - Mở thư mục log", "en": "O - Open log folder"},
    "error.restart": {"vi": "R - Khởi động lại game", "en": "R - Restart game"},
    "error.quit": {"vi": "ESC - Thoát", "en": "ESC - Quit"},
}


def set_language(lang: str) -> None:
    global _LANG
    _LANG = lang if lang in ("vi", "en") else "vi"


def get_language() -> str:
    return _LANG


def tr(key: str, **fmt) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_LANG) or entry.get("vi") or key
    if fmt:
        try:
            return text.format(**fmt)
        except (KeyError, ValueError):
            return text
    return text
