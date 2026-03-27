"""
Chịu trách nhiệm sinh tín hiệu âm thanh (mảng numpy) cho chuỗi các ký tự DTMF.
"""

import numpy as np
import soundfile as sf
import os
import sys

# Đưa thư mục gốc vào path để các file có thể sử dụng dưới dạng module con
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsp.constants import DTMF_MAPPING, SAMPLE_RATE, TONE_DURATION, SILENCE_DURATION, AMPLITUDE

# Đảo ngược mapping để tra cứu từ ký tự -> (row_freq, col_freq)
CHAR_TO_FREQ = {char: freqs for freqs, char in DTMF_MAPPING.items()}

def generate_single_tone(row_freq: float, col_freq: float, 
                         sample_rate: int, duration: float, amplitude: float) -> np.ndarray:
    """
    Sinh tín hiệu DTMF cho 1 phím: cộng sóng sin tại row_freq và col_freq.
    
    Args:
        row_freq: Tần số hàng (Hz)
        col_freq: Tần số cột (Hz)
        sample_rate: Tần số lấy mẫu (Hz)
        duration: Độ dài âm thanh (giây)
        amplitude: Biên độ tối đa (0.0 -> 1.0)
        
    Returns:
        Mảng numpy 1 chiều chứa mẫu âm thanh liền mạch.
    """
    # Tạo mảng thời gian t trục hoành tương ứng với các mẫu
    # Số lượng lấy mẫu = sample_rate * duration
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Sinh sóng sin cho tần số hàng và tần số cột
    # Công thức sóng sin: sin(2 * pi * f * t)
    row_wave = np.sin(2 * np.pi * row_freq * t)
    col_wave = np.sin(2 * np.pi * col_freq * t)
    
    # Tổng hợp 2 sóng và áp dụng biên độ (amplitude)
    # Chia cho 2.0 để bảo đảm không bị clip (vượt quá 1.0) khi hai sóng bằng 1 cùng lúc
    signal = (row_wave + col_wave) * (amplitude / 2.0)
    
    return signal

def generate_dtmf_tone(digits: str, 
                       sample_rate: int = SAMPLE_RATE, 
                       tone_duration: float = TONE_DURATION, 
                       silence_duration: float = SILENCE_DURATION, 
                       amplitude: float = AMPLITUDE) -> np.ndarray:
    """
    Sinh tín hiệu DTMF cho cả chuỗi digits, nối các tone lại với đoạn im lặng ngắn giữa chúng.
    """
    digits = digits.upper()
    audio_segments = []
    
    # Tạo mảng zero để biểu thị đoạn im lặng
    silence_samples = int(sample_rate * silence_duration)
    silence = np.zeros(silence_samples)
    
    for i, char in enumerate(digits):
        if char not in CHAR_TO_FREQ:
            raise ValueError(f"Ký tự không hợp lệ: '{char}'. DTMF chỉ hỗ trợ các số 0-9, chữ A-D và dấu *, #.")
            
        row_freq, col_freq = CHAR_TO_FREQ[char]
        tone = generate_single_tone(row_freq, col_freq, sample_rate, tone_duration, amplitude)
        
        audio_segments.append(tone)
        
        # Thêm khoảng gắt kết giữa các phím để người dùng/hệ thống phân biệt (không để ở cuối đoạn)
        if i < len(digits) - 1:
            audio_segments.append(silence)
            
    if not audio_segments:
        return np.array([])
        
    return np.concatenate(audio_segments)

if __name__ == "__main__":
    # Ví dụ nhỏ để sinh ra tín hiệu cho dãy "123#" và lưu dạng file sóng wav
    test_digits = "123#"
    print(f"Bắt đầu generate tín hiệu DTMF cho mã: '{test_digits}'...")
    
    try:
        audio_data = generate_dtmf_tone(test_digits)
        output_filename = "test_dtmf_123hash.wav"
        
        # Lưu file WAV, audio_data là float32 numpy array từ -1 đến 1 nên soundfile sẽ handle auto ghi chuẩn
        sf.write(output_filename, audio_data, SAMPLE_RATE)
        print(f"Đã lưu thành công audio test vào file: {output_filename}")
        
    except Exception as e:
        print(f"Lỗi khi quá trình sinh file: {e}")
