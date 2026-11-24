@echo off
echo Building Yaze Standalone Windows Executable with PyInstaller...
py -m PyInstaller --noconsole --onefile --name Yaze --icon ui/yaze.ico --add-data "ui;ui" --add-data "core;core" main.py
echo Build complete! Check the dist\ folder for Yaze.exe.
pause
