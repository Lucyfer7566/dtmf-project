"""
Giao diện người dùng trên Python bằng Tkinter để demo sinh và giải mã DTMF.
Tách bạch hoàn toàn logic thuật toán: Chỉ làm nhiệm vụ hiển thị và tương tác người dùng,
gọi hàm module qua lại một cách trực quan.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import os
import sys

# Dẫn path để load module nội bộ
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsp.encoder import generate_dtmf_tone
from dsp.decoder import detect_dtmf_tone
from dsp.constants import SAMPLE_RATE
from desktop_app.audio_io import play_signal, record_signal, save_wav, load_wav

class DTMFApp:
    def __init__(self, root):
        """Khởi tạo UI cơ bản bằng tk."""
        self.root = root
        self.root.title("DTMF Encoder Decoder Simulator")
        self.root.geometry("480x380")
        
        # Tiêu đề
        lbl_title = tk.Label(root, text="Chương trình Mô phỏng DTMF", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)
        
        # =========================================
        # Vùng tiện ích 1: Encoder & Nhập liệu play
        # =========================================
        frame_encode = tk.LabelFrame(root, text="Phát và Tự lưu tín hiệu DTMF (Encoder)", padx=10, pady=10)
        frame_encode.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_encode, text="Ký tự phát:").grid(row=0, column=0, pady=5, sticky="e")
        self.entry_digits = tk.Entry(frame_encode, width=25, font=("Arial", 12))
        self.entry_digits.grid(row=0, column=1, padx=5, pady=5)
        
        # Nút "Encode, Lưu WAV & Play" liên kết với hàm on_encode_play
        self.btn_encode = tk.Button(frame_encode, text="Encode, Tự lưu định dạng .WAV & Phát", command=self.on_encode_play, bg="#4CAF50", fg="white")
        self.btn_encode.grid(row=1, column=0, columnspan=2, pady=10)
        
        # =========================================
        # Vùng tiện ích 2: Decoder & Micro/File
        # =========================================
        frame_decode = tk.LabelFrame(root, text="Giải mã tín hiệu nguồn vào (Decoder)", padx=10, pady=10)
        frame_decode.pack(fill="x", padx=20, pady=10)
        
        # Nút "Record & Decode" dùng mic trực tiếp
        self.btn_record = tk.Button(frame_decode, text="Record Micro (5s)", width=16, command=self.on_record_decode, bg="#2196F3", fg="white")
        self.btn_record.grid(row=0, column=0, padx=10, pady=10)
        
        # Nút "Import WAV & Decode" dùng để đọc file bypass micro
        self.btn_load_wav = tk.Button(frame_decode, text="Import file WAV", width=16, command=self.on_load_wav_decode, bg="#FF9800", fg="white")
        self.btn_load_wav.grid(row=0, column=1, padx=10, pady=10)
        
        # Label hiển thị output
        self.lbl_result = tk.Label(frame_decode, text="Kết quả: <chưa có dữ liệu>", font=("Arial", 12, "bold"), fg="#D32F2F")
        self.lbl_result.grid(row=1, column=0, columnspan=2, pady=5)
        
    def on_encode_play(self):
        """Lấy chuỗi, xuất mảng, tự lưu file .wav và truyền xuống loa máy tính. """
        digits = self.entry_digits.get().strip()
        if not digits:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập chuỗi ký tự DTMF cần phát (0-9, A-D, *, #).")
            return
            
        try:
            self.btn_encode.config(state="disabled")
            self.root.update()
            
            # 1. Gọi DSP encoder để tính toán lượng data của chuỗi
            audio_signal = generate_dtmf_tone(digits)
            
            # 2. Tự lưu file WAV ngay lập tức định dạng {chuỗi digits}.wav
            # Thay đổi các dấu ký tự đặc biệt để an toàn cho tên file windows
            safe_filename = digits.replace("*", "star").replace("#", "hash")
            output_wav = f"dtmf_tone_{safe_filename}.wav"
            save_wav(output_wav, audio_signal, SAMPLE_RATE)
            
            # 3. Truyền lượng array này cho desktop io
            play_signal(audio_signal, SAMPLE_RATE)
            
            messagebox.showinfo("Hoàn tất", f"Phát loa hoàn tất!\nĐã lưu tự động file âm thanh: {output_wav}")
            
        except ValueError as ve:
            messagebox.showerror("Ký tự sai", str(ve))
        except Exception as e:
            messagebox.showerror("Lỗi Hệ Thống", f"Không thể phát/ghi sóng: {e}")
        finally:
            self.btn_encode.config(state="normal")
        
    def on_record_decode(self):
        """Thu mic trong vài giây, gọi thuật toán DSP để giải mật và chiếu ra màn hình."""
        record_duration = 5.0
        
        try:
            self.btn_record.config(state="disabled", text="Đang tiếp nhận mic...")
            self.lbl_result.config(text="Kết quả: [Đang ghi âm trong 5s...]")
            self.root.update()
            
            # Bước 1: Ghi âm micro trong record_duration giây
            audio_signal = record_signal(record_duration, SAMPLE_RATE)
            
            self.lbl_result.config(text="Kết quả: [Đang quét Goertzel...]")
            self.root.update()
            
            # Bước 2: Quét Goertzel để phát hiện các phân lớp
            decoded_digits = detect_dtmf_tone(audio_signal, SAMPLE_RATE)
            self._hien_thi_ket_qua(decoded_digits)
                
        except Exception as e:
            messagebox.showerror("Exception lỗi:", f"Lỗi mic hoặc DSP: {e}")
            self.lbl_result.config(text="Kết quả: [Lỗi hệ thống]", fg="#D32F2F")
        finally:
            self.btn_record.config(state="normal", text="Record Micro (5s)")

    def on_load_wav_decode(self):
        """Mở cửa sổ chọn file, đọc file WAV và cho decode trực tiếp bỏ qua micro"""
        file_path = filedialog.askopenfilename(
            title="Chọn file tín hiệu DTMF (.wav)",
            filetypes=(("WAV Audio Files", "*.wav"), ("All Files", "*.*"))
        )
        
        if not file_path:
            return  # Người dùng hủy không chọn
            
        try:
            self.lbl_result.config(text=f"Kết quả: [Đọc file {os.path.basename(file_path)}...]")
            self.root.update()
            
            # Mở file wav bằng soundfile lấy mảng âm thanh cùng bộ Sample Rate
            audio_signal, sr = load_wav(file_path)
            
            self.lbl_result.config(text="Kết quả: [Đang quét Goertzel...]")
            self.root.update()
            
            # Decode nguyên mảng sóng
            decoded_digits = detect_dtmf_tone(audio_signal, sr)
            self._hien_thi_ket_qua(decoded_digits)
            
        except Exception as e:
            messagebox.showerror("Lỗi File", f"Định dạng lỗi hoặc file không tồn tại: {e}")
            self.lbl_result.config(text="Kết quả: [Failed to decode file]")

    def _hien_thi_ket_qua(self, decoded_digits):
        """Hàm helper để gán kết quả xuất ra Label"""
        if decoded_digits:
            self.lbl_result.config(text=f"Kết quả: {decoded_digits}", fg="#388E3C")
        else:
            self.lbl_result.config(text="Kết quả: [Không tìm thấy sóng DTMF]", fg="#757575")

def run():
    root = tk.Tk()
    app = DTMFApp(root)
    root.mainloop()

if __name__ == "__main__":
    run()
