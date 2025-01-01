import random
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainterPath, QPainter, QPen, QContextMenuEvent, QMouseEvent
from PySide6.QtWidgets import QVBoxLayout, QMenu
from pathlib import Path
from qfluentwidgets import ImageLabel, CaptionLabel, CardWidget, isDarkTheme


class ClassCard(CardWidget):
    """ Gallery card """
    class_double_clicked = Signal(str)

    def __init__(self, iconPath: str, classes_presenter, class_id: str, parent=None):
        super().__init__(parent)
        self._borderRadius = 10
        self.iconWidget = ImageLabel(iconPath, self)
        self.label = CaptionLabel(Path(iconPath).stem, self)
        self.classes_presenter = classes_presenter
        self.class_id = class_id

        self.iconWidget.scaledToHeight(95)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignCenter)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.label, 0, Qt.AlignHCenter | Qt.AlignBottom)

        self.card_height = 136
        self.card_width = 128
        # create random color
        random_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.class_color = QColor(*random_color, 70)

        self.setFixedSize(self.card_width, self.card_height)

        self.class_double_clicked.connect(self.classes_presenter.show_class_viewer)

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 170)

    def _hoverBackgroundColor(self):
        return QColor(230, 230, 230, 90 if isDarkTheme() else 64)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        r = self.borderRadius
        d = 2 * r

        isDark = isDarkTheme()

        # draw top border
        path = QPainterPath()
        # path.moveTo(1, h - r)
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
            topBorderColor = self.class_color

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
        pen.setWidth(6)
        painter.setPen(pen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(rect, r, r)

    def mouseReleaseEvent(self, e):  # Emit clicked signal on mouse release
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Handles right-click context menu event."""
        menu = QMenu(self)
        menu.setStyleSheet("QMenu {background-color: #234f4b; color: white;}")
        show_summary_action = menu.addAction("Show Summary")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        # Connect actions to presenter methods (will be implemented later)
        if self.classes_presenter:  # Access the presenter from the parent widget
            show_summary_action.triggered.connect(lambda: self.classes_presenter.show_summary(self.class_id))
            rename_action.triggered.connect(lambda: self.classes_presenter.handle_rename_class(self.class_id))
            delete_action.triggered.connect(lambda: self.classes_presenter.delete_class(self.class_id))

        menu.exec_(event.globalPos())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handles double-click events."""
        if event.button() == Qt.LeftButton:
            self.class_double_clicked.emit(self.class_id)
