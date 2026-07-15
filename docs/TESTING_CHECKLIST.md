# Wing Flap Bird — Manual Testing Checklist (v0.1.0-beta)

Đánh dấu `[x]` sau khi test đạt. Ghi chú lỗi vào cột cuối.

## Môi trường

| # | Kiểm tra | Đạt | Ghi chú |
|---|---|---|---|
| 1 | Windows 10 x64 | [ ] | |
| 2 | Windows 11 x64 | [ ] | |
| 3 | Máy CHƯA cài Python | [ ] | |
| 4 | Không có Internet (rút mạng, chạy lần đầu) | [ ] | |
| 5 | Chạy từ Desktop | [ ] | |
| 6 | Chạy từ Downloads | [ ] | |
| 7 | Đường dẫn có dấu/khoảng trắng (`D:\Trò chơi\Wing Flap\`) | [ ] | |
| 8 | Username Windows có ký tự Unicode | [ ] | |
| 9 | Chạy từ thư mục chỉ đọc (vẫn chơi được; settings có thể không lưu nhưng không crash) | [ ] | |

## Camera

| # | Kiểm tra | Đạt | Ghi chú |
|---|---|---|---|
| 10 | Webcam laptop tích hợp | [ ] | |
| 11 | USB webcam | [ ] | |
| 12 | Không có webcam → banner cảnh báo + chơi bằng SPACE | [ ] | |
| 13 | Webcam đang bị Zoom/Teams chiếm → thông báo, không crash | [ ] | |
| 14 | Camera index khác 0 (chọn trong Settings) | [ ] | |
| 15 | Rút webcam giữa lúc chơi → game không đứng hình, tự thử kết nối lại | [ ] | |
| 16 | Settings > Test camera: preview hiện, Stop test tắt camera | [ ] | |
| 17 | Đổi camera → hiện gợi ý hiệu chỉnh lại | [ ] | |

## Gameplay

| # | Kiểm tra | Đạt | Ghi chú |
|---|---|---|---|
| 18 | Calibration thành công (3 pha + lưu, lần sau không phải làm lại) | [ ] | |
| 19 | Calibration thất bại / bấm S bỏ qua → dùng mặc định, vẫn chơi được | [ ] | |
| 20 | Vỗ 2 tay → chim bay lên rõ (~100px), chữ FLAP!, viền webcam xanh | [ ] | |
| 21 | Giữ tay trên cao → KHÔNG bay liên tục | [ ] | |
| 22 | Chơi hoàn toàn bằng SPACE | [ ] | |
| 23 | Đổi difficulty Easy↔Normal → lượt mới áp dụng ngay (không cần restart app) | [ ] | |
| 24 | ESC → pause; resume không làm chim tự bay (pending flap bị xóa) | [ ] | |
| 25 | Restart từ pause → reset điểm/vận tốc/cột | [ ] | |
| 26 | Game over → R chơi lại, M về menu | [ ] | |

## Settings & dữ liệu

| # | Kiểm tra | Đạt | Ghi chú |
|---|---|---|---|
| 27 | Mọi setting đổi xong tự lưu, mở lại app còn nguyên | [ ] | |
| 28 | Fullscreen bật/tắt ngay | [ ] | |
| 29 | Tắt webcam preview → panel biến mất trong gameplay | [ ] | |
| 30 | Reset high score (có hộp thoại xác nhận) | [ ] | |
| 31 | Reset calibration → lần chơi sau yêu cầu hiệu chỉnh lại | [ ] | |
| 32 | Reset all settings → về mặc định (ngôn ngữ vi, easy...) | [ ] | |
| 33 | Đổi ngôn ngữ vi↔en → toàn bộ menu đổi ngay | [ ] | |
| 34 | Dữ liệu nằm trong `%LOCALAPPDATA%\WingFlapBird`, KHÔNG có file mới sinh ra cạnh WingFlapBird.exe | [ ] | |

## Khác

| # | Kiểm tra | Đạt | Ghi chú |
|---|---|---|---|
| 35 | Privacy notice hiện đúng 1 lần đầu | [ ] | |
| 36 | Nút donate: ẩn/disabled khi chưa cấu hình URL; khi có URL chỉ mở lúc bấm | [ ] | |
| 37 | Credits mở trang GitHub khi bấm | [ ] | |
| 38 | Quit → process thoát hẳn (kiểm tra Task Manager, không còn thread camera) | [ ] | |
| 39 | Log ghi tại `%LOCALAPPDATA%\WingFlapBird\logs\wing_flap_bird.log`, không chứa frame/landmark | [ ] | |
| 40 | FPS game ~60, FPS camera ~20-30, RAM không tăng liên tục sau 10 phút | [ ] | |
