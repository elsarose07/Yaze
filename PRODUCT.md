# Product

<!-- impeccable:product-schema 1 -->

## Platform

windows-desktop

## Stack

Python 3.14 + PyQt6 + psutil + SQLite

## Users

Windows desktop power users, developers, remote workers, gamers, and network administrators who need real-time, low-overhead visibility into their internet bandwidth directly from their desktop without opening heavy web speedtests or external browser tabs.

## Product Purpose

Yaze provides an ultra-lightweight, native Windows network telemetry system that lives in the taskbar and system tray, delivering instantaneous download and upload rate indicators, a 60-second rolling visual oscilloscope graph, persistent historical consumption analytics, per-application bandwidth accounting, and on-demand bandwidth testing.

## Positioning

Unlike bloated Electron-based system monitors or ad-heavy online speedtest websites, Yaze runs with a native C/Python memory footprint (<45 MB RAM), updates dynamically every second directly on the Windows taskbar tray icon, and keeps running reliably in the background when the main window is dismissed.

## Operating Context

- Windows 10 & Windows 11 desktop environments.
- Continual background operation with tray icon minimization.
- Auto-launch via Windows CurrentVersion\\Run registry on system boot.
- Low-latency sampling of network interfaces and socket connections.

## Capabilities and Constraints

- Continuous background process with QSystemTrayIcon and explicit tray Exit option.
- Dynamic QPainter tray icon rendering live upload and download text in real-time.
- 60-second rolling dual-stream speed graph (Download & Upload).
- SQLite persistent storage for daily, weekly, and all-time traffic totals.
- Wi-Fi SSID, BSSID, signal strength percentage, and network adapter diagnostics.
- Throttled low-speed alert engine with configurable threshold and cooldown.
- Process-level bandwidth consumption tracker.
- Built-in multi-chunk HTTP speed test (latency, download, upload).

## Brand Commitments

- Name: Yaze
- Aesthetic: Studio Minimalist (Deep graphite #121214, crisp white data typography #FFFFFF, precise telemetry signal highlights).
- Tone: High precision, unobtrusive, utility-first, calm, and reliable.

## Evidence on Hand

- Verified psutil network I/O counters and connection sampling.
- Pre-installed and passing PyQt6 test suite in `tests/`.
- Embedded Cloudflare Edge speed test endpoints.

## Product Principles

1. Zero Overhead: Low CPU and RAM usage (<45 MB) to never disrupt gaming or compilation.
2. Immediate Glanceability: Critical numbers (speed, ping, connection) readable in under 200 ms.
3. Uninterrupted Presence: Never terminate unless explicitly instructed via the tray Exit action.
4. Data Integrity: Store bandwidth metrics locally in SQLite without cloud transmission.
