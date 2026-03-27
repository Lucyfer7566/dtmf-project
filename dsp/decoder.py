"""
Sử dụng Goertzel algorithm để giải mã tín hiệu âm thanh về các ký tự DTMF.
"""

import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsp.constants import ROW_FREQS, COL_FREQS, DTMF_MAPPING, SAMPLE_RATE
from dsp.goertzel import detect_energies_for_freqs
from dsp.encoder import generate_dtmf_tone

def frame_signal(signal: np.ndarray, frame_duration: float, sample_rate: int) -> list[np.ndarray]:
    """
    Chia tín hiệu dài thành các frame (không overlap) dài frame_duration (giây).
    """
    frame_length = int(frame_duration * sample_rate)
    frames = []
    
    # Duyệt qua tín hiệu theo từng đoạn có độ dài frame_length (không overlap)
    for i in range(0, len(signal), frame_length):
        frame = signal[i:i + frame_length]
        # Chúng ta chỉ phân tích trên những frame có đủ độ dài lý tưởng (ít nhất bằng một nửa frame)
        if len(frame) >= frame_length // 2:
            frames.append(frame)
            
    return frames

def detect_digit_from_frame(frame: np.ndarray, sample_rate: int) -> str | None:
    """
    Dùng Goertzel để tính năng lượng tại 8 tần số DTMF.
    Chọn tần số mạnh nhất ở nhóm ROW và COL, map về ký tự.
    Trả về None nếu năng lượng quá nhỏ (coi như không có digit).
    """
    if len(frame) == 0:
        return None
        
    # Tính năng lượng cho tất cả 8 tần số của DTMF bằng thuật toán Goertzel
    all_freqs = ROW_FREQS + COL_FREQS
    energies = detect_energies_for_freqs(frame, sample_rate, all_freqs)
    
    # Lọc ra tần số hàng (ROW) và cột (COL) có mức năng lượng cực tiểu/lớn nhất
    max_row_freq = max(ROW_FREQS, key=lambda f: energies[f])
    max_row_energy = energies[max_row_freq]
    
    max_col_freq = max(COL_FREQS, key=lambda f: energies[f])
    max_col_energy = energies[max_col_freq]
    
    # Thiết lập hệ số ngưỡng cơ bản do năng lượng tín hiệu có thể rất nhỏ ở đoạn im lặng (silence gap)
    threshold = 50.0
    
    if max_row_energy > threshold and max_col_energy > threshold:
        # Nhận diện nếu năng lượng tần số vượt ngưỡng
        char = DTMF_MAPPING.get((max_row_freq, max_col_freq), None)
        return char
        
    return None

def detect_dtmf_tone(signal: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Chia tín hiệu thành các frame, gọi detect_digit_from_frame cho mỗi frame,
    ghép các digit lại thành chuỗi (loại bỏ None và trùng lặp liên tiếp).
    """
    if len(signal) == 0:
        return ""
        
    # Chọn độ dài phân mảnh khoảng 40ms (rất lý tưởng cho chuẩn DTMF tối thiểu 40ms)
    frame_duration = 0.04
    frames = frame_signal(signal, frame_duration, sample_rate)
    
    detected_chars = []
    last_char = None
    
    for frame in frames:
        char = detect_digit_from_frame(frame, sample_rate)
        
        if char is not None:
            # Loại bỏ các ký tự trùng lặp liên tiếp trong BẢN THÂN một âm, 
            # NHƯNG nếu có một khoảng lặng (None) cắt ngang thì nó sẽ là âm mới độc lập.
            if char != last_char:
                detected_chars.append(char)
        
        # Cập nhật lại trạng thái frame kề trước (kể cả nó là đoạn im lặng None)
        last_char = char
                
    return "".join(detected_chars)

if __name__ == "__main__":
    # Test thử việc gọi encode ra tín hiệu và dùng decoder bóc tách lại
    test_str = "0123ABCD*#"
    print("====================================")
    print(f"[*] Encoder: Đang tạo mã cho chuỗi: '{test_str}'...")
    audio_signal = generate_dtmf_tone(test_str)
    
    print(f"[*] Decoder: Đang đọc và giải mã tín hiệu {len(audio_signal)} mẫu (samples)...")
    decoded_str = detect_dtmf_tone(audio_signal)
    
    print("====================================")
    print(f"Chuỗi ban đầu   : {test_str}")
    print(f"Chuỗi giải mã   : {decoded_str}")
    
    if test_str == decoded_str:
        print("\n=> TEST SUCCESS: Kết quả encode/decode khớp nhau hoàn toàn!")
    else:
        print("\n=> TEST FAIL: Giải mã không khớp!")
