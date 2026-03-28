# TÀI LIỆU KỸ THUẬT: HỆ THỐNG PHÂN TÍCH & GIẢI MÃ TÍN HIỆU ĐA TẦN (DTMF)

## PHẦN 1: BẢN CHẤT CỦA TÍN HIỆU DTMF

DTMF (Dual-Tone Multi-Frequency) là tín hiệu tạo ra từ bàn phím điện thoại. Mỗi phím bấm KHÔNG PHẢI là một âm thanh đơn lẻ, mà là sự hòa trộn của CHÍNH XÁC 2 sóng hình sin (1 sóng tần số Thấp + 1 sóng tần số Cao).

- **Nhóm Thấp (Row Freqs):** `697 Hz`, `770 Hz`, `852 Hz`, `941 Hz`
- **Nhóm Cao (Col Freqs):** `1209 Hz`, `1336 Hz`, `1477 Hz`, `1633 Hz`

Ví dụ: Khi bấm phím `1`, hệ thống loa điện thoại sẽ phát ra tiếng có tần số trộn lẫn của sóng **697 Hz** và sóng **1209 Hz**. Mục tiêu khi thực hiện dự án là bắt micro lắng nghe, bóc tách tổ hợp này và in chữ `1` lên màn hình.

---

## PHẦN 2: LÕI THUẬT TOÁN TOÁN HỌC GOERTZEL

Nếu dùng FFT (Biến đổi Fourier Nhanh), máy phải quét qua 4000 mức tần số khác nhau. Để tránh lãng phí vi xử lý, dự án sử dụng **Cơ chế lọc IIR của Thuật toán Goertzel** - loại thuật toán chỉ dò đúng "điểm chọc" đã cài sẵn.

### Công Thức Khởi Đầu

Tại hàm `goertzel_mag` (Python) hoặc `energiesForFreqs` (Dart):

1. **Hệ số Bậc (k):** Xác định Vị trí rổ của phổ: `k = int(0.5 + (N * target_freq) / sample_rate)`
   - Với `N` là độ dài số mẫu (Ví dụ 800 mẫu âm thanh). `sample_rate` là 8000Hz.
2. **Góc Xoay (omega):** $\omega = \frac{2\pi \cdot k}{N}$
3. **Cos Coefficient:** $coeff = 2 \times \cos(\omega)$

### Vòng Lặp Phản Hồi Hình Vô Tận (IIR Filter)

Thuật toán trỏ hai biến bộ nhớ `Q1 = 0`, `Q2 = 0`. Với hàng trăm mẫu mảng `$x_n$` đi vào:

```python
for n in range(N):
    Q0 = coeff * Q1 - Q2 + x[n]
    Q2 = Q1
    Q1 = Q0
```

_Giai đoạn này là để tạo một dao động cộng hưởng (Resonance). Nếu sóng `x[n]` vô tình cùng tần số với $\omega$ của thuật toán, Q sẽ khuếch đại lên khổng lồ. Nếu khác tần số, dãy luân phiên cộng trừ sẽ tự triệt tiêu Q về 0._

### Tính Năng lượng Vô Hướng Thực (Magnitude Squared)

Sau khi vòng lặp nhai hết `N` mẫu:
$$ Energy = Q_1^2 + Q_2^2 - Q_1 \times Q_2 \times coeff $$
Sóng Năng Lượng này được áp vào điều kiện: Nếu `Energy > Threshold` thì đó chính là DTMF, không phải nhiễu.

---

## PHẦN 3: LUỒNG HOẠT ĐỘNG TRÊN DESKTOP APP (PYTHON)

_Các file tham gia: `dsp/decoder.py`, `desktop_app/audio_io.py`, `desktop_app/gui_app.py`_

**1. Khai Hỏa Microphone qua Queue (`audio_io.py`)**

```python
sounddevice.InputStream(samplerate=self.rate, channels=self.channels, callback=self._callback)
```

Thay vì chờ đợi, nó mở một giếng nước. Cứ mỗi đoạn lấy mẫu âm thanh rớt xuống giếng, `_callback` sẽ ném mốc `indata.copy()` vào một giỏ `self.queue`. Giỏ này được Thread-Safe bảo vệ tuyệt đối.

**2. Tiêu Hóa Dữ Liệu Ở Main GUI (`gui_app.py`)**
Cứ mỗi 50ms, hàm `root.after(50, self._process_audio_queue)` chạy lại.

