# HỆ THỐNG PHÂN TÍCH & GIẢI MÃ TÍN HIỆU ĐA TẦN (DTMF SIGNAL ANALYZER)

Dự án này là một bộ công cụ viễn thông chuyên nghiệp, hoạt động xuyên nền tảng (**Máy tính Python** và **Di động Flutter**) nhằm mục đích thu âm, theo dõi thời gian thực (Live Stream) và giải mã các tín hiệu **DTMF** (Dual-Tone Multi-Frequency) - âm thanh thường được tạo ra khi bấm phím trên điện thoại.

---

## KẾT CẤU & KIẾN TRÚC HỆ THỐNG (ARCHITECTURE)

Hệ thống được thiết kế độc lập mặt giao diện nhưng **dùng chung một tư duy và thuật toán Lõi (Core DSP)**.

### 1. Phân hệ Desktop (Python)

- **Giao diện:** Xây dựng bằng `Tkinter` hỗ trợ Multi-threading (chạy ngầm không đơ màn hình).
- **Âm thanh:** Dùng `sounddevice` (Luồng Queue siêu tốc) và `scipy/numpy` để lấy và đúc mẫu PCM.
- **Biểu đồ:** Dùng `Matplotlib` vẽ các lưới Radar (Piano Roll) dưới dạng dải màu Heatmap (Magma) với tỷ lệ Tọa độ 2 chiều (Thời gian vs Tần số).

### 2. Phân hệ Mobile (Flutter/Dart)

- **Giao diện:** Bộ công cụ Cross-platform Dart. Tính mượt mà (60FPS) được đảm bảo bằng cơ chế `SingleChildScrollView` cuốn trục đồ hoạ liên tục.
- **Âm thanh:** Giao thức luồng `Stream<Uint8List>` của Hardware Micro thông qua thư viện `record`.
- **Biểu đồ:** Từ chối các bảng vẽ nặng nề. Áp dụng `CustomPainter` trực tiếp lên Canvas di động để họa những khối vuông Đơn Sắc (Solid blocks: Xanh / Vàng) hệt như một chiếc đàn Piano Tiles chạy ngược thời gian theo phương ngang dựa vào Năng lượng thực.

---

## LOGIC TOÁN HỌC: THUẬT TOÁN GOERTZEL

Nếu dùng FFT (Fast Fourier Transform), máy tính sẽ phải phân tách **TOÀN BỘ** bức màn tần số từ 0 -> 4000Hz. Rất tốn Vi xử lý (RAM/CPU) mà lại dư thừa.

Thay vào đó, hệ thống này dùng Thuật toán **Goertzel** - một loại "kính lúp" toán học. Nó chỉ chọc thủng phổ âm thanh tại **đúng 8 điểm tần số mục tiêu** của tín hiệu điện thoại, cắt gọt hoàn toàn tiếng gió, chó sủa, giọng nói con người (Noise rejection).

### Bảng Ma Trận Tần Số Khóa (DTMF Matrix)

| Low \ High | 1209 Hz | 1336 Hz | 1477 Hz | 1633 Hz |
| :--------: | :-----: | :-----: | :-----: | :-----: |
| **697 Hz** |    1    |    2    |    3    |    A    |
| **770 Hz** |    4    |    5    |    6    |    B    |
| **852 Hz** |    7    |    8    |    9    |    C    |
| **941 Hz** |   \*    |    0    |    #    |    D    |

_Một phím hợp lệ CHỈ KHI Goertzel tìm thấy năng lượng bùng nổ đồng thời ở đúng 1 Hàng (Vàng) và 1 Cột (Xanh)._

### Cách tính Năng lượng (Goertzel Energy Formula)

1. Tính Hệ số K: $k = (N \times TargetFrequency) / SampleRate$
2. Tính hằng số W (Cosin): $\omega = (2 \times \pi \times k) / N$
3. Dùng vòng lặp IIR Filter quét qua chuỗi âm thanh dài $N$ mẫu để ra $Q_1$, $Q_2$.
4. **Năng lượng sóng (Magnitude Squared):** $Energy = Q_1^2 + Q_2^2 - (Q_1 \times Q_2 \times 2 \times \cos(\omega))$
   Khi $Energy$ này bứt phá vượt mặt Ngưỡng cài đặt, phím máy tính sẽ được khắc (Decode).

