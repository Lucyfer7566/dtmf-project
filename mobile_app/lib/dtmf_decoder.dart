import 'dart:math';

/// Đây là phiên bản Dart của bộ giải mã (decoder) hệ thống DTMF sử dụng
/// năng lượng tần số Goertzel. Thuật toán này bám sát thiết kế và logic
/// tương tự như phiên bản Python gốc (không dùng thư viện ngoài cho Toán).
class DtmfDecoder {
  // Cấu hình mảng tần số Row/Col (Hz)
  static const List<double> rowFreqs = [697.0, 770.0, 852.0, 941.0];
  static const List<double> colFreqs = [1209.0, 1336.0, 1477.0, 1633.0];

  static const Map<String, List<double>> charToFreq = {
    '1': [697.0, 1209.0], '2': [697.0, 1336.0], '3': [697.0, 1477.0], 'A': [697.0, 1633.0],
    '4': [770.0, 1209.0], '5': [770.0, 1336.0], '6': [770.0, 1477.0], 'B': [770.0, 1633.0],
    '7': [852.0, 1209.0], '8': [852.0, 1336.0], '9': [852.0, 1477.0], 'C': [852.0, 1633.0],
    '*': [941.0, 1209.0], '0': [941.0, 1336.0], '#': [941.0, 1477.0], 'D': [941.0, 1633.0],
  };

  /// Áp dụng công thức Goertzel chuẩn (thực thi trên double).
  /// Quét 1 tần số [targetFreq] duy nhất bên trong [samples]. 
  /// Trả về bình phương biên độ (magnitude squared) tượng trưng cho mức "Năng Lượng".
  static double goertzelMagnitude(List<double> samples, int sampleRate, double targetFreq) {
    int n = samples.length;
    if (n == 0) return 0.0;

    double w = 2.0 * pi * targetFreq / sampleRate;
    double cosine = cos(w);
    double coeff = 2.0 * cosine;

    double sPrev = 0.0;
    double sPrev2 = 0.0;

    for (int i = 0; i < n; i++) {
        double s = samples[i] + (coeff * sPrev) - sPrev2;
        sPrev2 = sPrev;
        sPrev = s;
    }

    return (sPrev * sPrev) + (sPrev2 * sPrev2) - (coeff * sPrev * sPrev2);
  }

  /// Trả về Map {freq: energy} mô tả năng lượng trên tập các tần số List
  static Map<double, double> energiesForFreqs(List<double> samples, int sampleRate, List<double> freqs) {
    Map<double, double> result = {};
    for (var freq in freqs) {
      result[freq] = goertzelMagnitude(samples, sampleRate, freq);
    }
    return result;
  }

  /// Hàm chia cắt 1 mảng sóng liền mạch khổng lồ thành nhiều List tín hiệu con.
  /// Mục đích: Để quét liên tục qua từng lát cắt (VD: 0.1 sec = 100ms) tránh nuốt phím.
  static List<List<double>> frameSignal(List<double> signal, int sampleRate, double frameDurationSec) {
    int frameSize = (frameDurationSec * sampleRate).toInt();
    if (frameSize <= 0) return [];

    List<List<double>> frames = [];
    int start = 0;
    
    while (start < signal.length) {
      int end = start + frameSize;
      if (end > signal.length) end = signal.length;
      List<double> frame = signal.sublist(start, end);
      
      // Giữ lại các frame có kích thước tương đối dài
      if (frame.length >= frameSize / 2) {
        frames.add(frame);
      }
      start = end;
    }
    
    return frames;
  }

  /// Quét qua 4 cột 4 hàng của 1 Frame để thu nạp tần số max.
  /// Nếu cả hai dải đều pass ngưỡng tĩnh [threshold] tuyệt đối, 
  /// map lại thành String bấm phím.
  static String? detectDigitFromFrame(List<double> frame, int sampleRate, double threshold) {
    var rowEnergies = energiesForFreqs(frame, sampleRate, rowFreqs);
    double maxRowEnergy = -1.0;
    double maxRowFreq = 0.0;
    rowEnergies.forEach((freq, energy) {
      if (energy > maxRowEnergy) {
        maxRowEnergy = energy;
        maxRowFreq = freq;
      }
    });

    var colEnergies = energiesForFreqs(frame, sampleRate, colFreqs);
    double maxColEnergy = -1.0;
    double maxColFreq = 0.0;
    colEnergies.forEach((freq, energy) {
      if (energy > maxColEnergy) {
        maxColEnergy = energy;
        maxColFreq = freq;
      }
    });

    // ----------------------------------------------------
    // IN LOG ĐỂ DEBUG VÀ TUNING (ĐIỀU CHỈNH) NGƯỠNG THRESHOLD
    // ----------------------------------------------------
    // Bật dòng print dưới đây để xem trực tiếp năng lượng nhận được từ Mic có đủ mạnh không
    // print('Goertzel [ROW]: MaxFreq=$maxRowFreq, Energy=$maxRowEnergy | [COL]: MaxFreq=$maxColFreq, Energy=$maxColEnergy');

    // Chốt sổ: Có phải là tạp âm im lặng (noise)? Hay đã vượt threshold đủ to để gáy?
    if (maxRowEnergy > threshold && maxColEnergy > threshold) {
      String? matchedChar;
      charToFreq.forEach((char, freqs) {
        if (freqs[0] == maxRowFreq && freqs[1] == maxColFreq) {
          matchedChar = char;
        }
      });
      return matchedChar;
    }

    return null;
  }

  /// Thuật toán bao quát: Giải mã một dãy Float âm thanh bất kỳ.
  /// 
  /// **HƯỚNG DẪN TUNING (TINH CHỈNH NGƯỠNG THRESHOLD) KHI TEST THỰC TẾ:**
  /// - `energyThreshold`: Mức năng lượng tối thiểu (Magnitude Squared) để phân biệt tín hiệu DTMF với rác tạp âm.
  /// - **[1] TĂNG `energyThreshold` (ví dụ: lên 3e4, 5e4, v.v)**: 
  ///   Nếu mảng bắt quá nhạy sinh ra các False Positive (app tự nhảy ra số linh tinh kể cả khi có người chỉ đang nói chuyện hoặc gió thổi).
  /// - **[2] GIẢM `energyThreshold` (ví dụ: xuống 1000.0, 500.0)**: 
  ///   Nếu mic thiết bị thu bị nhỏ bẩm sinh, loa điện thoại ngoài mở nhỏ, bạn bật phát âm thanh ngay sát Mic rồi mà ứng dụng không chịu gắp ký tự hiển thị ra giao diện.
  static String decodeDtmfSignal(List<double> signal, {
    int sampleRate = 8000,
    double frameDurationSec = 0.1,  
    // Mảng [-1, 1] khi dùng Goertzel với frame 100ms (N=800) thường cho mức Magnitude
    // tầm vài chục ngàn. Ngưỡng Absolute Threshold khởi điểm 1e4 (10000.0) là giá trị cực tốt.
    double energyThreshold = 10000.0, 
  }) {
    List<List<double>> frames = frameSignal(signal, sampleRate, frameDurationSec);
    
    StringBuffer decodedString = StringBuffer();
    String? lastChar;

    for (var frame in frames) {
      String? currentChar = detectDigitFromFrame(frame, sampleRate, energyThreshold);
      
      // Lọc lặp đè logic chặn hiện tượng dính nút lặp lại liền kề.
      if (currentChar != null) {
        if (currentChar != lastChar) {
          decodedString.write(currentChar);
        }
      }
      lastChar = currentChar;
    }

    return decodedString.toString();
  }
}
