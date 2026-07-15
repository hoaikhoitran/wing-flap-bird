# Third-Party Notices — Wing Flap Bird

Wing Flap Bird được phát hành theo giấy phép MIT (xem `LICENSE`).
Bản phân phối Windows đóng gói các thành phần bên thứ ba sau. Toàn văn
mỗi giấy phép có tại trang chủ tương ứng của từng dự án.

| Thành phần | Giấy phép | Nguồn |
|---|---|---|
| Python 3.11 | Python Software Foundation License | https://www.python.org |
| pygame | GNU LGPL v2.1 | https://www.pygame.org |
| OpenCV (qua opencv-python) | Apache License 2.0 (wrapper: MIT) | https://opencv.org / https://github.com/opencv/opencv-python |
| MediaPipe | Apache License 2.0 | https://github.com/google-ai-edge/mediapipe |
| MediaPipe Pose Landmarker model (`pose_landmarker_lite.task`) | Apache License 2.0 | https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker |
| NumPy | BSD 3-Clause | https://numpy.org |
| platformdirs | MIT | https://github.com/tox-dev/platformdirs |
| PyInstaller | GPL v2 với Bootloader Exception* | https://pyinstaller.org |

\* PyInstaller chỉ là công cụ build. Bootloader nhúng trong `WingFlapBird.exe`
được cấp phép kèm ngoại lệ (Bootloader Exception) cho phép phân phối ứng dụng
đóng gói theo bất kỳ giấy phép nào; mã nguồn PyInstaller không có mặt trong
bản phân phối.

## Ghi chú

- pygame được liên kết động (dynamic linking) theo điều khoản LGPL v2.1;
  người dùng có thể thay thế thư viện pygame theo quyền của LGPL.
- Toàn bộ **đồ họa** trong game được vẽ bằng Pygame primitives, và toàn bộ
  **âm thanh** được tổng hợp bằng NumPy — không sử dụng asset của bên thứ ba,
  không sử dụng bất kỳ asset nào từ Flappy Bird hoặc game thương mại khác.
- Game hiển thị chữ bằng **font hệ thống** của Windows (Arial/Segoe UI/
  Tahoma) thông qua `pygame.font.SysFont` — không đóng gói font nào.
- "Wing Flap Bird" là trò chơi độc lập lấy cảm hứng từ thể loại game né
  chướng ngại vật; không liên quan tới, và không giả mạo, bất kỳ trò chơi
  thương mại nào.
- MediaPipe là nhãn hiệu của Google LLC; "Powered by MediaPipe" trong
  Credits chỉ nhằm ghi công công nghệ, không phải logo sản phẩm.
