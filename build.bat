@echo off
pyinstaller --onefile --noconsole --icon icon.ico auto_clicker.py
move dist\auto_clicker.exe .
rmdir /s /q build
rmdir /s /q dist
del auto_clicker.spec
echo Build complete! auto_clicker.exe is ready.