- Nó cạy Mảng ra khỏi `self.audio_io.queue.get_nowait()`.
- Ném nguyên cục đó sang `decode_dtmf_signal(buffer)`.
- Nhận lại dãy Matrix cường độ để tấy rửa biểu đồ Matplotlib:

```python
self.energy_matrix[:, :-1] = self.energy_matrix[:, 1:] # Ép dồn tất cả cột sang trái
self.energy_matrix[:, -1] = energy_col # Bổ sung cột mới vào rìa phải
self.image_heat.set_data(self.energy_matrix) # Chớp thay đổi lên GUI.
```

---

## PHẦN 4: LUỒNG HOẠT ĐỘNG TRÊN MOBILE APP (FLUTTER/DART)

### 1. Phễu Lọc Thô Phần Cứng (`audio_input.dart`)

```dart
return rawStream.map((Uint8List data) {
  var byteData = ByteData.sublistView(data);
  List<int> pcm16Data = List.filled(byteData.lengthInBytes ~/ 2, 0);
  for (int i = 0; i < byteData.lengthInBytes - 1; i += 2) {
    pcm16Data[i ~/ 2] = byteData.getInt16(i, Endian.little);
  }
  return pcm16Data;
});
```

**Chuyện gì xảy ra?** Plugin Audio ghi luồng dạng `Uint8List` (Dạng Bit 0101 thô). Lõi hệ thống Dart cực kỳ khó tính và dễ bị Crash Alignment (Bộ nhớ cấp phát lệch). Hàm trên luồn lách qua lớp vỏ `ByteData`, bóc lẻ rứt từng cụm 2 Bytes Little-Endian cực nhỏ và lấp ráp chúng làm 1 Khối chuẩn (PCM_16-bits). Sự mượt mà của Cáp Mạng đều nhờ đây cả.

### 2. Vùng Kẹp Thời Gian Thực (`main.dart` -> `_processLiveBuffer()`)

Ống truyền trả về `List<int>`, Flutter sẽ tự chia (Normalize) qua $32768.0$ để biến nó thành dải `-1.0 -> 1.0` siêu nhẹ và dồn vào `_audioBuffer`.

_Khống chế dòng lũ:_

```dart
while (_audioBuffer.length >= _frameSize) { ... }
```

Nếu Ống Buffer dài hơn kích thước Khung `800 mẫu (100ms)`, máy sẽ dùng Lưỡi dao `.sublist(0, 800)` cắt phăng khối đầu tiên mang đi Dịch mã Goertzel. Lấy xong lại vứt cái mảng thừa để vòng `while` liên tục bào mỏng đi mảng khổng lồ đến khi sạch bách âm thanh thừa.

_Tìm Số và Xây Cột Đèn (`_pianoRollHistory.add`):_
Kết quả từ thuật toán ra 8 cường độ âm tương ứng 8 dải (VD: 697Hz = 3.0, 1633Hz = 450,000.0). Nó sẽ in ra số DTMF. Đồng thời đẩy toàn bộ 8 cường độ vào Mảng Cuốn `_pianoRollHistory`.

**Auto-Scroll:**
Nhờ có `_scrollController.jumpTo(maxScrollExtent)`. Hệ điều hành sẽ tự bắn con mắt của ống kính cuộn biểu đồ Piano Roll chọt trượt dài vô hạn về bên Gốc Phải tương đương với nhịp 60 FPS mà không gặp bất kỳ hiện trạng Tràn RAM màn hình nào.

### 3. Kiến Trúc Lõi Đồ Hoạ DSP (`piano_roll_painter.dart`)

**Thuật toán DUAL AUTO-GAIN: Xóa Khử Nhiễu Của Mobile**
Micro Điện thoại luôn bắt sóng High cực To và bắt phổ Low cực Bé (Vênh nhau 10-100 Lần năng lượng). Màn hình sẽ ko thể vẽ cùng điểm chói sáng 1.0 chung.

```dart
double maxLowEnergy = 500.0;
double maxHighEnergy = 500.0;
// Quét tìm Max độc lập...
```

Tìm Max của dải Low, và Max Của Dải High. Áp dụng Mức Max lên làm chóp Phân Mã:

```dart
double currentMaxE = (row < 4) ? maxLowEnergy : maxHighEnergy;
double intensity = energy / currentMaxE;
if (intensity < 0.20) continue;
// Đủ Ngưỡng 20% => Trả Xanh Sáng Tuyệt Đối (Row HIGH) Hoặc Vàng Tuyệt Đối (ROW LOW).
```

