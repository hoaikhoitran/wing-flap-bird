# Wing Flap Bird — Quyền riêng tư webcam / Webcam Privacy

*Phiên bản chính sách: 1 (v0.1.0-beta)*

## Tiếng Việt

Wing Flap Bird dùng webcam để nhận diện động tác vỗ tay. Cam kết:

1. **Mọi xử lý hình ảnh diễn ra cục bộ** trên máy của bạn (MediaPipe Pose
   chạy offline, model được đóng gói sẵn trong game).
2. **Không frame camera nào được tải lên server.** Game không có bất kỳ
   kết nối mạng nào trong lúc chơi.
3. Game **không ghi hình**, **không chụp ảnh**, **không lưu video**.
4. Game **không gửi tọa độ khung xương (landmark) ra Internet** — chúng chỉ
   tồn tại trong bộ nhớ trong lúc chơi rồi bị hủy.
5. Kết quả hiệu chỉnh (calibration) chỉ lưu **các ngưỡng số** (ví dụ
   `up_margin_ratio: 0.42`) vào `%LOCALAPPDATA%\WingFlapBird\calibration.json`
   — không chứa hình ảnh hay dữ liệu sinh trắc.
6. Internet chỉ có thể được dùng khi **bạn chủ động bấm**:
   - Nút mở trang ủng hộ nhà phát triển.
   - Nút mở trang GitHub của dự án.
   Game không bao giờ tự mở trình duyệt hay truy cập URL.
7. **Không telemetry, không analytics, không auto-update ngầm.**
8. Bạn có thể **chơi hoàn toàn không cần camera** bằng phím SPACE
   (hoặc chạy với `--no-camera`).
9. Bạn có thể **tắt khung webcam preview** trong Cài đặt.

## English

Wing Flap Bird uses your webcam to detect arm-flapping gestures:

1. **All image processing happens locally** on your device (MediaPipe Pose
   runs offline; the model ships inside the game).
2. **No camera frame is ever uploaded.** The game makes no network
   connections during gameplay.
3. The game **does not record video, take photos, or store footage**.
4. Pose landmarks are **never sent over the Internet** — they live in
   memory during play and are discarded.
5. Calibration stores **numeric thresholds only** (e.g.
   `up_margin_ratio: 0.42`) in `%LOCALAPPDATA%\WingFlapBird\calibration.json`
   — no images, no biometric data.
6. The Internet may only be used when **you explicitly click**: the donate
   button or the GitHub repository button. The game never opens a browser
   on its own.
7. **No telemetry, no analytics, no background update checks.**
8. You can **play entirely without a camera** using the SPACE key
   (or the `--no-camera` flag).
9. The webcam preview panel can be **turned off in Settings**.
