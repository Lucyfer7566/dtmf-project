# DỰ ÁN: DTMF ENCODE/DECODE TRÊN DESKTOP (PYTHON) VÀ MOBILE (ANDROID, iOS)

## 1. Mục tiêu dự án

- Xây dựng hệ thống **mã hóa (encode)** và **giải mã (decode)** tín hiệu DTMF (Dual‑Tone Multi‑Frequency) trên:
  - Desktop App bằng Python.
  - Ứng dụng Mobile (Android, iOS).
- Vận dụng kiến thức môn **Xử lý tín hiệu số (DSP)** vào một bài toán thực tế trong viễn thông.

## 2. Tổng quan DTMF

- DTMF là kỹ thuật dùng **2 tần số sin đồng thời** để biểu diễn một phím bấm (0–9, \*, #, A–D).
- Tập tần số chuẩn ITU‑T Q.23:
  - Nhóm thấp (rows): 697 Hz, 770 Hz, 852 Hz, 941 Hz.
  - Nhóm cao (columns): 1209 Hz, 1336 Hz, 1477 Hz, 1633 Hz.
- Ví dụ: phím "5" = 770 Hz + 1336 Hz.

## 3. Chức năng chính của hệ thống

### 3.1 Encode (mã hóa DTMF)

- Nhập chuỗi số/ký tự (ví dụ: "123#").
- Chương trình sinh tín hiệu âm thanh bằng cách cộng hai sóng sin tương ứng với mỗi phím.
- Phát ra loa hoặc lưu thành file WAV.

### 3.2 Decode (giải mã DTMF)

- Thu tín hiệu âm thanh (microphone hoặc file âm thanh).
- Phân tích tần số để tìm 2 tần số thuộc nhóm thấp và nhóm cao.
- Tra bảng DTMF để suy ra phím tương ứng, ghép lại thành chuỗi.

## 4. Phần DSP cốt lõi

### 4.1 Sinh tín hiệu (encode)

- Dùng Python (numpy) tạo sóng sin tại các tần số DTMF.
- Sample rate dự kiến: 8 kHz (chuẩn thoại).

### 4.2 Giải mã (decode)

- Áp dụng **Goertzel algorithm** hoặc **FFT** để đo năng lượng tại 8 tần số DTMF.
- Chọn tần số mạnh nhất ở mỗi nhóm (thấp/cao), so sánh với ngưỡng, sau đó ánh xạ ra phím.

## 5. Thiết kế theo nền tảng

### 5.1 Desktop App (Python)

- Giao diện đơn giản (tkinter/PyQt).
- Chức năng:
  - Encode: nhập chuỗi → phát/ghi file âm DTMF.
  - Decode: đọc từ micro hoặc file WAV → hiển thị chuỗi nhận được.
- Thư viện: `numpy`, `scipy`, `pyaudio`/`sounddevice`.

### 5.2 Android

- Java/Kotlin + Android Studio.
- Dùng `AudioRecord` để ghi âm, `AudioTrack` hoặc `ToneGenerator` để phát.
- Thuật toán giải mã giống desktop, viết lại bằng Java/Kotlin.

### 5.3 iOS (tuỳ thời gian/khả năng)

- Swift + `AVAudioEngine` để ghi/phát âm.
- Xử lý tín hiệu (Goertzel/FFT) bằng Swift hoặc Accelerate framework.

## 6. Kết quả mong đợi

- Demo được encode/decode DTMF trên ít nhất Desktop (Python) + một nền tảng mobile (ưu tiên Android).
- Có báo cáo ngắn trình bày:
  - Nguyên lý DTMF và bảng tần số.
  - Mô tả thuật toán Goertzel/FFT dùng trong decode.
  - Thiết kế phần mềm và một số kết quả thử nghiệm.
