"""
Chức năng Input/Output với thiết bị âm thanh thực tế: 
Phát (play), Ghi âm (record) từ micro dùng thư viện sounddevice.
Đọc/Ghi file WAV dùng thư viện soundfile.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import queue

def play_signal(signal: np.ndarray, sample_rate: int):
    """Phát mảng tín hiệu âm thanh ra loa mặc định của hệ thống."""
    sd.play(signal, samplerate=sample_rate)
    sd.wait()

def record_signal(duration: float, sample_rate: int) -> np.ndarray:
    """Ghi âm từ microphone mặc định chặn dòng code, chờ tới khi đủ frame mới làm việc."""
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    return recording.flatten()

def save_wav(filename: str, signal: np.ndarray, sample_rate: int):
    """Lưu mảng numpy chứa tín hiệu âm thanh thành dạng file WAV cổ điển."""
    sf.write(filename, signal, sample_rate)

def load_wav(filename: str) -> tuple[np.ndarray, int]:
    """Đọc file WAV chỉ định chuyển thành định dạng mảng numpy để xử lý."""
    signal, file_sample_rate = sf.read(filename)
    if len(signal.shape) > 1:
        signal = signal[:, 0]
    return signal, file_sample_rate

def start_live_record(sample_rate: int):
    """
    Bắt đầu thu âm bằng luồng bất đồng bộ (Non-blocking ASYNC mode).
    Sử dụng callback bắn trực tiếp Frame mẫu vào Hàng Đợi ảo để hệ thống không bị Lock Đơ màng hình.
    
    Returns:
        tuple[InputStream, queue.Queue]: Luồng sống chạy ẩn và Chân hàng đợi chứa Data Array.
    """
    q = queue.Queue()
    
    def audio_callback(indata, frames, time, status):
        # Đẩy dữ liệu vào hộp khi nhận được Audio Block (không chặn luồng Main)
        q.put(indata.copy())
        
    stream = sd.InputStream(samplerate=sample_rate, channels=1, callback=audio_callback)
    stream.start()
    return stream, q
