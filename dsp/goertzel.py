"""
Triển khai thuật toán Goertzel để phát hiện năng lượng của một tần số cụ thể.
Phù hợp để dạy sinh viên về xử lý tín hiệu không dùng FFT cho đơn tần.
"""

import math
import numpy as np

def goertzel(samples: np.ndarray, sample_rate: int, target_freq: float) -> float:
    """
    Tính năng lượng (magnitude squared) tại tần số target_freq trong đoạn tín hiệu samples
    bằng thuật toán Goertzel.
    """
    # N là tổng số lượng mẫu trong dải tín hiệu cần phân tích
    N = len(samples)
    if N == 0:
        return 0.0

    # Tính toán góc pha (w) cho tần số mục tiêu tính theo radian.
    # Sử dụng target_freq trực tiếp cho độ chính xác cao thay vì quy về k-bin (k = N * f / Fs)
    # Công thức: w = 2 * pi * F_target / F_sample
    w = 2.0 * math.pi * target_freq / sample_rate
    
    # Tính các hệ số trung gian của thuật toán Goertzel để tối ưu tính toán
    cosine = math.cos(w)
    coeff = 2.0 * cosine
    
    # Các biến trạng thái lưu lại 2 giá trị s(n-1) và s(n-2) trước đó (delay registers)
    s_prev = 0.0
    s_prev2 = 0.0
    
    # Vòng lặp vô hạn xung (IIR filter) qua từng mẫu tín hiệu (sample)
    for sample in samples:
        # s là trạng thái tín hiệu tại bước n hiện tại
        s = sample + (coeff * s_prev) - s_prev2
        
        # Cập nhật lại các trạng thái trễ cho vòng lặp bước (n+1) tiếp theo
        s_prev2 = s_prev
        s_prev = s
        
    # Tính năng lượng (magnitude bình phương) thu được tại tần số target_freq
    # Công thức năng lượng: power = s(N)^2 + s(N-1)^2 - coeff * s(N) * s(N-1)
    power = (s_prev ** 2) + (s_prev2 ** 2) - (coeff * s_prev * s_prev2)
    
    return power


def detect_energies_for_freqs(samples: np.ndarray, sample_rate: int, freqs: list[float]) -> dict[float, float]:
    """
    Trả về dict {freq: energy} cho mỗi tần số trong freqs.
    """
    energies = {}
    for freq in freqs:
        # Gọi thuật toán Goertzel cho từng tần số trong danh sách cần quét
        energies[freq] = goertzel(samples, sample_rate, freq)
        
    return energies
