import win32gui
import win32con
import win32process
import psutil
import time
import logging
import sys
import os
from typing import Optional
import pystray
from PIL import Image
import threading
from logging.handlers import RotatingFileHandler
import winreg
from collections import deque
from datetime import datetime, timedelta

class BrowserMonitor:
    def __init__(self, browser_name='chrome'):
        self.browser_name = browser_name.lower()
        self.running = True
        self.setup_logging()
        self.setup_tray()
        
        # State tracking
        self.last_focus_time = datetime.now() - timedelta(minutes=5)
        self.cpu_history = deque(maxlen=6)  # Last 3 seconds of readings
        self.active_window_history = deque(maxlen=4)  # Last 2 seconds
        self.last_cpu_spike = datetime.now() - timedelta(minutes=5)
        
    def setup_logging(self):
        """Setup logging to file with rotation."""
        log_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'BrowserMonitor')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'browser_monitor.log')
        
        handler = RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024,
            backupCount=3
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def create_shortcut(self):
        """Create startup shortcut."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            script_path = os.path.abspath(sys.argv[0])
            if script_path.endswith('.py'):
                cmd = f'pythonw.exe "{script_path}"'
            else:
                cmd = f'"{script_path}"'
                
            winreg.SetValueEx(
                key,
                "BrowserMonitor",
                0,
                winreg.REG_SZ,
                cmd
            )
            winreg.CloseKey(key)
            return True
        except Exception as e:
            self.logger.error(f"Error creating startup entry: {e}")
            return False

    def remove_shortcut(self):
        """Remove startup shortcut."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, "BrowserMonitor")
            winreg.CloseKey(key)
            return True
        except Exception as e:
            self.logger.error(f"Error removing startup entry: {e}")
            return False

    def setup_tray(self):
        """Setup system tray icon and menu."""
        icon_image = Image.new('RGB', (64, 64), color='blue')
        
        menu = (
            pystray.MenuItem("Browser: " + self.browser_name, lambda: None),
            pystray.MenuItem("Run at startup", self.toggle_startup, checked=self.check_startup),
            pystray.MenuItem("Exit", self.stop_monitoring)
        )
        
        self.icon = pystray.Icon(
            "browser_monitor",
            icon_image,
            "Browser Monitor",
            menu
        )

    def check_startup(self, item):
        """Check if app is in startup."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            winreg.QueryValueEx(key, "BrowserMonitor")
            winreg.CloseKey(key)
            return True
        except:
            return False

    def toggle_startup(self, icon, item):
        """Toggle startup status."""
        if self.check_startup(item):
            self.remove_shortcut()
        else:
            self.create_shortcut()

    def stop_monitoring(self, icon, item):
        """Stop monitoring and exit."""
        self.running = False
        icon.stop()

    def get_browser_process_name(self) -> str:
        """Get the process name for the browser."""
        browser_processes = {
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'edge': 'msedge.exe',
            'vivaldi': 'vivaldi.exe'
        }
        return browser_processes.get(self.browser_name, 'chrome.exe')

    def get_active_window_title(self) -> str:
        """Get the title of the currently active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
        except:
            return ""

    def get_cpu_usage(self, process_name: str) -> float:
        """Get total CPU usage for all instances of a process."""
        total_cpu = 0
        try:
            related_processes = [process_name]
            if self.browser_name in ['chrome', 'vivaldi']:
                base_name = process_name.replace('.exe', '')
                related_processes.extend([
                    f"{base_name}GPU.exe",
                    f"{base_name}Renderer.exe"
                ])
            
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                if proc.info['name'] in related_processes:
                    total_cpu += proc.info['cpu_percent']
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
        return total_cpu

    def is_browser_loading(self) -> bool:
        """Enhanced detection of browser loading state."""
        current_time = datetime.now()
        
        # Get current CPU usage and update history
        cpu_usage = self.get_cpu_usage(self.get_browser_process_name())
        self.cpu_history.append(cpu_usage)
        
        # Get current active window and update history
        active_window = self.get_active_window_title()
        self.active_window_history.append(active_window)
        
        # Calculate average CPU usage
        avg_cpu = sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0
        
        # Determine threshold based on browser
        threshold = 20 if self.browser_name == 'vivaldi' else 15
        
        # Check if we're in cooldown period
        if (current_time - self.last_focus_time).total_seconds() < 5:
            return False
            
        # Check if there was a recent CPU spike
        if cpu_usage > threshold * 1.5:  # Significant spike
            self.last_cpu_spike = current_time
            return True
            
        # Check for sustained moderate CPU usage
        if avg_cpu > threshold and (current_time - self.last_cpu_spike).total_seconds() < 2:
            return True
            
        # Not loading
        return False

    def get_browser_window(self) -> Optional[int]:
        """Find the browser window handle."""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.browser_name == 'vivaldi':
                    if ' - Vivaldi' in title or title == 'Vivaldi':
                        windows.append(hwnd)
                else:
                    if self.get_browser_window_title_part() in title:
                        windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None

    def should_focus_window(self) -> bool:
        """Determine if we should focus the window."""
        current_time = datetime.now()
        
        # Check cooldown period
        if (current_time - self.last_focus_time).total_seconds() < 5:
            return False
            
        # Check if browser was recently active
        browser_was_active = any(
            self.browser_name.lower() in title.lower() 
            for title in list(self.active_window_history)[:-1]
        )
        
        # Don't focus if browser was just active
        if browser_was_active:
            return False
            
        return True

    def focus_window(self, hwnd: int) -> None:
        """Bring a window to front and focus it."""
        try:
            if self.should_focus_window():
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                self.last_focus_time = datetime.now()
                self.logger.info("Browser window focused successfully")
        except Exception as e:
            self.logger.error(f"Error focusing window: {e}")

    def monitor_browser(self):
        """Main monitoring loop."""
        self.logger.info(f"Starting browser monitoring for {self.browser_name}...")
        was_loading = False
        
        while self.running:
            try:
                is_loading = self.is_browser_loading()
                
                if was_loading and not is_loading:
                    self.logger.info("Browser finished loading")
                    hwnd = self.get_browser_window()
                    if hwnd:
                        self.focus_window(hwnd)
                    time.sleep(1)
                
                was_loading = is_loading
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)

    def run(self):
        """Run the monitor with system tray icon."""
        monitor_thread = threading.Thread(target=self.monitor_browser)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.icon.run()

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    monitor = BrowserMonitor('vivaldi')  # Change to your preferred browser
    monitor.run()