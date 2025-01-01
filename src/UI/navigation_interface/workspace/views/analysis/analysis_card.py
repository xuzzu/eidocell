from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QPainterPath, QPainter, QPen
from PySide6.QtWidgets import QVBoxLayout, QSizePolicy
from pathlib import Path
from qfluentwidgets import CaptionLabel, CardWidget, isDarkTheme
from qframelesswindow.webengine import FramelessWebEngineView
from backend.config import ANALYSIS_CARD_WIDTH, ANALYSIS_CARD_HEIGHT, ANALYSIS_CARD_IMAGE_HEIGHT

class AnalysisCard(CardWidget):
    """ Card for displaying analysis plots. """
    deleteRequested = Signal()
    doubleClicked = Signal(str)

    def __init__(self, html_file_path, parent=None):
        super().__init__(parent)
        self._borderRadius = 0
        self.html_file_path = html_file_path
        # self.label = CaptionLabel(Path(html_file_path).stem, self)  # Set label name from the file name
        self.web_view = FramelessWebEngineView(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)  # Remove card margins

        # Ensure web_view takes available space and caption label uses minimum space
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # For webview
        # self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.vBoxLayout.addWidget(self.web_view)  # stretch factor for webview
        # self.vBoxLayout.addWidget(self.label, 0, Qt.AlignHCenter | Qt.AlignBottom)

        self.card_height = ANALYSIS_CARD_HEIGHT
        self.card_width = ANALYSIS_CARD_WIDTH

        self.setFixedSize(self.card_width, self.card_height)

        # Connect loadFinished signal for debugging
        self.web_view.loadFinished.connect(self.on_load_finished)

        # Load the plot
        self.load_plot(html_file_path)

    def on_load_finished(self, success):
        if not success:
            print("Failed to load the plot HTML.")
        else:
            print("Plot HTML loaded successfully.")

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        return QColor(237, 255, 245, 90 if isDarkTheme() else 64)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        r = self.borderRadius
        d = 2 * r

        isDark = isDarkTheme()

        # draw top border
        path = QPainterPath()

        path.arcMoveTo(1, h - d - 1, d, d, 240)
        path.arcTo(1, h - d - 1, d, d, 225, -60)
        path.lineTo(1, r)
        path.arcTo(1, 1, d, d, -180, -90)
        path.lineTo(w - r, 1)
        path.arcTo(w - d - 1, 1, d, d, 90, -90)
        path.lineTo(w - 1, h - r)
        path.arcTo(w - d - 1, h - d - 1, d, d, 0, -60)

        topBorderColor = QColor(240, 240, 240, 60)
        if isDark:
            if self.isPressed:
                topBorderColor = QColor(255, 255, 255, 18)
            elif self.isHover:
                topBorderColor = QColor(255, 255, 255, 13)
        else:
            topBorderColor = QColor(240, 240, 240, 60)

        painter.strokePath(path, topBorderColor)

        # draw bottom border
        path = QPainterPath()
        path.arcMoveTo(1, h - d - 1, d, d, 240)
        path.arcTo(1, h - d - 1, d, d, 240, 30)
        path.lineTo(w - r - 1, h - 1)
        path.arcTo(w - d - 1, h - d - 1, d, d, 270, 30)

        bottomBorderColor = topBorderColor
        if not isDark and self.isHover and not self.isPressed:
            bottomBorderColor = QColor(0, 0, 0, 27)

        painter.strokePath(path, bottomBorderColor)

        # draw background and border
        pen = QPen(topBorderColor)
        pen.setWidth(3)
        painter.setPen(pen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(rect, r, r)

    def mouseReleaseEvent(self, e):  # Emit clicked signal on mouse release
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def load_plot(self, html_file_path):
        """Loads the specified HTML file into the web view."""
        print("Loading plot:", html_file_path)
        url = QUrl.fromLocalFile(html_file_path)
        if not Path(html_file_path).exists():
            print(f"HTML file does not exist: {html_file_path}")
        self.web_view.load(url)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.html_file_path)  # Emit the file path
