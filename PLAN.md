# Kế Hoạch Triển Khai (PLAN)

Dự án sẽ được triển khai theo các bước cụ thể như sau:

1. **Core DSP (Hệ thống Xử lý tín hiệu cốt lõi):**
   - Viết bảng cấu hình tần số `constants.py`.
   - Viết bộ tính toán năng lượng `goertzel.py`.
   - Hiện thực Encoder sinh sóng kép (`encoder.py`).
   - Hiện thực Decoder chia khối tín hiệu và kết hợp Goertzel để phát hiện ký tự (`decoder.py`).

2. **Kiểm thử tự động (Unit Test):**
   - Viết các test case trong `test_encoder.py` và `test_decoder.py` kiểm định độ chính xác lý tưởng của toán học mà không cần GUI. Chạy test và chỉnh sửa DSP logic nếu hỏng.

3. **Desktop Interface (GUI & Audio I/O):**
   - Liên kết chức năng lấy mẫu từ âm thanh thật vào mảng (`desktop_app/audio_io.py`).
   - Xây dựng giao diện mô phòng bàn phím và bảng kết quả giải mã bằng Tkinter (`desktop_app/gui_app.py`).

4. **Mobile Application (Flutter):**
   - Phần mobile sẽ được triển khai lại bằng Flutter trong thư mục `mobile_app/` để hỗ trợ cả Android và iOS từ cùng một codebase.