---

## LUỒNG HOẠT ĐỘNG (DATA FLOW)

Hệ thống Cáp Quang thời gian thực chạy trên mạch nguyên lý 4 bước luân hồi:

1. **[Thu Thập] - Bơm Dữ Liệu:**
   Ống Mic mở ra luồng chảy `Stream` ở Tần số `8000Hz`. Máy sẽ liên tục múc từng khối **PCM 16-Bit** chèn lên bộ đệm âm thanh RAM (`_audioBuffer`).
2. **[Cúp Khối] - Windowing:**
   Không bao giờ phân tích đơn lẻ lẻ tẻ mảng Byte, hệ thống chờ khi bộ đệm đạt mốc **100ms (Frame Size = 800 mẫu âm)**. Tức thì cắt xoẹt cục 800 mẫu đó mang đi nướng ở lò Goertzel.
3. **[Xét Nghiệm] - Decoding Threshold:**
   Hàm Goertzel ném ra 8 con số cường độ Năng lượng cho 8 dải (4 High, 4 Low). Hệ thống lùng sục ra Mức Đỉnh lớn nhất của mảng High và Low. Nếu Đỉnh này lớn hơn mốc Rác cài sẵn (Threshold = 100.0) ➔ Xác định Toạ độ ➔ Suy ra Phím (Ví dụ `Max_Low_0` ghép với `Max_High_2` = Số `3`).
4. **[Hiển Thị] - Auto-Gain Heatmap:**
   Dựa trên tỷ lệ cường độ đó, `CustomPainter` sẽ bôi ánh sáng (Đèn ON/OFF). Các khối 100ms được móc xích vào mảng `History`, dàn hàng ngang và bọc trong khung Scroll trượt. Máy sẽ gồng sức tự động cuộn màn hình sang tận cùng biên giới bên Phải, tạo cảm giác Tín hiệu trôi giật thời gian thực.

---

## CÁC HÀM XỬ LÝ QUAN TRỌNG NHẤT

### Trong Bản Desktop (Python):

- `dsp/decoder.py -> goertzel_mag()`: Khung xương toán học IIR Core, vòng lặp vi phân số Năng lượng sóng dội `energy`.
- `audio_io.py -> LiveAudioHandler`: Thread bắt Audio bất tử của Sounddevice, gõ cộc cộc ném Block âm thanh rớt vào Queue Thread an toàn (Thread-Safe).
- `gui_app.py -> _process_audio_queue()`: Hàm cập nhật Giao diện. Vắt mẫu từ Queue ra, giải mã ra phím Text, và Update màu mảng `extent` của Matplotlib để rạch dải sáng Vàng-Xanh (Piano Roll) lên khung giao diện tĩnh.

### Trong Bản Mobile (Flutter/Dart):

- `audio_input.dart -> startRecordStream()`: Ngắt giới hạn thời gian cố định. Đổi đầu ra thành Ống `Stream`. Trong này có màng lọc giải phẫu Data C cấp thấp (`ByteData`), xử lý ép kiểu Unsigned 8-Bit sang vạch sóng Signed 16-Bit cực mượt chống kẹt Alignment Memory của HĐH điện thoại.
- `main.dart -> _processLiveBuffer()`: Cục não điều phối của App. Ăn Mẫu `_audioBuffer` ở khối `800 frames / 100ms`, gọi hàm Decode và điều binh khiển tướng Cột năng lượng Ném vào mảng Cuộn Cuốn băng `_pianoRollHistory`.
- `dtmf_decoder.dart -> energiesForFreqs()`: Hàm băm Toán Học Goertzel bằng ngôn ngữ Dart.
- `piano_roll_painter.dart -> _paint()`: Hoạ sĩ Đồ Hoạ Thời gian Thực (`60FPS`). Tích hợp công nghệ lọc nhiễu **Dual Auto-Gain**. Lục tìm điểm sáng nhất ở 4 dải Low, đồng thời tìm điểm sáng nhất ở 4 dải High độc lập ➔ Trả lại khối Đồ hoạ Hình Chữ Nhật rực Rỡ 1 Màu Vuông Vắn (`AmberAccent` và `LightGreenAccent`) nếu Vượt Ngưỡng `20%`.
