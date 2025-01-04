### test_progress_infobar.py
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton)
from UI.dialogs.progress_infobar import ProgressInfoBar, InfoBarIcon, InfoBarPosition


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress InfoBar Test")
        layout = QVBoxLayout(self)
        self.button = QPushButton("Start Progress", self)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.start_progress)

    def start_progress(self):
        self.info_bar = ProgressInfoBar.new(
            icon=InfoBarIcon.INFORMATION,
            title="Operation in Progress",
            content="This is a test of the progress info bar.",
            duration=-1,  # Keep it visible until manually closed
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=self
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # Update every 100 milliseconds
        self.progress = 0

    def update_progress(self):
        self.progress += 5
        self.info_bar.set_progress(self.progress)
        if self.progress >= 100:
            self.timer.stop()
            self.info_bar.set_title("Operation Complete!")
            self.info_bar.set_content("The operation has finished successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())