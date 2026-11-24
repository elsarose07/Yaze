"""Manages Windows startup registry entry for automatic launch on boot."""

import os
import sys
import winreg

APP_NAME = "Yaze"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

class StartupManager:
    """Controls auto-startup via Windows CurrentVersion\\Run registry."""

    @staticmethod
    def get_launch_command() -> str:
        """Construct the launch command for running Yaze in the background."""
        # If frozen as an executable (PyInstaller)
        if getattr(sys, "frozen", False):
            exe_path = sys.executable
            return f'"{exe_path}" --tray'
        else:
            # Running as Python script
            python_exe = sys.executable
            # Ensure pythonw.exe is used if available to avoid opening a console window
            pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
            target_python = pythonw if os.path.exists(pythonw) else python_exe
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
            return f'"{target_python}" "{script_path}" --tray'

    @staticmethod
    def is_auto_start_enabled() -> bool:
        """Check if Yaze is configured in HKCU Run registry."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(value)
        except FileNotFoundError:
            return False
        except Exception:
            return False

    @staticmethod
    def set_auto_start(enabled: bool) -> bool:
        """Enable or disable auto-start on Windows login."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    cmd = StartupManager.get_launch_command()
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            print(f"Error updating Windows startup registry: {e}")
            return False
