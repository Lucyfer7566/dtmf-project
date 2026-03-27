import 'dart:math';
import 'dart:typed_data';

class DtmfEncoder {
  // Bảng tần số chuẩn DTMF (Hz)
  static const List<double> rowFreqs = [697.0, 770.0, 852.0, 941.0];
  static const List<double> colFreqs = [1209.0, 1336.0, 1477.0, 1633.0];

  static const Map<String, List<double>> charToFreq = {
    '1': [697.0, 1209.0], '2': [697.0, 1336.0], '3': [697.0, 1477.0], 'A': [697.0, 1633.0],
    '4': [770.0, 1209.0], '5': [770.0, 1336.0], '6': [770.0, 1477.0], 'B': [770.0, 1633.0],
    '7': [852.0, 1209.0], '8': [852.0, 1336.0], '9': [852.0, 1477.0], 'C': [852.0, 1633.0],
    '*': [941.0, 1209.0], '0': [941.0, 1336.0], '#': [941.0, 1477.0], 'D': [941.0, 1633.0],
  };

  /// Sinh tín hiệu sóng DTMF, mảng trả về là danh sách các mẫu dạng float [-1.0, 1.0]
  static List<double> generateDtmfSignal(
    String digits, {
    int sampleRate = 8000,
    double toneDurationSec = 0.1,
    double silenceDurationSec = 0.05,
    double amplitude = 0.8,
  }) {
    List<String> validDigits = digits.toUpperCase().split('').where((c) => charToFreq.containsKey(c)).toList();
    if (validDigits.isEmpty) return [];

    int toneSamples = (toneDurationSec * sampleRate).toInt();
    int silenceSamples = (silenceDurationSec * sampleRate).toInt();
    
    // Tính tổng số lượng hạt mẫu (samples) cần cho chuỗi array đầu ra
    int totalSamples = (toneSamples * validDigits.length) + (silenceSamples * (validDigits.length - 1));
    List<double> outputSignal = List<double>.filled(totalSamples, 0.0);
    
    int currentIndex = 0;

    for (int i = 0; i < validDigits.length; i++) {
      String char = validDigits[i];
      double fRow = charToFreq[char]![0];
      double fCol = charToFreq[char]![1];

      // 1. Phân đoạn ghi sóng Tone cho phím được bấm
      for (int s = 0; s < toneSamples; s++) {
        double t = s / sampleRate;
        
        // Cấu trúc Sóng 1 + Sóng 2. Thiết lập amplitude/2 để tránh lệch biên (-1 tới 1)
        double wave1 = sin(2.0 * pi * fRow * t);
        double wave2 = sin(2.0 * pi * fCol * t);
        
        outputSignal[currentIndex++] = (wave1 + wave2) * (amplitude / 2.0);
      }

      // 2. Chèn khoảng lặng ngắt âm giữa các ký tự
      if (i < validDigits.length - 1) {
        for (int s = 0; s < silenceSamples; s++) {
          outputSignal[currentIndex++] = 0.0;
        }
      }
    }

    return outputSignal;
  }

  /// Loại bỏ nhiễu và ép kiểu đồ thị Float Normalized [-1.0, 1.0] vào khung PCM 16-bit [-32768, 32767]
  static List<int> floatToPcm16(List<double> signal) {
    List<int> pcmData = List<int>.filled(signal.length, 0);
    for (int i = 0; i < signal.length; i++) {
      double s = signal[i];
      
      // Setup Hard Limits: Sóng không được vượt quá 1.0 (âm thanh lạch tạch/clip)
      if (s > 1.0) s = 1.0;
      if (s < -1.0) s = -1.0;
      
      // Multiply tỷ lệ PCM 16 bit
      pcmData[i] = (s * 32767.0).round();
    }
    return pcmData;
  }

  /// Khung hàm phụ trợ để nhét Array PCM vào một lõi File WAV thuần bộ nhớ đệm
  static Uint8List createWavBytes(List<int> pcmData, int sampleRate) {
    int byteRate = sampleRate * 1 * 2; // Số byte / 1 block: 1 channel, 16 bit phân giải
    int dataSize = pcmData.length * 2;
    int fileSize = 36 + dataSize;
    
    // Ghi File Header chuân định dạng Audio RIFF / WAVE
    var header = ByteData(44);
    header.setUint8(0, 0x52); header.setUint8(1, 0x49); header.setUint8(2, 0x46); header.setUint8(3, 0x46);
    header.setUint32(4, fileSize, Endian.little);
    header.setUint8(8, 0x57); header.setUint8(9, 0x41); header.setUint8(10, 0x56); header.setUint8(11, 0x45);
    
    // Chunk "fmt "
    header.setUint8(12, 0x66); header.setUint8(13, 0x6D); header.setUint8(14, 0x74); header.setUint8(15, 0x20);
    header.setUint32(16, 16, Endian.little); 
    header.setUint16(20, 1, Endian.little); // Format: PCM không nén
    header.setUint16(22, 1, Endian.little); // Channels: 1
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, byteRate, Endian.little);
    header.setUint16(32, 2, Endian.little); // Block align
    header.setUint16(34, 16, Endian.little); // Bits per sample

    // Chunk "data"
    header.setUint8(36, 0x64); header.setUint8(37, 0x61); header.setUint8(38, 0x74); header.setUint8(39, 0x61);
    header.setUint32(40, dataSize, Endian.little);

    // Gộp mảng Payload dữ liệu vào khung Container
    var wavBytes = Uint8List(44 + dataSize);
    wavBytes.setAll(0, header.buffer.asUint8List());
    
    // Copy array PCM bytes
    var pcmBytes = ByteData(dataSize);
    for (int i = 0; i < pcmData.length; i++) {
      pcmBytes.setInt16(i * 2, pcmData[i], Endian.little);
    }
    wavBytes.setAll(44, pcmBytes.buffer.asUint8List());
    
    return wavBytes;
  }
}
