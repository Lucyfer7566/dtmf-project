"""
Test cho phần thuật toán tạo DTMF (Encoder).
"""
import unittest
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsp.encoder import generate_dtmf_tone
from dsp.constants import SAMPLE_RATE, TONE_DURATION, SILENCE_DURATION

class TestEncoder(unittest.TestCase):
    def test_encode_12hash(self):
        """Kiểm tra xem mảng sinh ra có đúng độ dài dự tính không với chuỗi '12#'."""
        digits = "12#"
        audio_signal = generate_dtmf_tone(digits)
        
        # Đảm bảo mảng sinh ra không rỗng và là numpy array
        self.assertIsNotNone(audio_signal)
        self.assertIsInstance(audio_signal, np.ndarray)
        self.assertGreater(len(audio_signal), 0)
        
        # Có 3 tones và 2 đoạn silence ngắn
        expected_duration = (3 * TONE_DURATION) + (2 * SILENCE_DURATION)
        expected_samples = int(expected_duration * SAMPLE_RATE)
        
        self.assertEqual(len(audio_signal), expected_samples, "Độ dài mảng numpy không tương ứng với tổng thời gian phát")
    
    def test_encode_undefined_character(self):
        """Kiểm tra xử lý ngoại lệ khi nhập ký tự không có trong chuẩn DTMF."""
        with self.assertRaises(ValueError):
            generate_dtmf_tone("X")

if __name__ == '__main__':
    unittest.main()
