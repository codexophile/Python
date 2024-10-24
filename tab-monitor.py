import win32gui
import win32con
import win32process
import psutil
import time
import logging
from typing import Optional

class BrowserMonitor:
    def __init__(self, browser_name='chrome'):
        self.browser_name = browser_name.lower()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_browser_process_name(self) -> str:
        """Get the process name for the browser."""
        browser_processes = {
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'edge': 'msedge.exe',
            'vivaldi': 'vivaldi.exe'  # Added Vivaldi
        }
        return browser_processes.get(self.browser_name, 'chrome.exe')

    def get_browser_window_title_part(self) -> str:
        """Get the partial title to identify browser windows."""
        browser_titles = {
            'chrome': 'Chrome',
            'firefox': 'Mozilla Firefox',
            'edge': 'Edge',
            'vivaldi': 'Vivaldi'  # Added Vivaldi
        }
        return browser_titles.get(self.browser_name, 'Chrome')

    def get_cpu_usage(self, process_name: str) -> float:
        """Get total CPU usage for all instances of a process."""
        total_cpu = 0
        try:
            # For Vivaldi/Chrome, also check for related processes
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
        """Check if browser is likely loading based on CPU usage."""
        process_name = self.get_browser_process_name()
        cpu_usage = self.get_cpu_usage(process_name)
        
        # Adjust threshold based on browser
        threshold = 15  # Default threshold
        if self.browser_name == 'vivaldi':
            threshold = 20  # Slightly higher threshold for Vivaldi
            
        return cpu_usage > threshold

    def get_browser_window(self) -> Optional[int]:
        """Find the browser window handle."""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                
                # Handle Vivaldi's different window title patterns
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

    def focus_window(self, hwnd: int) -> None:
        """Bring a window to front and focus it."""
        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Bring to front
            win32gui.SetForegroundWindow(hwnd)
            
            self.logger.info("Browser window focused successfully")
        except Exception as e:
            self.logger.error(f"Error focusing window: {e}")

    def monitor_browser(self):
        """Main monitoring loop."""
        self.logger.info(f"Starting browser monitoring for {self.browser_name}...")
        
        was_loading = False
        
        while True:
            try:
                is_loading = self.is_browser_loading()
                
                # Detect transition from loading to not loading
                if was_loading and not is_loading:
                    self.logger.info("Browser finished loading")
                    hwnd = self.get_browser_window()
                    if hwnd:
                        self.focus_window(hwnd)
                    time.sleep(2)  # Wait before checking again
                
                was_loading = is_loading
                time.sleep(0.5)  # Check interval
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
                continue

if __name__ == "__main__":
    # You can now use 'vivaldi' as browser name
    monitor = BrowserMonitor('vivaldi')  # Change this to your preferred browser
    try:
        monitor.monitor_browser()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")