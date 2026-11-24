# Yaze – Real-Time Network Monitoring System for Windows

A lightweight, native Windows network monitoring application built with Python and PyQt6.

## Features
- **Real-Time Taskbar/Tray Speed Display**: Dynamically updates the tray icon with current download and upload speeds.
- **Continuous Background Operation**: Keeps running in the system tray when the dashboard is closed; separate explicit Exit option in the tray menu.
- **Dynamic Speed Graph**: 60-second rolling visual graph for download and upload throughput.
- **Data Usage History**: Persistent SQLite database tracking daily, weekly, monthly, and all-time consumption.
- **Wi-Fi & Network Diagnostics**: SSID, signal strength, adapter name, IP address, and gateway.
- **Application-wise Network Monitoring**: Identifies active processes and their bandwidth consumption.
- **Low-Speed Toast Alerts**: Configurable alerts when speeds drop below a designated threshold.
- **Integrated Speed Test**: Measure real-time ping, download, and upload speeds.
- **Windows Auto-Startup**: One-click toggle in Settings via Windows Registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

## Installation & Running

```bash
# Run application
py main.py

# Run test suite
py -m unittest discover tests
```
