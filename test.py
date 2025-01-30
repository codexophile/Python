import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLineEdit, QPushButton, QProgressBar, QTextEdit)
from PyQt6.QtCore import QThread, pyqtSignal

class DownloadWorker(QThread):
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    download_progress = pyqtSignal(float)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.process = None

    def run(self):
        try:
            # Create the yt-dlp process
            self.process = subprocess.Popen(
                ['yt-dlp', self.url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Read output line by line
            for line in self.process.stdout:
                self.progress.emit(line.strip())
                
                # Parse progress information
                if '[download]' in line:
                    try:
                        # Extract percentage from lines like "[download]  50.0% of ~50.00MiB"
                        if "% of" in line:
                            percentage = float(line.split("%")[0].split()[-1])
                            self.download_progress.emit(percentage)
                    except (ValueError, IndexError):
                        pass

            # Check for errors
            error = self.process.stderr.read()
            if error:
                self.error.emit(error)

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        if self.process:
            self.process.terminate()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT-DLP GUI")
        self.setMinimumSize(600, 400)
        self.worker = None

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL...")
        layout.addWidget(self.url_input)

        # Download and Stop buttons
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Output display
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        layout.addWidget(self.output_display)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.output_display.append("Error: Please enter a URL")
            return

        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.output_display.clear()

        self.worker = DownloadWorker(url)
        self.worker.progress.connect(self.update_output)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.download_finished)
        self.worker.download_progress.connect(self.update_progress)
        self.worker.start()

    def stop_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.output_display.append("Download stopped by user")
            self.download_finished()

    def update_output(self, text):
        self.output_display.append(text)

    def handle_error(self, error):
        self.output_display.append(f"Error: {error}")

    def update_progress(self, percentage):
        self.progress_bar.setValue(int(percentage))

    def download_finished(self):
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.worker = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())