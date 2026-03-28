@echo off
echo =======================================================
echo     CONG CU BIEN DICH DTMF ANALYZER (PYTHON -^> EXE)
echo =======================================================
echo.
echo [*] Dang kiem tra va cai dat PyInstaller...
python -m pip install pyinstaller matplotlib numpy scipy sounddevice soundfile

echo.
echo [*] Bat dau tien trinh dong goi (Chuyen doi ra .exe)
echo [*] Vui long cho doi trong giay lat. Tien trinh co the mat 1-2 phut khi tich hop engine do hoa Matplotlib...
echo.

python -m PyInstaller --name "DTMF_Analyzer_Desktop" --noconsole --onefile ./desktop_app/gui_app.py --clean

echo.
echo =======================================================
echo [*] Build hoan tat 100%%!
echo [*] Ung dung cua ban dang nam o thu muc: dist\DTMF_Analyzer_Desktop.exe
echo =======================================================
pause
