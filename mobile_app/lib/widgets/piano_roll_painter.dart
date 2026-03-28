import 'package:flutter/material.dart';

class PianoRollPainter extends CustomPainter {
  final List<List<double>> energyGrid;
  
  PianoRollPainter(this.energyGrid);

  @override
  void paint(Canvas canvas, Size size) {
    // 1. Dọn nền đen để nổi khối (Y như Magma 0.0)
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), Paint()..color = Colors.black);

    if (energyGrid.isEmpty) return;
    
    final paint = Paint()..style = PaintingStyle.fill;
    final rowCount = 8; // 8 Làn tần số
    final colCount = energyGrid.length;
    
    final cellHeight = size.height / rowCount;
    // Độ rộng cố định mỗi viên gạch 15 pixels để có thể kéo thả vuốt ngang
    final cellWidth = 15.0; 
    
    // 2. Kẻ lót vạch Dạ Quang như trên bản Desktop Python
    // Vùng Low Freqs (4 Làn màu Vàng) - Ở Dưới cùng màn hình (Y cao nhất trong Flutter)
    canvas.drawRect(Rect.fromLTWH(0, cellHeight * 4, size.width, size.height), Paint()..color = Colors.yellow.withOpacity(0.08));
    // Vùng High Freqs (4 Làn màu Xanh) - Ở Nửa trên màn hình
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, cellHeight * 4), Paint()..color = Colors.green.withOpacity(0.08));

    // 3. Đường Ranh Giới Giữa màn hình
    canvas.drawLine(Offset(0, cellHeight * 4), Offset(size.width, cellHeight * 4), Paint()..color = Colors.white54..strokeWidth = 2);

    // Kẻ chỉ lưới (Grid lines mờ mờ cho dễ gióng mắt)
    for (int i = 1; i < rowCount; i++) {
        canvas.drawLine(Offset(0, cellHeight * i), Offset(size.width, cellHeight * i), Paint()..color = Colors.white24..strokeWidth = 1);
    }

    // Auto-Gain Kép (Dual Auto-Gain Visualization): 
    // Loa và Micro điện thoại thường có dải đáp ứng tần số không đồng đều (High-Freq thường to hơn Low-Freq rất nhiều).
    // Phải lùng sục Lửa to nhất của Nhóm Thấp và Nhóm Cao hoàn toàn BIỆT LẬP để tự động bù trừ âm lượng 2 dải.
    double maxLowEnergy = 500.0; 
    double maxHighEnergy = 500.0; 
    
    for (var colItems in energyGrid) {
      if (colItems.length >= 8) {
        for (int r = 0; r < 4; r++) {
          if (colItems[r] > maxLowEnergy) maxLowEnergy = colItems[r];
        }
        for (int r = 4; r < 8; r++) {
          if (colItems[r] > maxHighEnergy) maxHighEnergy = colItems[r];
        }
      }
    }

    // 4. Vẽ Toàn Cảnh (Draw All)
    for (int col = 0; col < colCount; col++) {
      final x = col * cellWidth;
      
      for (int row = 0; row < rowCount; row++) {
        final double energy = energyGrid[col][row];
        
        // Đảo chiều Y vì Toạ độ Flutter (0,0) nằm ở đỉnh góc trái màn hình.
        // Hàng 0 (697Hz) sẽ nằm tận đáy `size.height - 1 * cellHeight`.
        final y = size.height - (row + 1) * cellHeight;
        
        // Chọn điểm uốn tuỳ thuộc vào Dải Tần của nó
        double currentMaxE = (row < 4) ? maxLowEnergy : maxHighEnergy;
        
        // Auto-Gain Thực Tế:
        double intensity = energy / currentMaxE;
        
        // Cửa Gác Đóng/Mở Nguyên Khối: Chỉ vẽ Khối khi Cường độ vượt ngưỡng 20%
        if (intensity < 0.20) continue; 
        
        paint.color = _getSolidToneColor(row);
        canvas.drawRect(Rect.fromLTWH(x, y, cellWidth, cellHeight), paint);
      }
    }
  }

  // Khóa Cứng 2 Làn Ánh Sáng Đơn Sắc Tuyệt Đối (Solid Colors)
  Color _getSolidToneColor(int row) {
    if (row >= 4) {
      return Colors.lightGreenAccent; // Đúng 1 loại màu Xanh Sáng chói cho mọi cường độ
    } else {
      return Colors.amberAccent; // Đúng 1 loại màu Vàng Sáng chói cho mọi cường độ
    }
  }

  @override
  bool shouldRepaint(covariant PianoRollPainter oldDelegate) => true;
}
