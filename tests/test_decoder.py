"""
Test cho phần thuật toán giải mã DTMF (Decoder) và hàm tính Goertzel.
"""
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsp.encoder import generate_dtmf_tone
from dsp.decoder import detect_dtmf_tone

class TestDecoder(unittest.TestCase):
    def test_decode_single_digit(self):
        """Gửi mảng số lý tưởng của phím '5' đi giải mã lấy lại kết quả."""
        digits = "5"
        signal = generate_dtmf_tone(digits)
        decoded = detect_dtmf_tone(signal)
        self.assertEqual(decoded, digits, f"Decode lỗi. Kỳ vọng: {digits}, Nhận được: {decoded}")

    def test_decode_multiple_digits(self):
        """Giải mã chuỗi nhiều phím liền nhau có dấu đặc biệt (12#)."""
        digits = "12#"
        signal = generate_dtmf_tone(digits)
        decoded = detect_dtmf_tone(signal)
        self.assertEqual(decoded, digits, f"Decode lỗi. Kỳ vọng: {digits}, Nhận được: {decoded}")
        
    def test_decode_complex_sequence(self):
        """Giải mã chuỗi với phím 0 và dấu sao (09*)."""
        digits = "09*"
        signal = generate_dtmf_tone(digits)
        decoded = detect_dtmf_tone(signal)
        self.assertEqual(decoded, digits, f"Decode lỗi. Kỳ vọng: {digits}, Nhận được: {decoded}")

if __name__ == '__main__':
    unittest.main()
