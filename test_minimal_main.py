#!/usr/bin/env python3
"""
Minimal test version of main window to isolate hanging issue.
"""

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget


def main():
    app = QApplication(sys.argv)

    # Create a simple main window without complex initialization
    window = QMainWindow()
    window.setWindowTitle("Test Main Window")
    window.setGeometry(100, 100, 800, 600)

    # Simple central widget
    central = QWidget()
    layout = QVBoxLayout(central)

    label = QLabel("If you can see this, the main window loads successfully!")
    label.setStyleSheet("font-size: 16px; padding: 20px;")
    layout.addWidget(label)

    window.setCentralWidget(central)
    window.show()

    print("Main window created successfully!")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
