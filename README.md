# DTMF Encode & Decode System (Goertzel Algorithm)

Dự án giáo dục mã nguồn mở mô phỏng và xử lý tín hiệu **Dual-Tone Multi-Frequency (DTMF)**. 
Điểm làm nên linh hồn của dự án này đó là **không sử dụng** các thư viện hộp đen (như FFT, JTransform có sẵn của Numpy Lib), mà tự xây dựng và thực thi trực tiếp thuật toán **Goertzel** bằng các phép toán nguyên thủy trên nền tảng: **Python (Desktop)** và bộ code port độc lập **Dart (Flutter Mobile)**.

Đây là một dự án tối ưu để sinh viên, lập trình viên thực hành, học hỏi phân tích tín hiệu số (DSP) và tìm hiểu cơ chế hoạt động của hạ tầng viễn thông/tổng đài.

---

## Chức Năng Chính

- **DTMF Encoder:** Sinh tín hiệu âm thanh chuẩn (Sine Wave) từ các phím bấm (0-9, A-D, *, #) bằng cách lấy tổng biên độ của 2 dải tần số đặc trưng (Row và Col). Hỗ trợ ngắt quãng Silence gap để tiếng kêu tách bạch.
- **DTMF Decoder:** Phân mảnh file âm thanh hoặc microphone stream thành dãy số thực, cắt các khối Frame 100ms thời gian thực, chạy vòng lặp chặn IIR qua thuật toán Goertzel để dò tìm năng lượng biên độ (Magnitude) rồi trích xuất ra phím được bấm một cách chuẩn xác không để nhiễu tạp âm (có chặn nhiễu Threshold ngặt).
- **Cross-Platform:** Có sẵn hệ thống cấu trúc Frontend hoàn chỉnh chạy trên phần cứng Native của **Windows/macOS (Tkinter GUI)** và **Android/iOS (Flutter App)** dùng chung một lý thuyết lõi (Core Logic).

---

## Tổ Chức Cây Thư Mục

Dự án được chia làm 3 phân vùng độc lập để dễ dàng tham chiếu chéo mã nguồn:

- `dsp/`: Lõi xử lý tín hiệu gốc bằng Python (Chứa bộ tính năng lượng `goertzel.py`, bảng dải tần `constants.py`).
- `desktop_app/`: Ứng dụng Desktop có hiển thị UI. Có vai trò gọi các hàm DSP, liên kết luồng thu/phát âm thanh bằng Microphone thực tế thông qua thư viện IO `sounddevice`.
- `mobile_app/`: Toàn bộ ứng dụng Di động Cross-platform bằng Dart (Flutter). Cấu trúc lõi DSP và thuật toán Goertzel được **tái thiết kế và nhúng 100% sang Dart độc lập**, giao tiếp cực nhanh trên RAM mà không cần gọi API Backend ngoài, hỗ trợ biên dịch ra iOS lẫn Android.
- `tests/`: Phân vùng Unit Test cho thiết kế Python chặn các lỗi sai logic toán học.

---

## Hướng Dẫn Cài Đặt Khởi Chạy - Python Desktop App 

### Yêu cầu hệ thống:
- Hệ điều hành Windows, macOS hoặc Linux.
- Có cài đặt Python 3.9 trở lên. Máy tính cấu hình Audio Microphone và Loa hoạt động bình thường.

### Cài đặt Môi trường:
Mở Terminal / PowerShell tại thư mục cấu trúc gốc của dự án. Khởi tạo môi trường ảo (khuyến nghị):
```bash
python -m venv venv

# Kích hoạt trên Windows:
.\venv\Scripts\activate
# Khởi động nếu đang ở macOS/Linux:
source venv/bin/activate
```

Cài đặt các thư viện lõi C++ (numpy, sounddevice, soundfile):
```bash
pip install -r requirements.txt
```

### Chạy Ứng dụng PC:
```bash
python -m desktop_app.gui_app
```
Giao diện Tkinter sẽ được gọi lên! Cho phép bạn bấm bàn phím thao tác "Encode" (phát ra loa) và Bấm nút "Record & Decode" (Hệ thống sẽ thu âm 5 giây từ Mic để giải mã lốc phím bạn vừa bấm).

---

## Hướng Dẫn Cài Đặt Khởi Chạy - Flutter Mobile App

### Yêu cầu hệ thống:
- Đã cài đặt [Flutter SDK](https://docs.flutter.dev/get-started/install) trên máy (Yêu cầu phiên bản Dart >= 3.0.0).
- Có mở máy ảo (Android Emulator/iOS Simulator) hoặc ưu tiên cắm cáp kết nối trực tiếp thiết bị điện thoại thật thông qua USB Debugging.

### Cài đặt & Build Code:
1. Mở môi trường Terminal và di chuyển vào thư mục Mobile:
```bash
cd mobile_app
```
2. Cập nhật và Download các package thư viện của Dart (như plugin `record` thu âm hay `just_audio` phát nhạc):
```bash
flutter pub get
```
3. Chạy lệnh cài và nạp ứng dụng lên màn hình điện thoại của bạn:
```bash
flutter run
```

** Đặc biệt Lưu ý:** Trong giao diện trên thiết bị Android/iOS, ở lần đầu tiên bấm Decode luồng âm thanh, ứng dụng OS sẽ yêu cầu quyền Truy Cập Micro. Bạn phải ấn **"Cho phép" (Allow Record Audio)** để thiết bị có Data mảng chạy vô DSP phân tích!

---

## Thông Tin Kỹ Thuật: Tại sao dùng Goertzel (DSP)
Thay vì sử dụng thuật toán Fast Fourier Transform (FFT) phải phân tích biểu diễn tần số cho **TOÀN BỘ CÁC TẦN SỐ** dư thừa (tiêu tốn chi phí lên tới $O(N \log N)$), chúng ta lựa chọn sử dụng nền tảng thuật toán **Goertzel** vì DTMF chỉ quan tâm tới đúng một lượng băng thông là **8 dải tần số cụ thể** mà ITU-T quy ước. 
Thuật toán Goertzel hoạt động xuất sắc như một cấu hình IIR (Infinite Impulse Response) một cực, quét qua các Block thời gian thực tế với chi phí tối ưu hóa vô cùng mượt mà, siêu việt trên các dòng vi điều khiển (MCU) nhúng hoặc các Mobile nhẹ RAM thụ lý.

*Ngoài ra, hệ thống đã trang bị sẵn **Threshold Tuning (Mức lọc nhiễu Threshold)** rất an toàn, có khả năng lọc bỏ phần thô của tiếng quạt gió hoặc tiếng ù nền.*

---