Nhờ Thuật toán tách Lõi Bù Trừ Kép này, Bất kể đưa tần số dtmf bé cỡ nào vào Micro, Mobile App luôn hiển thị Cột Vuông ON/OFF nguyên khối Vàng Đậm/Xanh Đậm (Solid Color) chuẩn xác theo tỷ lệ toán học, tạo thành một khung Ma trận DTMF.

---

## PHẦN 5: CÁCH ĐỌC BIỂU ĐỒ (VISUALIZATION GUIDE) VÀ VÍ DỤ THỰC TẾ

Hệ thống biểu diễn tín hiệu giải mã thông qua hai loại biểu đồ trực quan chính:

### 1. Biểu đồ Thời gian thực (Waveform) - _Chỉ hiển thị trên Desktop_

- Hiển thị biên độ âm thanh (Amplitude) thô thu được từ Micro.
- **Cách đọc:** Trục ngang là Thời gian, trục dọc là Biên độ dao động (từ `-1.0` đến `1.0`). Khi đo tín hiệu DTMF, đồ thị này sẽ hiển thị dưới dạng một dải cụm sóng liên tục, biên độ dày đặc và khá ổn định. Nếu hình dáng sóng nổ lởm chởm gai góc ngẫu nhiên thì đó có thể là âm thanh môi trường (tiếng nói, tiếng ồn).

### 2. Biểu đồ Mật độ Phổ (Piano Roll / Heatmap) - _Lõi Hiển Thị Của Cả 2 Thiết Bị_

Đây là "con mắt" của hệ thống dựa trên ma trận năng lượng Goertzel, cung cấp khả năng tự kiểm dịch (Manual validation) cho người dùng.

- **Trục dọc (Y):** 8 tần số chuẩn của bảng mã DTMF, chia làm 2 vùng kiểm soát:
  - **4 làn bên trên** là Nhóm Tần Số Cao `Col` (Tính bằng Hz): `1633`, `1477`, `1336`, `1209`.
  - **4 làn bên dưới** là Nhóm Tần Số Thấp `Row` (Tính bằng Hz): `941`, `852`, `770`, `697`.
- **Trục ngang (X):** Lưu lượng thời gian. Các lưới vuông sẽ tự động cuộn sang trái (mỗi ô vuông đại diện cho một mốc 100 mili-giây).
- **Mã Hóa Màu Sắc:**
  - Nếu bất kỳ Tần số **Cao** nào bắt được tín hiệu vượt mốc Threshold, nó sẽ khiến ô vuông tại làn đó hiện **Màu Xanh (Lime/LightGreen)**.
  - Nếu Tần số **Thấp** bắt được tín hiệu, nó khiến ô vuông hiện **Màu Vàng (Amber)**.

### PHÂN TÍCH VÍ DỤ THỰC TẾ

**Ví dụ 1: Khi hệ thống thu được Phím `5`**
Khi phát tiếng phím `5` vào thiết bị:

1. Tại rãnh Radar Piano Roll sẽ thấy **CHÍNH XÁC 2 ô vuông Đơn Sắc sáng lên cùng lúc** tại một cột thời gian thẳng đứng:
   - Một ô màu **Vàng** ở làn `770 Hz`.
   - Một ô màu **Xanh** ở làn `1336 Hz`.
2. Dao cắt thuật toán đối chiếu `770` (Hàng Số 2) và `1336` (Cột Số 2) vào bảng Ma trận DTMF Core. Giao điểm của chúng chính là Phím `5`.
3. Nhờ cơ sở khoa học trên hình ảnh, hệ thống hiển thị mã `5` ra màn hình.

**Ví dụ 2: Khi hệ thống thu được Phím `*`**

- Hình ảnh Piano Roll ghi nhận 1 ô **Vàng ở làn đáy `941 Hz`** và 1 ô **Xanh ở làn `1209 Hz`**.
- Chiếu theo giao điểm toạ độ toán học: Đây là nút `*`.

**Ví dụ 3: Lỗi Tín Hiệu (Chống Nhiễu Noise)**

- Nếu vô tình đưa một âm thanh tiếng ho vào điện thoại. Micro giật mạnh.
- Nếu nhìn trên Waveform, sóng vọt lên đỉnh `1.0`. Nhưng trên Piano Roll, chỉ có duy nhất **1 ô sáng lên ở dải Vàng**, hoặc bảng quang phổ **hiện màu loang lổ xen kẽ**.
- **Kết luận:** Âm thanh KHÔNG đủ một cặp điểm (1 Vàng + 1 Xanh). Thuật toán huỷ lệnh, báo cáo đây là Tạp Âm Rác và không in ký tự nào ra màn hình mã hoá.
