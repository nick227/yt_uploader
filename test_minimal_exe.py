#!/usr/bin/env python3
"""
Minimal test script for EXE packaging.
"""

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget


def main():
    app = QApplication(sys.argv)

    # Create a simple window
    window = QMainWindow()
    window.setWindowTitle("Test EXE")
    window.setGeometry(100, 100, 400, 300)

    # Create central widget
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)

    # Add a label
    label = QLabel("If you can see this, the EXE is working!")
    label.setStyleSheet("font-size: 16px; padding: 20px;")
    layout.addWidget(label)

    window.setCentralWidget(central_widget)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
