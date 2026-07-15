# Visual Audit — Wing Flap Bird (baseline trước redesign 2.5D)

*Ngày audit: 2026-07-15 · Nguồn: screenshot render THẬT từ game
(`python main.py --capture-readme --capture-baseline`) — không mockup,
không AI image. Baseline: `docs/screenshots/baseline/`*

## 1. Font — LỖI NGHIÊM TRỌNG NHẤT

Runtime dùng `pygame.font.SysFont("arial"...)`; trong môi trường render
thực tế **mọi ký tự tiếng Việt có dấu móc/mũ kép đều thành ô vuông
(tofu)**:

| Màn hình | Chuỗi hỏng quan sát được |
|---|---|
| Main menu | `CHƠI→CH▯I`, `CÀI ĐẶT→CÀI Đ▯T`, `CÁCH CHƠI→CÁCH CH▯I`, `ỦNG HỘ NHÀ PHÁT TRIỂN→▯NG H▯...TRI▯N`, `GIỚI THIỆU→GI▯I THI▯U`, tagline `Vỗ...nhỏ...để` vỡ 3 chỗ, `Kỷ lục: 7→K▯ l▯c: 7` |
| Settings | `ĐẶT`, `Độ khó`, `Dễ`, `Độ nhạy cử chỉ`, `Ngôn ngữ`, `Tiếng Việt`, `Hiệu ứng`, `Âm lượng`, `Nhạc nền`, `BẬT/TẮT`, `Thử camera`, `Quét lại`, `Xóa kỷ lục/hiệu chỉnh`, `Khôi phục mặc định`, `QUAY LẠI` — hỏng đồng loạt |
| Gameplay HUD | `Kỷ lục: 7` hỏng ngay cạnh score |

→ Bắt buộc bundle **Be Vietnam Pro** + `core/font_manager.py`, cấm
`SysFont`/`Font(None)` (Phase 6). Vị trí SysFont hiện tại:
`game/ui.py:_load_font`, `game/widgets.py` (tooltip 13px), `main.py`
(error screen).

## 2. Asset còn là primitive

| Asset | Hiện trạng |
|---|---|
| Nhân vật | 1 con chim vàng vẽ ellipse/polygon (`game/player.py`), rất nhỏ trên nền, KHÔNG có lựa chọn nhân vật |
| Obstacle | **Pipe xanh lá** 2 rectangle + rim (`game/obstacle.py`) — giống Flappy Bird, bị cấm theo art direction mới |
| Background | 1 lớp gradient + mây ellipse trắng + ground sọc chéo (`game/ui.py:Background`) — không parallax, không chiều sâu |
| Shadow | Hoàn toàn không có (không contact shadow, không cast shadow) |
| UI | 6 button rectangle bo góc GIỐNG HỆT nhau xếp dọc; panel phẳng không depth |
| Icon | Không có; một chỗ dùng ký tự `!`/`⚠` thay icon |

## 3. Animation còn cứng

- Bird: cánh 1 polygon dao động sin — không có frame animation thật.
- Không idle/hurt/death frames. Game over: nhân vật đứng im.
- Menu: buttons chỉ đổi màu hover; không press/transition animation.
- Không có wind trail, feather; particle chỉ là chấm tròn.

## 4. Màu sắc thiếu nhất quán

- Màu hard-code rải rác: `game/ui.py` (sky/ground/state colors),
  `game/widgets.py` (COL_*), `game/player.py`, `game/obstacle.py`,
  từng screen tự khai màu panel khác nhau — chưa có module theme chung.

## 5. Layout/overlap

- Không phát hiện overlap trong screenshot baseline (menu/settings/
  gameplay); tuy nhiên toàn bộ widget đặt bằng **số pixel tuyệt đối**
  → dễ vỡ khi đổi text vi/en (Phase 9 cần layout system).
- Score "2" ở gameplay bị đè lên pipe phía sau — chấp nhận được nhưng
  cần outline/panel rõ hơn.

## 6. Màn hình giống prototype nhất → cần redesign

1. Gameplay (pipe xanh + bird primitive + nền 1 lớp) — nặng nhất.
2. Main menu (6 rectangle + title text thuần).
3. Game over (chỉ text + phím tắt, không button).
4. How to Play (stick figure que — giữ concept, nâng chất lượng).

## 7. README placeholder

- Khung ASCII "preview" + dòng `*(TODO: thay bằng screenshot/GIF thật...)*`
  → Phase 14 xóa, thay bằng screenshot thật từ capture mode.

## 8. Baseline screenshots

`docs/screenshots/baseline/`: `main-menu.png`, `gameplay.png`,
`settings.png`, `how-to-play.png`, `support.png`, `game-over.png`
(capture bằng renderer thật, seed 20260715, `--no-camera`).

## 9. Điểm ĐANG hoạt động tốt (giữ nguyên hành vi)

- Flap pulse ring + chữ FLAP! + particle đã phát đúng lúc.
- Autopilot capture đạt score 2, ≥3 cổng trên màn → pipeline screenshot
  dùng được cho README sau redesign.
- 47/47 test pass; smoke source PASS trước audit.
