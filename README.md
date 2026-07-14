# 🐦 Wing Flap — Vỗ cánh để bay!

Game lấy cảm hứng từ Flappy Bird, nhưng **không dùng bàn phím để bay**:
bạn phải **vỗ hai tay như chim trước webcam**. MediaPipe Pose nhận diện
động tác, mỗi chu kỳ *nâng tay lên → hạ tay xuống đủ nhanh* = một lần
vỗ cánh đẩy nhân vật bay lên.

```text
┌─────────────────────────────────────────────┐
│   ĐIỂM: 12                    ┌──────────┐  │
│            ██                 │ webcam + │  │
│    🐦      ██                 │ skeleton │  │
│            ██     ██          └──────────┘  │
│    ██             ██           TAY CAO      │
│    ██             ██          [████████░]   │
└─────────────────────────────────────────────┘
```

## 1. Cài đặt

Yêu cầu **Python 3.9 – 3.12** (MediaPipe chưa hỗ trợ 3.13):

```bash
python --version
pip install -r requirements.txt
python main.py
```

Khuyến nghị dùng virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
```

> **Lưu ý về model pose:** với MediaPipe bản mới (≥ 0.10.30, đã gỡ API
> `mp.solutions`), game dùng Tasks API và cần file model
> `assets/models/pose_landmarker_lite.task` (~5.8 MB). File này được
> **tự động tải về trong lần chạy đầu tiên**; nếu máy không có mạng,
> tải thủ công tại
> `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task`
> rồi đặt vào `assets/models/`. Với MediaPipe cũ (còn `mp.solutions`),
> game tự dùng API legacy, không cần model ngoài.

(Tùy chọn) sinh file âm thanh WAV vào `assets/` — không bắt buộc, vì
game tự tổng hợp âm thanh bằng NumPy nếu không có file:

```bash
python tools/generate_assets.py
```

## 2. Cách chơi

1. Chạy `python main.py`, đứng cách webcam **1.5 – 2.5 m** sao cho thấy
   được từ hông trở lên.
2. Ở menu nhấn **ENTER** (hoặc vỗ cánh) — lần đầu game sẽ chạy
   **hiệu chỉnh ~5 giây**:
   - Đứng giữa khung hình → *"Đang nhận diện cơ thể"*
   - Giữ hai tay thấp ~1 giây → *"Giữ hai tay THẤP"*
   - Nâng hai tay cao qua vai ~1 giây → *"Nâng hai tay LÊN CAO"*
   - *"Hiệu chỉnh hoàn tất!"* → vào game.
3. Sau hiệu chỉnh, game vào màn **CHUẨN BỊ** đếm ngược `3-2-1-GO` (~2.5 s):
   chim đứng yên, cột chưa chạy, webcam vẫn nhận diện — đủ thời gian vào
   tư thế. Sau chữ **GO!** trọng lực mới bắt đầu (và trong 1 giây đầu
   trọng lực chỉ bằng một nửa để không chết oan).
4. **Vỗ hai tay** (nâng lên qua vai rồi hạ xuống dứt khoát) để bay lên
   ~100 px mỗi lần. Mỗi chu kỳ chỉ tính **một** lần vỗ, cooldown 220 ms
   (vỗ được ~2–3 lần/giây). Cột đầu tiên chỉ xuất hiện sau 3 giây.
5. Bay qua khoảng trống giữa các cột để ghi điểm. Chạm cột, chạm đất
   hoặc bay quá mép trên màn hình → thua.

### Phím điều khiển

| Phím    | Chức năng                                        |
|---------|--------------------------------------------------|
| `ESC`   | Thoát game                                       |
| `R`     | Chơi lại sau khi game over                       |
| `C`     | Chạy lại hiệu chỉnh (ở menu hoặc màn game over)  |
| `S`     | Bỏ qua hiệu chỉnh (dùng ngưỡng mặc định)         |
| `SPACE` | Vỗ cánh **dự phòng/debug** — không phải điều khiển chính; tự kích hoạt khi webcam lỗi |
| `F1`    | Bật / tắt overlay debug ngay trong game          |

## 3. Chọn đúng webcam

Máy có nhiều camera (laptop + camera rời, camera ảo của OBS...):

```bash
python main.py --camera 1     # thử 0, 1, 2...
```

hoặc sửa `CAMERA_INDEX` trong [config.py](config.py). Muốn chơi không
cần webcam: `python main.py --no-camera` (bay bằng SPACE).

## 4. Điều chỉnh độ nhạy nhận diện

Mọi ngưỡng nằm trong `FlapDetectorConfig` ở [config.py](config.py).
Tất cả khoảng cách được **chuẩn hóa theo chiều rộng vai** nên không phụ
thuộc đứng gần hay xa webcam.

| Tham số                | Mặc định | Ý nghĩa — chỉnh khi nào                                        |
|------------------------|----------|----------------------------------------------------------------|
| `up_margin_ratio`      | `0.35`   | Tay phải cao hơn vai bao nhiêu mới tính "tay cao". **Giảm** nếu phải giơ tay quá cao |
| `down_margin_ratio`    | `0.10`   | Ngưỡng "tay thấp" (nằm ngay trên vai). Tăng nếu khó về trạng thái thấp |
| `min_down_speed_ratio` | `1.1`    | Tốc độ hạ tay tối thiểu. **Giảm** nếu vỗ nhẹ không ăn, **tăng** nếu bị nhận nhầm |
| `flap_cooldown`        | `0.22`   | Lấy từ `flap_cooldown_ms` của độ khó (easy 220 ms, normal 300 ms; không nên quá 450 ms) |
| `smoothing_alpha`      | `0.45`   | Làm mượt landmark. Giảm → mượt hơn nhưng phản hồi trễ hơn      |
| `min_visibility`       | `0.5`    | Độ tin cậy tối thiểu của landmark trước khi xử lý              |

Chạy **hiệu chỉnh** (phím `C`) sẽ tự tính `up/down_margin_ratio` theo
biên độ tay của chính bạn — nên làm trước khi chỉnh tay các số trên.

## 5. Độ khó & vật lý

Game có 2 chế độ trong [config.py](config.py):

```python
DIFFICULTY = "easy"     # hoặc "normal"
```

Toàn bộ vật lý dùng **hệ delta-time** (px/s, px/s²) — không trộn với hệ
per-frame. Quy đổi: `giá_trị_per_frame × 60` (vận tốc) hoặc `× 3600`
(gia tốc) tại 60 FPS.

| Tham số (easy)   | Giá trị   | Ý nghĩa                                          |
|------------------|-----------|--------------------------------------------------|
| `gravity`        | `800`     | ≈0.22 px/frame² — rơi từ giữa màn hình ~1.6 s    |
| `flap_force`     | `-400`    | Vận tốc được **đặt** (không cộng dồn) → bay lên ~100 px |
| `max_fall_speed` | `210`     | ≈3.5 px/frame — vận tốc rơi không tăng vô hạn    |
| `pipe_speed`     | `150`     | ≈2.5 px/frame                                    |
| `pipe_gap_*`     | `210–250` | Khoảng trống rộng cho người mới (cửa sổ 700 px)  |
| `first_obstacle_delay` | `3.0` | Cột đầu xuất hiện sau 3 s                     |
| `start_delay`    | `2.5`     | Đếm ngược GET_READY trước khi có trọng lực       |
| `start_grace_period` | `1.0` | 1 s đầu sau GO trọng lực giảm một nửa           |
| `flap_cooldown_ms` | `220`   | Vỗ được ~2–3 lần/giây                            |

Chế độ `"normal"` nhanh và gắt hơn (gravity 1300, cột 230 px/s, gap
195–245, cooldown 300 ms). Muốn tinh chỉnh riêng, sửa trực tiếp
`EASY_CONFIG` / `NORMAL_CONFIG`.

## 6. Chế độ debug

`DEBUG_MODE = True` trong [config.py](config.py) (hoặc `--debug` /
`--no-debug`, hoặc phím `F1`). Overlay hiển thị hai nhóm:

- **Gameplay**: `Velocity Y`, `Gravity` (kèm nhãn `x0.5 grace` trong 1 s
  đầu), `Flap force`, `Flap detected: YES/no` (giữ YES ≥ 300 ms),
  `Cooldown: READY/...`, `Game state`.
- **Vision**: tọa độ Y đã làm mượt của hai cổ tay và hai vai, vận tốc
  tay, trạng thái state machine (`ARMS_DOWN / ARMS_UP / FLAP_CONFIRMED /
  NO_POSE`), cooldown, visibility, tổng số flap.

Ngoài ra mỗi lần flap console in
`FLAP detected | old_velocity=... | new_velocity=...` để xác nhận sự
kiện thật sự truyền vào `player.flap()`.

## 7. Xử lý sự cố

| Vấn đề | Cách xử lý |
|--------|------------|
| **Không mở được webcam** | Game vẫn chạy, hiện banner đỏ và tự cho phép chơi bằng SPACE. Kiểm tra app khác đang chiếm camera (Zoom, Teams...), thử `--camera 1` |
| **Webcam bị rút giữa chừng** | Game không đứng hình; vision thread tự thử kết nối lại mỗi 2 giây |
| **`pip install mediapipe` lỗi** | Kiểm tra Python 3.9–3.12 (64-bit). Python 3.13 chưa được MediaPipe hỗ trợ |
| **"KHÔNG NHẬN DIỆN ĐƯỢC" liên tục** | Thiếu sáng, đứng quá gần/xa, hoặc nền quá rối. Cần thấy rõ từ hông trở lên; visibility hiển thị trong debug |
| **Vỗ không ăn** | Hạ tay dứt khoát hơn (có ngưỡng vận tốc chống giữ-tay-trên-cao); chạy lại hiệu chỉnh `C`; giảm `min_down_speed_ratio` |
| **Nhận nhầm khi tay rung nhẹ** | Tăng `min_down_speed_ratio`, `up_margin_ratio` hoặc `stable_frames_required` |
| **FPS camera thấp (< 15)** | Giữ `POSE_MODEL_COMPLEXITY = 0` (lite — mặc định) và/hoặc giảm `CAMERA_WIDTH/HEIGHT = 480/360` trong config. `1`/`2` (full/heavy) chính xác hơn nhưng chậm hơn |
| **"Không tải được model pose"** | Máy không có mạng ở lần chạy đầu. Tải thủ công file `.task` (xem mục Cài đặt) vào `assets/models/` |
| **File high score hỏng** | Tự động bỏ qua và đếm lại từ 0 (`data/high_score.json`) |

## 8. Kiến trúc mã nguồn

```text
gameFUn/
├── main.py                  # Điểm khởi chạy + tham số dòng lệnh
├── config.py                # TOÀN BỘ hằng số & threshold
├── requirements.txt
├── game/
│   ├── game.py              # Game loop + state machine MENU/CALIBRATING/PLAYING/GAME_OVER
│   ├── player.py            # Vật lý chim, animation vỗ cánh, nghiêng theo vận tốc
│   ├── obstacle.py          # Sinh cột, tính điểm, va chạm tròn-vs-chữ nhật
│   ├── particles.py         # Hiệu ứng hạt (vỗ cánh, ghi điểm, va chạm)
│   ├── sound.py             # Âm thanh: ưu tiên assets/*.wav, fallback tổng hợp NumPy
│   └── ui.py                # Nền, HUD, khung webcam, menu, calibration, debug overlay
├── vision/
│   ├── camera.py            # cv2.VideoCapture an toàn, tự mở lại khi mất kết nối
│   ├── pose_tracker.py      # Wrapper MediaPipe Pose, trích 6 landmark thân trên
│   ├── flap_detector.py     # WingFlapDetector: state machine + EMA + ngưỡng vận tốc
│   ├── calibration.py       # Hiệu chỉnh ngưỡng theo từng người chơi
│   └── vision_system.py     # Thread webcam+pose, snapshot thread-safe cho game loop
├── tools/generate_assets.py # Sinh WAV placeholder (tùy chọn)
├── assets/                  # Âm thanh tùy chọn (flap/score/hit/gameover.wav)
└── data/high_score.json     # Kỷ lục
```

**Luồng dữ liệu:** vision thread đọc webcam → MediaPipe Pose →
`WingFlapDetector` (state machine `ARMS_DOWN → ARMS_UP → hạ nhanh →
FLAP_CONFIRMED`) → cộng dồn sự kiện vào counter có lock → game loop 60 FPS
gọi `consume_flaps()` mỗi frame → `player.flap()`. Nhờ đó pose detection
(~20–30 FPS) không bao giờ chặn game loop, và không sự kiện nào bị mất
kể cả khi FPS camera thấp.
"# wing-flap-bird" 
