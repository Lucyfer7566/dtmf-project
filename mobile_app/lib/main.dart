import 'dart:io';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import 'dtmf_encoder.dart';
import 'audio_input.dart';
import 'dtmf_decoder.dart';
import 'widgets/piano_roll_painter.dart';

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

  // --- TRẠNG THÁI LIVE STREAM ---
  bool _isRecording = false;
  StreamSubscription<List<int>>? _audioSub;
  final List<double> _audioBuffer = [];
  final int _sampleRate = 8000;
  final int _frameSize = 800; // 100ms: Tăng từ 40ms lên 100ms để Năng lượng Goertzel cực đại như lúc code cũ (chống hụt năng lượng theo hàm N^2)
  final List<List<double>> _pianoRollHistory = [];
  String? _lastChar;
  int _chunkCounter = 0;
  
  // Trục trượt màn hình hiển thị toàn cảnh biểu đồ
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _audioSub?.cancel();
    _scrollController.dispose();
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

  /// Nút Microphone (Live Stream Decode)
  Future<void> _toggleRecord() async {
    if (_isRecording) {
      await _stopRecording();
    } else {
      await _startRecording();
    }
  }

  Future<void> _startRecording() async {
    try {
      final stream = await AudioInput.startRecordStream(sampleRate: _sampleRate);
      setState(() {
        _isRecording = true;
        _decodeResult = '';
        _pianoRollHistory.clear();
        _audioBuffer.clear();
        _lastChar = null;
        _chunkCounter = 0;
        _statusMessage = 'Đang kích hoạt vòi lấy mẫu Mic...';
      });

      _audioSub = stream.listen((List<int> chunk) {
        try {
          // Bơm thẳng dữ liệu vào bộ óc xử lý
          final doubleChunk = chunk.map((c) => c / 32768.0).toList();
          _audioBuffer.addAll(doubleChunk);
          _processLiveBuffer();
        } catch(e) {
          if (mounted) setState(() => _statusMessage = 'Lỗi Map Data: $e');
        }
      }, onError: (err) {
        if (mounted) setState(() => _statusMessage = 'Lỗi Mic Rớt Luồng: $err');
      });
      
    } catch (e) {
      setState(() {
        _statusMessage = 'LỖI PHẦN CỨNG BẬT MIC: $e';
        _isRecording = false;
      });
    }
  }

  void _processLiveBuffer() {
    bool hasNewFrame = false;
    final allFreqs = [...DtmfDecoder.rowFreqs, ...DtmfDecoder.colFreqs];
    double tempDebugMaxEnergy = 0.0;

    // Cắt mảng âm thanh trôi chảy thành các khối vuông cố định (_frameSize)
    while (_audioBuffer.length >= _frameSize) {
      final frame = _audioBuffer.sublist(0, _frameSize);
      _audioBuffer.removeRange(0, _frameSize);
      
      List<double> frameEnergies = [];
      _chunkCounter++;
      
      // Tính Toán Phổ Goertzel
      final energies = DtmfDecoder.energiesForFreqs(frame, _sampleRate, allFreqs);
      for (var f in allFreqs) {
        double e = energies[f] ?? 0.0;
        frameEnergies.add(e);
        if (e > tempDebugMaxEnergy) tempDebugMaxEnergy = e;
      }
      
      // Ngưỡng 100.0 cực kỳ nhạy giống hệ thống Tĩnh 5s cũ. Khoá cổng tiếng gió.
      final char = DtmfDecoder.detectDigitFromFrame(frame, _sampleRate, 100.0);
      if (char != null) {
        if (char != _lastChar) {
          _decodeResult += char;
          _lastChar = char;
        }
      } else {
        _lastChar = null;
      }
      
      _pianoRollHistory.add(frameEnergies);
      
      // XOÁ BỎ: Hủy giới hạn độ dài History. Khách hàng giờ được xem lại toàn cảnh không bị xóa
      hasNewFrame = true;
    }
    
    if (hasNewFrame && mounted) {
      setState(() {
         // Cập nhật dòng trạng thái để User biết Mic có đang thực sự chạy và in ra Energy gốc
         _statusMessage = 'LIVE [Block $_chunkCounter]: Đỉnh sóng ${tempDebugMaxEnergy.toStringAsFixed(1)}';
      });
      
      // Auto-Scroll: Đẩy tự động biểu đồ giật theo thời gian thực về Phải ngoài cùng
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.jumpTo(_scrollController.position.maxScrollExtent);
        }
      });
    }
  }

  Future<void> _stopRecording() async {
     await _audioSub?.cancel();
     await AudioInput.stopRecordStream();
     setState(() {
       _isRecording = false;
       _statusMessage = 'Trạng thái: Đã dừng thu âm an toàn.';
     });
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
            const SizedBox(height: 15),

            // Nút Ghi Âm LIVE STREAM
            ElevatedButton.icon(
              onPressed: _toggleRecord,
              icon: Icon(_isRecording ? Icons.stop_circle : Icons.mic_rounded),
              label: Text(_isRecording ? '[LIVE] Dừng Ngay & Chốt Kết Quả' : 'Bắt Đầu Record LiveStream'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(55),
                backgroundColor: _isRecording ? Colors.red.shade400 : Colors.teal.shade400,
                foregroundColor: Colors.white,
                textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),

            const SizedBox(height: 15),
            
            // Khu vực trình chiếu Lưới Gạch Radar 8 Làn (Piano Roll) có Khả Năng Vuốt Kéo và Trục Y Tĩnh
            Container(
              height: 180, 
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.black,
                border: Border.all(color: Colors.white, width: 2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                children: [
                  // Cột Label Trục Y Cố Định (Fixed Y-Axis)
                  Container(
                    width: 45,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade900,
                      border: Border(right: BorderSide(color: Colors.white54, width: 1))
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: const [
                        Text('1633', style: TextStyle(color: Colors.lightGreenAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                        Text('1477', style: TextStyle(color: Colors.lightGreenAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                        Text('1336', style: TextStyle(color: Colors.lightGreenAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                        Text('1209', style: TextStyle(color: Colors.lightGreenAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                        Text('941', style: TextStyle(color: Colors.limeAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                        Text('852', style: TextStyle(color: Colors.limeAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                        Text('770', style: TextStyle(color: Colors.limeAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                        Text('697', style: TextStyle(color: Colors.limeAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                      ]
                    )
                  ),
                  // Phần Cuộn Lưới Nhiệt
                  Expanded(
                    child: ClipRRect(
                      borderRadius: const BorderRadius.only(topRight: Radius.circular(2), bottomRight: Radius.circular(2)),
                      child: SingleChildScrollView(
                        controller: _scrollController,
                        scrollDirection: Axis.horizontal,
                        child: CustomPaint(
                          // Thiết lập Width dài vô hạn: Lấy số lượng cột x 15 Pixels chiều ngang mỗi viên
                          // Trừ đi 45px do vướng cột Y-axis
                          size: Size(
                            _pianoRollHistory.length * 15.0 > (MediaQuery.of(context).size.width - 45 - 48) 
                              ? _pianoRollHistory.length * 15.0 
                              : (MediaQuery.of(context).size.width - 45 - 48),
                            180
                          ),
                          painter: PianoRollPainter(_pianoRollHistory),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 15),

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
