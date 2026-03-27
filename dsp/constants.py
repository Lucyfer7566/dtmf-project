"""
File constants.py chứa các cấu hình hệ thống DTMF sử dụng trong dự án:
- Định nghĩa các tần số chuẩn DTMF (Row group, Col group).
- Map các cụm tần số (row_freq, col_freq) tương ứng với các phím trên bàn phím (0-9, A-D, *, #).
- Các tham số quy định thời gian phát âm (Duration) và tần số lấy mẫu (Sample Rate) sử dụng trong toàn bộ hệ thống.
"""

# Tần số hàng (Row Frequencies) tính theo Hz
ROW_FREQS = [697, 770, 852, 941]

# Tần số cột (Col Frequencies) tính theo Hz
COL_FREQS = [1209, 1336, 1477, 1633]

# Bảng mapping từ (row_freq, col_freq) -> ký tự tương ứng
DTMF_MAPPING = {
    (697, 1209): '1', (697, 1336): '2', (697, 1477): '3', (697, 1633): 'A',
    (770, 1209): '4', (770, 1336): '5', (770, 1477): '6', (770, 1633): 'B',
    (852, 1209): '7', (852, 1336): '8', (852, 1477): '9', (852, 1633): 'C',
    (941, 1209): '*', (941, 1336): '0', (941, 1477): '#', (941, 1633): 'D',
}

# Các tham số cho Xử lý tín hiệu bằng số (DSP parameters)
SAMPLE_RATE = 8000            # Tần số lấy mẫu (samples/second)
TONE_DURATION = 0.4           # Thời gian phát tín hiệu DTMF (giây) (Đã làm chậm)
SILENCE_DURATION = 0.2        # Khoảng dừng giữa các phím (giây) (Đã làm chậm)
AMPLITUDE = 0.8               # Biên độ dao động tối đa của sóng (từ 0.0 đến 1.0)
