import 'dart:io';
import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import 'dtmf_encoder.dart';
import 'audio_input.dart';
import 'dtmf_decoder.dart';

void main() {
  runApp(const DtmfApp());
}

class DtmfApp extends StatelessWidget {
  const DtmfApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DTMF Mobile App',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.amber), 
        useMaterial3: true,
      ),
      home: const DtmfPage(),
    );
  }
}

class DtmfPage extends StatefulWidget {
  const DtmfPage({super.key});

  @override
  State<DtmfPage> createState() => _DtmfPageState();
}

class _DtmfPageState extends State<DtmfPage> {
  final TextEditingController _controller = TextEditingController();
  final AudioPlayer _player = AudioPlayer(); 
  String _statusMessage = 'Sẵn sàng ghi/phát DTMF...';
  
  // Biến lưu trữ văn bản giải mã
  String _decodeResult = 'Chưa Thu Âm';

  @override
  void dispose() {
    _controller.dispose();
    _player.dispose(); 
    super.dispose();
  }

  /// Nút Play (Encode)
  Future<void> _encodeAndPlayTone() async {
    final digits = _controller.text.trim();
    if (digits.isEmpty) {
      setState(() => _statusMessage = 'Lỗi: Vui lòng nhập số DTMF!');
      return;
    }

    try {
      final sampleRateCfg = 8000;
      final floatSignal = DtmfEncoder.generateDtmfSignal(
        digits, 
        sampleRate: sampleRateCfg,
        toneDurationSec: 0.4,
        silenceDurationSec: 0.2,
      );
      
      if (floatSignal.isEmpty) return;

      final pcmSignal = DtmfEncoder.floatToPcm16(floatSignal);
      final wavBytes = DtmfEncoder.createWavBytes(pcmSignal, sampleRateCfg);
      final tempFile = File('${Directory.systemTemp.path}/temp_dtmf.wav');
      await tempFile.writeAsBytes(wavBytes);
      
      await _player.setFilePath(tempFile.path);
      await _player.play();

      setState(() {
        _statusMessage = 'Đã phát hoàn tất mã $digits';
      });
      
    } catch (e) {
      setState(() => _statusMessage = 'Lỗi AUDIO_IO: $e');
    }
  }

  /// Nút Microphone (Decode)
  Future<void> _recordAndDecodeTone() async {
    try {
      setState(() {
        _statusMessage = 'Đang mở luồng Microphone thu âm 5s...';
        _decodeResult = 'Đang lắng nghe...';
      });

      // 1. Khởi tạo ghi âm từ audio_input.dart (Lấy mảng PCM 16-bit)
      final pcm = await AudioInput.recordPcmSamples(
        sampleRate: 8000, 
        duration: const Duration(seconds: 5)
      );

      if (pcm.isEmpty) {
        setState(() => _statusMessage = 'Lỗi: Thiết bị mic không trả về âm thanh!');
        return;
      }

      setState(() => _statusMessage = 'Đang chuẩn hóa biên độ mảng PCM...');

      // 2. Chuyển List<int> PCM 16-bit sang List<double> chuẩn hóa [-1.0..1.0]
      // Đã gỡ bỏ Auto-Gain vì mạch khuếch đại tự động sẽ hóa âm thanh quạt gió/im lặng 
      // thành sóng 1.0 cực đại gây ra False Positives (lỗi nhảy số ngẫu nhiên).
      // Việc chia đúng tỷ lệ thực 32768.0 kết hợp với threshold siêu thấp (100.0) là hoàn hảo nhất.
      final List<double> signal = pcm.map((val) => val / 32768.0).toList();

      setState(() => _statusMessage = 'Đang đưa vào Goertzel để phát hiện mã DTMF...');

      // 3. Phép gọi thuật toán giải mã 
      // Setup Threshold Threshold cực chuẩn: 100.0 (Bắt được sóng âm siêu bé từ Mic thực tế)
      final digits = DtmfDecoder.decodeDtmfSignal(signal, sampleRate: 8000, energyThreshold: 100.0);

      setState(() {
        _statusMessage = 'Hoàn tất! Cấu trúc xử lý thành công gốc ${pcm.length} mẫu.';
        if (digits.isEmpty) {
          _decodeResult = '[Dải Tĩnh / Không Phát Hiện Ký Tự]';
        } else {
          _decodeResult = digits;
        }
      });

    } catch (e) {
      // 4. Try/catch với các trường hợp cấp phép giấy phép từ chối mic
      setState(() {
        final errText = e.toString().toLowerCase();
        if (errText.contains('permission') || errText.contains('quyền') || errText.contains('từ chối')) {
          _statusMessage = 'CẢNH BÁO: App bị từ chối quyền hoặc chưa cấp quyền thu âm Microphone trên cài đặt máy!';
        } else {
          _statusMessage = 'LỖI HỆ THỐNG AUDIO: $e';
        }
        _decodeResult = '⚠ Lỗi';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ứng dụng DTMF Phổ Cập'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 32.0),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: 'Gõ mã (Vd: 888#A)',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.dialpad),
              ),
              keyboardType: TextInputType.text,
            ),
            
            const SizedBox(height: 20),
            
            ElevatedButton.icon(
              onPressed: _encodeAndPlayTone,
              icon: const Icon(Icons.speaker_group),
              label: const Text('Quy Trình 1: Bấm để Phát Ra Loa'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(55),
                backgroundColor: Colors.amber.shade100,
                textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
            
            const SizedBox(height: 40),
            const Divider(),
            const SizedBox(height: 20),

            // Nút Ghi Âm (Giao diện 2)
            ElevatedButton.icon(
              onPressed: _recordAndDecodeTone,
              icon: const Icon(Icons.mic_rounded),
              label: const Text('Quy Trình 2: Record (5s) & Decode'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(55),
                backgroundColor: Colors.teal.shade100,
                textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),

            const SizedBox(height: 20),

            // Hộp chứa bảng Decoded Text Result rất to và rõ ràng
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade300, width: 1.5)
              ),
              child: Column(
                children: [
                  const Text('Dữ Liệu Khớp Được:', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 8),
                  Text(
                    _decodeResult,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      color: _decodeResult.contains('Chưa') || _decodeResult.contains('Không') 
                        ? Colors.redAccent 
                        : Colors.green.shade800,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),

            const Spacer(),
            
            // Console Message dưới cùng
            Text(
              _statusMessage,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: _statusMessage.contains('Lỗ') ? Colors.redAccent : Colors.amber.shade900,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
