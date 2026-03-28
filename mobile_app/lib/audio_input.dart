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

  /// Bắt đầu stream PCM từ mic không giới hạn thời gian. 
  /// Trả về luồng Suối Stream các mẫu PCM 16-bit liên tục bắn về UI.
  static Future<Stream<List<int>>> startRecordStream({
    int sampleRate = 8000, 
  }) async {
    // 1. Xin quyền
    if (!await requestMicrophonePermission()) {
      throw Exception("Quyền Microphone đã bị từ chối.");
    }

    // 2. Cấu hình yêu cầu chuẩn xác cho DTMF: PCM 16-bit, Mono
    final config = RecordConfig(
      encoder: AudioEncoder.pcm16bits,
      sampleRate: sampleRate,
      numChannels: 1, 
    );

    // 3. Khởi tạo Stream ngầm của phần cứng cắm vô ống nước
    final rawStream = await _audioRecorder.startStream(config);

    // Lọc ống nước Map Stream để Biến Đổi Bão Hòa: Uint8 -> Int16
    return rawStream.map((Uint8List data) {
      // Dùng rào ảo ByteData để đọc bit độc lập mà không bị kẹt lỗi Alignment của iOS/Android
      var byteData = ByteData.sublistView(data);
      List<int> pcm16Data = List.filled(byteData.lengthInBytes ~/ 2, 0);
      for (int i = 0; i < byteData.lengthInBytes - 1; i += 2) {
        // Giải phẫu Endian.little vì Audio Cổ Điển hay xuất Endian bé
        pcm16Data[i ~/ 2] = byteData.getInt16(i, Endian.little);
      }
      return pcm16Data;
    });
  }

  /// Cắt cầu dao dừng luồng Record
  static Future<void> stopRecordStream() async {
    await _audioRecorder.stop();
  }
}
