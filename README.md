# DTMF Analyzer System

Dự án này là hệ thống phần mềm sử dụng micro để lắng nghe và chuyển đổi chuỗi âm thanh **DTMF** (Dual-Tone Multi-Frequency) thành văn bản chuẩn thời gian thực.

Dự án hỗ trợ 2 nền tảng ứng dụng:
- **Desktop App (Hệ điều hành Windows/Mac/Linux):** Giao diện Python Tkinter.
- **Mobile App (Hệ điều hành iOS/Android):** Ứng dụng điện thoại bằng Flutter.

*(Nếu có thắc mắc gì về cách hệ thống lõi hoạt động, vui lòng đọc [Tài Liệu Kỹ Thuật ở đây](docs/TECHNICAL_DOCUMENTATION.md)).*

---

## 💻 1. HƯỚNG DẪN CÀI ĐẶT BẢN MÁY TÍNH (PYTHON DESKTOP)

Phiên bản Desktop được thiết kế với giao diện Bảng Điều Khiển với các lưới phổ Waveform và Heatmap phân tích chi tiết mọi tầng rung động.

### a. Yêu Cầu Cấu Hình
- Cài đặt Python `3.9` hoặc cao hơn.
- Yêu cầu cấp quyền Sử Dụng Microphone trong mục cài đặt bảo mật của Windows/Mac.

### b. Các Bước Cài Đặt (Terminal/Command Prompt)
1. Cài đặt toàn bộ các thư viện phụ thuộc của dự án thông qua file `requirements.txt`:
```bash
pip install -r requirements.txt
```
*(Lưu ý: Nếu sử dụng Linux (Ubuntu/Debian), hãy đảm bảo đã cài thư viện cội nguồn âm thanh `portaudio` bằng lệnh `sudo apt-get install portaudio19-dev` trước khi chạy pip install).*

2. Kích hoạt giao diện người dùng:
Khởi chạy bảng hệ thống bằng dòng lệnh:
```bash
python -m desktop_app.gui_app
```

### c. Hướng Dẫn Sử Dụng Tính Năng
- Cắm tai nghe hoặc Microphone vào máy.
- Bấm **"Start Live Stream"**. Mọi âm thanh lọt vào micro sẽ được hiển thị trên sóng liên tục. Đưa tiếng Beep lại gần micro, ma trận lưới Piano Roll sẽ rạch sóng liên tục và màn hình chính sẽ hiện ra những dãy Số DTMF được giải mã hoàn chỉnh.
- *Để tiết kiệm RAM máy tính, bấm Stop sau khi sử dụng xong.*

---

## 2. HƯỚNG DẪN CÀI ĐẶT BẢN DI ĐỘNG (FLUTTER APP) 

### a. Yêu Cầu Cấu Hình
- Môi trường lập trình **Flutter SDK** (`3.10.x` trở lên).
- Thiết bị thật cắm cáp hoặc Máy ảo Simulator có Micro.

### b. Các Bước Cài Đặt
1. Vào mục thư mục **mobile_app** và Cập nhật Thư Viện phụ thuộc (`pubspec.yaml`):
```bash
cd mobile_app
flutter pub get
```

2. Yêu cầu Cấp Quyền Build (Bắt Buộc cho IOS):
Nếu sử dụng iPhone/Mac, cần phải sửa file `ios/Runner/Info.plist` và thêm dòng:
```xml
<key>NSMicrophoneUsageDescription</key>
<string>App DTMF cần quyền Mic để lấy luồng tín hiệu số.</string>
```
*(Với Android, plugin record đã tự động điền sẵn permission)*

3. Khởi Chạy Ứng Dụng:
```bash
flutter run
```

### c. Hướng Dẫn Sử Dụng Trực Quan
- Mở App DTMF trên điện thoại lên.
- Bấm Nút **"BẮT ĐẦU RECORD LIVESTREAM"**. Trình quét Radar sẽ khởi động.
- Bật nguồn âm thanh tín hiệu DTMF và để gần điện thoại để thu âm.
- Biểu đồ **"Piano Roll"** sẽ hiển thị liên tục:
  - Cột **Vàng** = Nhóm Tần Số Thấp (Row: 697-941Hz)
  - Cột **Xanh** = Nhóm Tần Số Cao (Col: 1209-1633Hz)
- Vuốt ngón tay sang trái phải ở phần Đồ th nếu muốn xem lại Tín hiệu cũ mà chưa kịp đọc.

---