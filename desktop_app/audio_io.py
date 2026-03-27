"""
Chức năng Input/Output với thiết bị âm thanh thực tế: 
Phát (play), Ghi âm (record) từ micro dùng thư viện sounddevice.
Đọc/Ghi file WAV dùng thư viện soundfile.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np

def play_signal(signal: np.ndarray, sample_rate: int):
    """Phát mảng tín hiệu âm thanh ra loa mặc định của hệ thống."""
    sd.play(signal, samplerate=sample_rate)
    sd.wait()

def record_signal(duration: float, sample_rate: int) -> np.ndarray:
    """Ghi âm từ microphone mặc định trong thời gian quy định."""
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    return recording.flatten()

def save_wav(filename: str, signal: np.ndarray, sample_rate: int):
    """
    Lưu mảng numpy chứa tín hiệu âm thanh thành dạng file WAV cổ điển.
    
    Args:
        filename (str): Tên file muốn định danh
        signal (np.ndarray): Mảng âm thanh (khoảng -1.0 tới 1.0)
        sample_rate (int): Số mẫu trên 1 giây.
    """
    # soundfile.write tự động nhận biết dtype float và map về hệ nhị phân 16-bit PCM khi lưu
    sf.write(filename, signal, sample_rate)

def load_wav(filename: str) -> tuple[np.ndarray, int]:
    """
    Đọc file WAV chỉ định chuyển thành định dạng mảng numpy để xử lý.
    
    Returns:
        tuple[np.ndarray, int]: Trả về Mảng tín hiệu và Tân số mẫu thực thụ của file đó.
    """
    signal, file_sample_rate = sf.read(filename)
    
    # Kênh đầu ra có thể là Stereo, ta chọn lấy 1 kênh index=[0] để thành Mono
    if len(signal.shape) > 1:
        signal = signal[:, 0]
        
    return signal, file_sample_rate
