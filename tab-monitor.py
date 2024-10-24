from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pygetwindow as gw
import time
import psutil
import win32gui
import win32con
import sys
import logging

class TabLoadMonitor:
    def __init__(self, browser_name='chrome'):
        self.browser_name = browser_name.lower()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_browser_window_title(self):
        """Get the title of the browser window based on browser name."""
        browser_titles = {
            'chrome': 'Chrome',
            'firefox': 'Firefox',
            'edge': 'Edge'
        }
        return browser_titles.get(self.browser_name)

    def is_page_loaded(self, driver):
        """Check if the page is completely loaded."""
        try:
            # Wait for the document.readyState to be 'complete'
            return driver.execute_script("return document.readyState") == "complete"
        except Exception as e:
            self.logger.error(f"Error checking page load status: {e}")
            return False

    def focus_browser_window(self):
        """Bring the browser window to front."""
        try:
            browser_title = self.get_browser_window_title()
            if not browser_title:
                self.logger.error("Unsupported browser")
                return False

            # Find and focus the window
            windows = gw.getWindowsWithTitle(browser_title)
            if windows:
                try:
                    windows[0].activate()
                    return True
                except Exception as e:
                    self.logger.error(f"Error activating window: {e}")
                    return False
            return False
        except Exception as e:
            self.logger.error(f"Error focusing browser window: {e}")
            return False

    def monitor_tab_load(self):
        """Main function to monitor tab loading and switch focus."""
        try:
            # Connect to existing browser session
            options = webdriver.ChromeOptions()  # Adjust based on browser
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            driver = webdriver.Chrome(options=options)
            
            self.logger.info("Starting tab load monitoring...")
            
            while True:
                try:
                    # Check if page is still loading
                    if not self.is_page_loaded(driver):
                        self.logger.info("Page is loading...")
                        
                        # Wait for page to complete loading
                        WebDriverWait(driver, timeout=300).until(
                            lambda d: self.is_page_loaded(d)
                        )
                        
                        # Once loaded, focus the browser window
                        if self.focus_browser_window():
                            self.logger.info("Page loaded - Browser window focused")
                        else:
                            self.logger.warning("Could not focus browser window")
                    
                    time.sleep(1)  # Check interval
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(1)  # Wait before retrying
                    
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            return False
        
        finally:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    monitor = TabLoadMonitor()
    monitor.monitor_tab_load()