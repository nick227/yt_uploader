import logging
import signal
import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.splash_screen import show_splash_screen

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

    # Show splash screen immediately
    splash = show_splash_screen()

    # Allow Python to process signals every 500ms
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    # Import MainWindow after QApplication is created
    from app.ui.main_window import MainWindow

    # Create main window (this will take some time to load)
    w = MainWindow()

    # Finish splash screen and show main window
    splash.finish(w)
    w.show()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        w.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
