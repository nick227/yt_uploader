import logging
import signal
import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

# Configure logging for production
logging.basicConfig(level=logging.WARNING)
logging.getLogger("google_auth_httplib2").setLevel(logging.ERROR)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
logging.getLogger("googleapiclient.discovery").setLevel(logging.ERROR)


def signal_handler(signum, frame):
    """Handle Ctrl+C signal gracefully."""
    QApplication.quit()


def main():
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    app = QApplication(sys.argv)

    print("Creating simple main window without auth...")

    # Create a simple main window without authentication
    window = QMainWindow()
    window.setWindowTitle("Media Uploader (No Auth)")
    window.setGeometry(100, 100, 800, 600)

    central = QWidget()
    layout = QVBoxLayout(central)

    label = QLabel("Main window loaded successfully without authentication!")
    label.setStyleSheet("font-size: 16px; padding: 20px;")
    layout.addWidget(label)

    window.setCentralWidget(central)
    window.show()

    print("Main window created and shown successfully!")

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        window.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
