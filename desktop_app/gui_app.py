"""
Giao diện người dùng trên Python bằng Tkinter để demo sinh và giải mã DTMF.
Tách bạch hoàn toàn logic thuật toán: Chỉ làm nhiệm vụ hiển thị, tương tác 
và có phân tích đồ thị vẽ sóng (Waveform & Spectrum Live).
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import os
import sys
import numpy as np
import queue

# Import Matplotlib dùng Backend TkAgg tương thích mọi nền tảng
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Dẫn path để load module nội bộ
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dsp.encoder import generate_dtmf_tone
from dsp.decoder import detect_dtmf_tone
from dsp.constants import SAMPLE_RATE, ROW_FREQS, COL_FREQS, DTMF_MAPPING
from dsp.goertzel import detect_energies_for_freqs
from desktop_app.audio_io import play_signal, save_wav, load_wav, start_live_record

class DTMFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DTMF Encoder/Decoder Simulator & Analyzer")
        self.root.geometry("1100x750")
        
        # Cờ Trạng thái Thu Âm "Bất Đồng Bộ"
        self.is_recording = False
        self.recording_stream = None
        self.recording_q = None
        self.recording_buffer = []

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        control_frame = tk.Frame(root)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)

        # ---- ENCODER BOX ----
        frame_encode = tk.LabelFrame(control_frame, text="Vùng 1: Thuật toán Encoder (Sinh Sóng)", padx=10, pady=10)
        frame_encode.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        tk.Label(frame_encode, text="Ký tự DTMF (0-9,*,#,A-D):").pack(pady=2)
        vcmd = (root.register(self.validate_dtmf_input), '%P')
        self.entry_digits = tk.Entry(frame_encode, width=20, font=("Arial", 14), justify="center", validate="key", validatecommand=vcmd)
        self.entry_digits.insert(0, "A89")
        self.entry_digits.pack(pady=5)
        
        self.btn_encode = tk.Button(frame_encode, text="Mạo danh Âm (Encode) & Phát Loa", command=self.on_encode_play, bg="#4CAF50", fg="white", height=2)
        self.btn_encode.pack(fill="x", pady=2)

        # ---- DECODER BOX ----
        frame_decode = tk.LabelFrame(control_frame, text="Vùng 2: Thuật toán Decoder (Giải Mã Goertzel)", padx=10, pady=10)
        frame_decode.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        btn_box = tk.Frame(frame_decode)
        btn_box.pack(fill="x", pady=5)
        btn_box.columnconfigure(0, weight=1)
        btn_box.columnconfigure(1, weight=1)

        self.btn_record = tk.Button(btn_box, text="Bắt Đầu Thu Âm", command=self.toggle_record, bg="#F44336", fg="white", height=2)
        self.btn_record.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.btn_load_wav = tk.Button(btn_box, text="Import WAV", command=self.on_load_wav_decode, bg="#FF9800", fg="white", height=2)
        self.btn_load_wav.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.lbl_result = tk.Label(frame_decode, text="KẾT QUẢ > Đang rảnh...", font=("Arial", 13, "bold"), fg="#D32F2F")
        self.lbl_result.pack(fill="both", expand=True, pady=(10, 0))

        # ---- MATRIX BOX (BẢNG TRA CỨU NHANH) ----
        frame_matrix = tk.LabelFrame(control_frame, text="Vùng 3: Ma Trận Bàn Phím (Tra Cứu/Reference)", padx=10, pady=10)
        frame_matrix.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # Góc Tọa độ rỗng
        tk.Label(frame_matrix, text="", font=("Arial", 9, "bold"), fg="gray").grid(row=0, column=0, padx=2)
        
        # Rải Header Cột (Màu Lục)
        for c, cf in enumerate(COL_FREQS):
            tk.Label(frame_matrix, text=f"{int(cf)}", fg="#4CAF50", font=("Arial", 10, "bold")).grid(row=0, column=c+1, padx=6)
            
        # Rải Hàng Dọc (Màu Vàng) và Nút Chữ
        for r, rf in enumerate(ROW_FREQS):
            tk.Label(frame_matrix, text=f"{int(rf)}", fg="#D4AF37", font=("Arial", 10, "bold")).grid(row=r+1, column=0, pady=4)
            for c, cf in enumerate(COL_FREQS):
                char = DTMF_MAPPING.get((rf, cf), "")
                tk.Label(frame_matrix, text=char, font=("Arial", 12, "bold"), bg="#E0E0E0", relief="groove", width=3).grid(row=r+1, column=c+1, padx=2, pady=2)

        # ---- PLOT FRAME ----
        plot_frame = tk.LabelFrame(root, text="Phân Tích Thông Kê Tín Hiệu (Live Analytics)", padx=10, pady=10)
        plot_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.fig = Figure(figsize=(7, 4), dpi=100)
        self.ax_time = self.fig.add_subplot(211)
        self.ax_freq = self.fig.add_subplot(212)
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self._plot_audio_signal(np.zeros(100), "Trạng thái nghỉ (Idle)")

    def _plot_audio_signal(self, audio_signal, title="Phân tích tín hiệu", live_mode=False):
        self.ax_time.clear()
        
        if not live_mode:
            self.ax_freq.clear()

        # TIME DOMAIN - Lấy max đoạn kết
        if live_mode:
            # LIVE MODE: Xem hẳn 1 Giây gần nhất (1.0s) để thấy từng luồng hơi thở lên xuống
            n_samples = min(len(audio_signal), int(SAMPLE_RATE * 1.0))
            if n_samples > 0:
                plot_time_domain = audio_signal[-n_samples:]
                time_axis = np.linspace(0, len(plot_time_domain) / SAMPLE_RATE, len(plot_time_domain), endpoint=False) 
                self.ax_time.plot(time_axis, plot_time_domain, color="blue", linewidth=1.0)
            
            self.ax_time.set_title(f"{title} - [Live Stream] Trục thời gian 1s gần nhất")
            self.ax_time.set_ylim(-0.3, 0.3) # Biên độ nhỏ giúp Mic phóng to độ nảy cực nhạy!
            self.ax_time.set_xlabel("Thời gian (Giây)")
        else:
            # POST-DECODE: Vẽ cấu trúc của TOÀN BỘ độ dài file âm thanh vừa ghi.
            # Rút mẫu (Downsample) bước nhảy nếu mảng quá lớn để chống kẹt CPU.
            step = max(1, len(audio_signal) // 8000)
            plot_time_domain = audio_signal[::step]
            
            time_axis = np.linspace(0, len(audio_signal) / SAMPLE_RATE, len(plot_time_domain), endpoint=False) 
            self.ax_time.plot(time_axis, plot_time_domain, color="blue", linewidth=1.0)
            
            self.ax_time.set_title(f"{title} - [Waveform] Biên độ Mảng Tổng Thể")
            self.ax_time.set_xlabel("Thời gian Tổng (Giây)")
            
        self.ax_time.set_ylabel("Amplitude")
        self.ax_time.grid(True, linestyle=":", alpha=0.6)

        # PIANO ROLL DOMAIN (DOMAIN 2) - Lưới Nhiệt 8 Làn Quét Chuỗi Thời Gian
        if not live_mode:
            all_freqs = ROW_FREQS + COL_FREQS
            frame_len = int(SAMPLE_RATE * 0.04) # Chia mẫu 40ms trượt chuẩn quốc tế DTMF
            
            # Khởi tạo ma trận tích lũy năng lượng cho toàn bộ rải rác
            energy_grid = []
            
            # Quét vòng lặp Thời gian: Phân mảnh tín hiệu gốc băm nát thành hàng trăm Frame 40ms!
            for i in range(0, len(audio_signal) - frame_len, frame_len):
                frame = audio_signal[i:i + frame_len]
                
                # Thuật toán Lấy Giữ Tạp Âm Cứng Đờ: Nếu mic im phăng phắc, gán = 0 để làm Đen màn hình.
                if np.max(np.abs(frame)) < 0.01:
                    energies = {f: 0.0 for f in all_freqs}
                else:
                    energies = detect_energies_for_freqs(frame, SAMPLE_RATE, all_freqs)
                
                # Ghép nguyên 8 chỉ số của Frame này vào Cột Tích Lũy
                energy_grid.append([energies[f] for f in all_freqs])
                
            if len(energy_grid) == 0:
                energy_grid = [[0.0]*8]
                
            # Đã thu thập xong. Chuyển vị thành hệ [8 Hàng Tần Số] x [N Cột Thời Gian]
            energy_matrix = np.array(energy_grid).T
            
            # Giảm tỷ lệ độ chói cực đại bằng Log/Căn cho các Cục Lửa rõ nét
            energy_matrix = np.sqrt(energy_matrix)

            # Phun lửa lên lưới "Gạch Lót Sàn" imshow
            self.ax_freq.imshow(energy_matrix, aspect='auto', origin='lower',
                                extent=[0, len(audio_signal)/SAMPLE_RATE, -0.5, 7.5],
                                cmap='magma', interpolation='nearest', zorder=1)
            
            # Cắt Lót nhãn cho 8 Làn Tần Số Trục Y
            self.ax_freq.set_yticks(range(8))
            self.ax_freq.set_yticklabels([f"{int(f)} Hz" for f in all_freqs], fontweight='bold')
            
            # Kẻ Grid ngang mờ đứt nét bằng Trắng để phân luồng dễ gióng mắt (zorder=2 cho ngập chìm)
            for i in range(8):
                self.ax_freq.axhline(i, color='white', linewidth=0.5, alpha=0.3, zorder=2)
                
            # Sơn dải viền mờ ảo làm vệt sáng chỉ đường cho 2 dải màu phân cực Vàng - Xanh
            self.ax_freq.axhspan(-0.5, 3.5, color='yellow', alpha=0.15, zorder=3)
            self.ax_freq.axhspan(3.5, 7.5, color='green', alpha=0.15, zorder=3)
            
            # Vẽ đường Line phân cách cực đại ở giữa ranh giới (giữa Row và Col)
            self.ax_freq.axhline(3.5, color='white', linewidth=1.5, linestyle="--", alpha=0.7, zorder=4)
            
            # Thẩm mỹ Màu Trục (Vàng chóe cho 4 dòng dưới, Lục lam cho 4 dòng trên)
            for i, label in enumerate(self.ax_freq.get_yticklabels()):
                if i < 4:
                    label.set_color("#FFC107") # Vàng (Low Freqs)
                else:
                    label.set_color("#4CAF50") # Xanh (High Freqs)
            
            # Trình bày UI Đồ hoạ
            self.ax_freq.set_title("[Piano Roll Tĩnh] Toàn Cảnh 8 Làn Quét Thời Gian (Từng Mốc 40ms)")
            self.ax_freq.set_xlabel("Quá Trình Mốc Lịch Sử (Time / Giây)")
            self.ax_freq.set_ylabel("Cấu Trúc Tầng DTMF Lõi")

        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()

    def validate_dtmf_input(self, new_value):
        import re
        if new_value == "": 
            return True
        # Chỉ cho phép gõ các ký tự hợp lệ Phím DTMF (không phân biệt Hoa/Thường)
        return bool(re.match(r'^[0-9a-dA-D*#]+$', new_value))

    def on_encode_play(self):
        digits = self.entry_digits.get().strip()
        if not digits:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập chuỗi ký tự DTMF cần phát (0-9, A-D, *, #).")
            return
            
        try:
            self.btn_encode.config(state="disabled")
            self.root.update()
            
            audio_signal = generate_dtmf_tone(digits)
            self._plot_audio_signal(audio_signal, f"Encode Mẫu: [{digits}]")
            
            safe_filename = digits.replace("*", "star").replace("#", "hash")
            output_wav = f"dtmf_tone_{safe_filename}.wav"
            save_wav(output_wav, audio_signal, SAMPLE_RATE)
            
            play_signal(audio_signal, SAMPLE_RATE)
            self.lbl_result.config(text=f"KẾT QUẢ > Đã chèn sóng gốc {digits}", fg="#388E3C")
            messagebox.showinfo("Export Thành Công", f"Âm thanh chuẩn Goertzel đã được kết xuất và nhúng lưu tại file:\n[{output_wav}]")
            
        except ValueError as ve:
            messagebox.showerror("Ký tự sai", str(ve))
        finally:
            self.btn_encode.config(state="normal")
        
    def toggle_record(self):
        """Bật/Sập luồng ghi âm. Nếu đang thu thì Dừng -> Xích Data đem đi Phân Tích Decode."""
        if not self.is_recording:
            # 1. Mở Khoá Cơ Chế Bắt Đầu Ghi Âm Vô Hạn
            self.is_recording = True
            self.btn_record.config(text="Dừng & Giải Mã Audio", bg="#607D8B")
            self.btn_load_wav.config(state="disabled")
            self.btn_encode.config(state="disabled")
            self.lbl_result.config(text="KẾT QUẢ > Đang THU ÂM (Sóng vút nhảy múa...)", fg="#D32F2F")
            
            self.recording_buffer = []
            
            try:
                # Bypass Luồng Mic Bất Đồng Bộ
                self.recording_stream, self.recording_q = start_live_record(SAMPLE_RATE)
                
                # Bắn mũi tên Loop quét Hàng Đợi ảo sau mỗi 10 khung hình/s
                self.root.after(100, self.update_live_record)
            except Exception as e:
                messagebox.showerror("Microphone Không Bắt Được", str(e))
                self.reset_record_ui()
                
        else:
            # RÚT LẠI CỜ FLAG VÀ THOÁT LUỒNG LOOP LIVE THU
            self.is_recording = False
            
    def update_live_record(self):
        """Vòng lặp bơm nước từ Hàng Đợi Chờ ra cập nhật đồ thị Mắt."""
        if self.is_recording:
            # Dọn cạn máng Queue
            while True:
                try:
                    chunk = self.recording_q.get_nowait()
                    self.recording_buffer.extend(chunk.flatten())
                except queue.Empty:
                    break
                    
            # Update Live Stream Sóng âm thời gian thực nếu ống Buffer kịp có nước
            if len(self.recording_buffer) > 0:
                audio_array = np.array(self.recording_buffer)
                self._plot_audio_signal(audio_array, "Đang Bắt Sóng Live...", live_mode=True)
                
            # Duy trì ngọn lửa vòng lặp tiếp diễn
            self.root.after(100, self.update_live_record)
        else:
            # ==============================
            # KỊCH BẢN CHỐT: HẬU KỲ DECODE khi kết thúc nút Bấm (is_recording = False)
            # ==============================
            self.recording_stream.stop()
            self.recording_stream.close()
            
            audio_signal = np.array(self.recording_buffer)
            self.reset_record_ui()
            
            if len(audio_signal) == 0:
                self.lbl_result.config(text="KẾT QUẢ > Trống (File 0s)", fg="#757575")
                return
                
            self.lbl_result.config(text="KẾT QUẢ > Đang đo Goertzel Quãng Cuối...", fg="#FF9800")
            self.root.update()
            
            # Khởi động lại Màn Hình FFT toàn dải
            self._plot_audio_signal(audio_signal, f"Decode: Mẫu Phân Tích Bản Thu ({len(audio_signal)/SAMPLE_RATE:.1f}s)")

            decoded_digits = detect_dtmf_tone(audio_signal, SAMPLE_RATE)
            self._hien_thi_ket_qua(decoded_digits)

    def reset_record_ui(self):
        """Helper Khôi phục diện mạo hệ đồ chơi UI."""
        self.is_recording = False
        self.btn_record.config(state="normal", text="Bắt Đầu Thu Âm", bg="#F44336")
        self.btn_load_wav.config(state="normal")
        self.btn_encode.config(state="normal")

    def on_load_wav_decode(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file tín hiệu DTMF (.wav)",
            filetypes=(("WAV Audio Files", "*.wav"), ("All Files", "*.*"))
        )
        if not file_path: return 
            
        try:
            bn = os.path.basename(file_path)
            self.lbl_result.config(text=f"KẾT QUẢ > Import File: {bn}", fg="#FF9800")
            self.root.update()
            
            audio_signal, sr = load_wav(file_path)
            
            self._plot_audio_signal(audio_signal, f"Decode Mẫu: [{bn}]")
            
            decoded_digits = detect_dtmf_tone(audio_signal, sr)
            self._hien_thi_ket_qua(decoded_digits)
            
        except Exception as e:
            messagebox.showerror("Lỗi File", str(e))

    def _hien_thi_ket_qua(self, decoded_digits):
        if decoded_digits:
            self.lbl_result.config(text=f"KẾT QUẢ > Khớp Được: {decoded_digits}", fg="#388E3C")
        else:
            self.lbl_result.config(text="KẾT QUẢ > [Băng thông Im lặng / Nhiễu mờ]", fg="#757575")


def run():
    root = tk.Tk()
    app = DTMFApp(root)
    root.mainloop()

if __name__ == "__main__":
    run()
