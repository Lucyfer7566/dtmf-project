// Lệnh yêu cầu cài đặt Plugin trước khi chạy:
// flutter pub add record
// flutter pub get

import 'dart:async';
import 'dart:typed_data';
import 'package:record/record.dart';

class AudioInput {
  // Đối tượng AudioRecorder cung cấp sẵn hàm stream PCM nhẹ và mạnh mẽ
  static final AudioRecorder _audioRecorder = AudioRecorder();

  /// Hàm khởi tạo ghi âm: Request quyền Microphone trên Android/iOS
  static Future<bool> requestMicrophonePermission() async {
    // Gọi hasPermission(), nếu chưa có hệ thống Native Android/iOS sẽ bắn Popup xin quyền
    return await _audioRecorder.hasPermission();
  }

  /// START -> COLLECT -> STOP
  /// Bắt đầu stream PCM từ mic. Thu mẫu trong khoảng thời gian [duration]. 
  /// Trả về mảng 16-bit PCM tuyến tính cho bộ Goertzel.
  static Future<List<int>> recordPcmSamples({
    int sampleRate = 8000, 
    Duration duration = const Duration(seconds: 2)
  }) async {
    
    // 1. Xin quyền
    if (!await requestMicrophonePermission()) {
      throw Exception("Quyền Microphone đã bị từ chối.");
    }

    // 2. Chuyển cấu hình yêu cầu chuẩn xác cho DTMF: PCM 16-bit, Mono
    final config = RecordConfig(
      encoder: AudioEncoder.pcm16bits,
      sampleRate: sampleRate,
      numChannels: 1, 
    );

    // Biến tạm để nhồi (collect) mẫu dạng Byte rời rạc
    final List<int> rawBytes = [];
    
    // Khởi tạo Stream
    final stream = await _audioRecorder.startStream(config);

    // START: Lắng nghe Microphone và đưa từng chuỗi Uint8List vào mảng rawBytes (COLLECT)
    final subscription = stream.listen((Uint8List data) {
      rawBytes.addAll(data);
    });

    // Chờ hệ thống ghi âm đúng khoảng thời gian duration quy định
    await Future.delayed(duration);

    // STOP: Hủy bỏ lắng nghe Microphone và ra lệnh dừng Hardware Microphone
    await subscription.cancel();
    await _audioRecorder.stop();

    // 3. XỬ LÝ BYTE: Ghép 2 biến 8-bit lại thành mẫu PCM 16-bit dao động [-32768..32767]
    var byteData = Uint8List.fromList(rawBytes);
    // Hàm Int16List.view rất hiệu quả, tự động gộp các byte liền nhau tạo thành chuỗi 16-bit theo Endian hiện hành
    var pcm16Data = Int16List.view(byteData.buffer);

    return pcm16Data.toList();
  }
}
