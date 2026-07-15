# 🐦 Wing Flap Bird

**Vỗ hai tay như chim trước webcam để bay!** Game né chướng ngại vật điều
khiển bằng chuyển động cơ thể, chạy hoàn toàn offline trên Windows.

> Lấy cảm hứng từ thể loại game né chướng ngại vật. Đây là trò chơi độc lập,
> không liên quan tới bất kỳ game thương mại nào.

## Preview

```text
┌─────────────────────────────────────────────┐
│   12                          ┌──────────┐  │
│            ██                 │ webcam + │  │
│    🐦      ██                 │ skeleton │  │
│            ██     ██          └──────────┘  │
│    ██             ██           TAY CAO      │
│    ██             ██          [████████░]   │
└─────────────────────────────────────────────┘
```

*(TODO: thay bằng screenshot/GIF thật trước khi công bố)*

## Download

1. Mở trang **[Releases](https://github.com/hoaikhoitran/wing-flap-bird/releases)**
2. Tải `WingFlapBird-v0.1.0-beta-Windows-x64.zip`
3. Giải nén
4. Mở `WingFlapBird.exe`

Không cần cài Python, không cần Internet, không cần terminal.

> ⚠️ **Windows SmartScreen**: vì bản beta chưa có chứng chỉ ký mã, Windows có
> thể hiển thị cảnh báo SmartScreen. Chọn *More info → Run anyway*. Chỉ tải
> game từ trang GitHub Releases chính thức của repository này.

## How to play

1. Đứng cách webcam **1.5–2.5 m**, camera thấy được vai, khuỷu tay, cổ tay.
2. Lần đầu chơi, game hiệu chỉnh nhanh ~5 giây (đứng giữa khung hình →
   giữ tay thấp → giơ tay cao). Kết quả được lưu cho những lần sau.
3. **Nâng hai tay qua vai rồi hạ xuống dứt khoát** = một lần vỗ cánh
   (bay lên ~100 px). Mỗi chu kỳ chỉ tính một lần vỗ.
4. Né các cột để ghi điểm. Menu **CÁCH CHƠI** trong game có minh họa
   và chế độ test cử chỉ trực tiếp.

## Privacy

Hình ảnh webcam được **xử lý cục bộ 100%** trên máy bạn. Game không ghi
hình, không lưu video, không gửi bất kỳ dữ liệu nào lên Internet, không
telemetry. Bạn có thể chơi không cần camera (phím SPACE) và tắt khung
webcam preview trong Cài đặt. Chi tiết: **[PRIVACY.md](PRIVACY.md)**.

## System requirements

- Windows 10/11 x64
- Webcam (tùy chọn — không có vẫn chơi được bằng bàn phím)
- CPU 4 nhân trở lên khuyến nghị (MediaPipe chạy bằng CPU)
- ~700 MB dung lượng trống

## Controls

| Phím / Động tác | Chức năng |
|---|---|
| **Vỗ hai tay** | Bay lên (điều khiển chính) |
| `SPACE` | Bay (dự phòng khi không có webcam / debug) |
| `ESC` | Tạm dừng / quay lại |
| `R` | Chơi lại (màn game over) |
| `M` | Về menu chính (màn game over) |
| `F1` | Bật/tắt debug overlay |
| Chuột / `↑↓` `Enter` | Điều hướng menu |

## Troubleshooting

| Vấn đề | Cách xử lý |
|---|---|
| Không mở được webcam | Kiểm tra app khác đang chiếm camera (Zoom, Teams); vào **Cài đặt → Camera → Quét lại** và chọn camera khác; game vẫn chơi được bằng SPACE |
| "KHÔNG NHẬN DIỆN ĐƯỢC" liên tục | Thiếu sáng, đứng quá gần/xa; làm theo gợi ý trên màn hiệu chỉnh |
| Vỗ không ăn | Hạ tay dứt khoát hơn; chạy lại hiệu chỉnh (CÁCH CHƠI → Chạy hiệu chỉnh); tăng **Độ nhạy** trong Cài đặt |
| Nhận nhầm khi tay rung nhẹ | Giảm **Độ nhạy** trong Cài đặt |
| Game chậm | Đóng app nặng khác; MediaPipe cần CPU; tắt webcam preview |
| Game crash | Xem log tại `%LOCALAPPDATA%\WingFlapBird\logs\wing_flap_bird.log` và tạo issue kèm file này |

## Build from source (developer)

Yêu cầu **Python 3.11 x64** (phiên bản MediaPipe hỗ trợ ổn định đã test;
chưa hỗ trợ Python 3.13).

```bash
git clone https://github.com/hoaikhoitran/wing-flap-bird.git
cd wing-flap-bird
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python main.py            # chạy game
pytest                    # chạy test
```

Tham số hữu ích: `--camera 1`, `--no-camera`, `--debug`, `--smoke`.

Build bản Windows:

```bash
scripts\build_windows.bat
# hoặc thủ công:
pyinstaller build\wing_flap_bird.spec --clean --noconfirm --workpath build_tmp --distpath dist
```

Kết quả: `dist/WingFlapBird/WingFlapBird.exe` và
`release/WingFlapBird-v0.1.0-beta-Windows-x64.zip`.

## Support development

Wing Flap Bird miễn phí. Nếu thích game, bạn có thể ủng hộ qua nút
**ỦNG HỘ NHÀ PHÁT TRIỂN** trong menu (khi developer đã cấu hình
`DONATE_URL` trong `core/links.py`). Việc ủng hộ hoàn toàn tự nguyện và
không mở khóa lợi thế trong game.

## Contributing

Issue và pull request đều được hoan nghênh. Trước khi gửi PR:

```bash
pytest        # toàn bộ test phải pass
```

Checklist test thủ công: [docs/TESTING_CHECKLIST.md](docs/TESTING_CHECKLIST.md).

## License

[MIT](LICENSE) © 2026 hoaikhoitran — xem thêm
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
