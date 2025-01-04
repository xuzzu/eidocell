import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from UI.navigation_interface.sessions.create_session_dialog import CreateSessionDialog
from qfluentwidgets import (
    SingleDirectionScrollArea,
    FluentStyleSheet,
    isDarkTheme,
    getIconColor,
)
from qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase


class ClickableWindow(QWidget):
    """Clickable window"""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(292, 72)
        self._isPressed = None
        self._isEnter = False

    def enterEvent(self, e):
        self._isEnter = True
        self.update()

    def leaveEvent(self, e):
        self._isEnter = False
        self.update()

    def mouseReleaseEvent(self, e):
        self._isPressed = False
        self.update()
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

    def mousePressEvent(self, e: QMouseEvent):
        self._isPressed = True
        self.update()

    def paintEvent(self, e):
        """paint window"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        bg = 51 if isDark else 204
        brush = QBrush(QColor(bg, bg, bg))
        painter.setPen(Qt.NoPen)

        if not self._isEnter:
            painter.setBrush(brush)
            painter.drawRoundedRect(self.rect(), 4, 4)
        else:
            painter.setPen(QPen(QColor(bg, bg, bg), 2))
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
            painter.setPen(Qt.NoPen)
            if not self._isPressed:
                bg = 24 if isDark else 230
                brush.setColor(QColor(bg, bg, bg))
                painter.setBrush(brush)
                painter.drawRect(2, 2, self.width() - 4, self.height() - 4)
            else:
                bg = 102 if isDark else 230
                brush.setColor(QColor(153, 153, 153))
                painter.setBrush(brush)
                painter.drawRoundedRect(
                    5, 1, self.width() - 10, self.height() - 2, 2, 2
                )


class FolderCard(ClickableWindow):
    """Folder card"""

    folder_tile_clicked = Signal(str)

    def __init__(self, session_name: str, folderPath: str, session_id: str = None, parent=None):
        super().__init__(parent)
        self.folder_path = folderPath
        self.session_name = session_name
        self.session_id = session_id
        self.folderName = os.path.basename(folderPath)
        self.clicked.connect(self.on_folder_tile_clicked)
        c = getIconColor()
        self.__closeIcon = QPixmap(
            f":/qfluentwidgets/images/folder_list_dialog/Close_{c}.png"
        ).scaled(12, 12, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        """paint card"""
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
            | QPainter.Antialiasing
        )

        # paint text and icon
        color = Qt.white if isDarkTheme() else Qt.black
        painter.setPen(color)
        if self._isPressed:
            self.__drawText(painter, 12, 12, 12, 10)
            painter.drawPixmap(self.width() - 26, 18, self.__closeIcon)
        else:
            self.__drawText(painter, 10, 13, 10, 11)
            painter.drawPixmap(self.width() - 24, 20, self.__closeIcon)

    def on_folder_tile_clicked(self):
        self.folder_tile_clicked.emit(self.session_id)

    def __drawText(self, painter, x1, fontSize1, x2, fontSize2):
        """draw text"""
        # paint folder name
        font = QFont("Microsoft YaHei")
        font.setBold(True)
        font.setPixelSize(fontSize1)
        painter.setFont(font)
        name = QFontMetrics(font).elidedText(
            self.session_name, Qt.ElideRight, self.width() - 48
        )
        painter.drawText(x1, 30, name)

        # paint folder path
        font = QFont("Microsoft YaHei")
        font.setPixelSize(fontSize2)
        painter.setFont(font)
        path = QFontMetrics(font).elidedText(
            self.folder_path, Qt.ElideRight, self.width() - 24
        )
        painter.drawText(x2, 37, self.width() - 16, 18, Qt.AlignLeft, path)

    def get_folder_path(self):
        return self.folder_path

    def get_session_name(self):
        return self.session_name

    def set_session_id(self, session_id):
        self.session_id = session_id


class AddFolderCard(ClickableWindow):
    """Add folder card"""

    def __init__(self, parent=None):
        super().__init__(parent)
        c = getIconColor()
        self.__iconPix = QPixmap(
            f":/qfluentwidgets/images/folder_list_dialog/Add_{c}.png"
        ).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        """paint card"""
        super().paintEvent(e)
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        pw = self.__iconPix.width()
        ph = self.__iconPix.height()
        if not self._isPressed:
            painter.drawPixmap(int(w / 2 - pw / 2), int(h / 2 - ph / 2), self.__iconPix)
        else:
            painter.drawPixmap(
                int(w / 2 - (pw - 4) / 2),
                int(h / 2 - (ph - 4) / 2),
                pw - 4,
                ph - 4,
                self.__iconPix,
                )


class FolderListDialog(MaskDialogBase):
    """Folder list dialog box"""

    folderChanged = Signal(list)
    session_created = Signal(FolderCard)
    session_chosen = Signal(str)

    def __init__(self, folderPaths: list, title: str, content: str, sessions_data: tuple, parent):
        super().__init__(parent=parent)
        self.title = title
        self.content = content

        self.__originalPaths = folderPaths
        self.folder_paths = folderPaths.copy()

        self.vBoxLayout = QVBoxLayout(self.widget)
        self.titleLabel = QLabel(title, self.widget)
        self.contentLabel = QLabel(content, self.widget)
        self.scrollArea = SingleDirectionScrollArea(self.widget)
        self.scrollWidget = QWidget(self.scrollArea)
        self.completeButton = QPushButton(self.tr("Done"), self.widget)
        self.addFolderCard = AddFolderCard(self.scrollWidget)

        # Create folder cards
        self.folder_cards = [FolderCard(session_name, images_directory, session_id, self.scrollWidget)
                             for (session_name, images_directory, session_id) in sessions_data]
        self.__initWidget()

    def __initWidget(self):
        """initialize widgets"""
        self.__setQss()

        w = max(
            self.titleLabel.width() + 48,
            self.contentLabel.width() + 48,
            352,
            )
        self.widget.setFixedWidth(w)
        self.scrollArea.resize(294, 72)
        self.scrollWidget.resize(292, 72)
        self.scrollArea.setFixedWidth(294)
        self.scrollWidget.setFixedWidth(292)
        self.scrollArea.setMaximumHeight(400)
        self.scrollArea.setViewportMargins(0, 0, 0, 0)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.hScrollBar.setForceHidden(True)
        self.__initLayout()

        # connect signal to slot
        self.addFolderCard.clicked.connect(self.openCreateSessionDialog)
        self.completeButton.clicked.connect(self.__onButtonClicked)
        for card in self.folder_cards:
            card.folder_tile_clicked.connect(self.on_folder_card_clicked)

    def on_folder_card_clicked(self, session_id):
        """Handle the selection of a folder card."""
        print(f"Selected Session with ID: ({session_id})")
        self.session_chosen.emit(session_id)
        self.close()  # Close the dialog

    def openCreateSessionDialog(self):
        """Open a custom dialog to input the new session name and select an image folder."""
        dialog = CreateSessionDialog(self)
        dialog.accepted.connect(lambda: self.createNewSession(dialog))
        dialog.exec()

    def createNewSession(self, dialog: CreateSessionDialog):
        """Creates a new session folder card."""
        session_name = dialog.sessionNameLineEdit.text().strip()
        folder_path = dialog.selectedFolderPath
        if session_name and folder_path:
            session_names = [card.get_session_name() for card in self.folder_cards]
            if session_name in session_names:
                return

            card = FolderCard(session_name, folder_path, None, self.scrollWidget)
            self.scrollLayout.addWidget(card, 0, Qt.AlignTop)
            card.folder_tile_clicked.connect(self.on_folder_card_clicked)
            card.show()

            self.folder_paths.append(folder_path)
            self.folder_cards.append(card)

            self.__adjustWidgetSize()

            self.session_created.emit(card)
        else:
            print("Error creating session.")

    def __initLayout(self):
        """initialize layout"""
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)

        # labels
        layout_1 = QVBoxLayout()
        layout_1.setContentsMargins(0, 0, 0, 0)
        layout_1.setSpacing(6)
        layout_1.addWidget(self.titleLabel, 0, Qt.AlignTop)
        layout_1.addWidget(self.contentLabel, 0, Qt.AlignTop)
        self.vBoxLayout.addLayout(layout_1, 0)
        self.vBoxLayout.addSpacing(12)

        # cards
        layout_2 = QHBoxLayout()
        layout_2.setAlignment(Qt.AlignCenter)
        layout_2.setContentsMargins(4, 0, 4, 0)
        layout_2.addWidget(self.scrollArea, 0, Qt.AlignCenter)
        self.vBoxLayout.addLayout(layout_2, 1)
        self.vBoxLayout.addSpacing(24)

        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(8)
        self.scrollLayout.addWidget(self.addFolderCard, 0, Qt.AlignTop)
        for card in self.folder_cards:
            self.scrollLayout.addWidget(card, 0, Qt.AlignTop)

        # buttons
        layout_3 = QHBoxLayout()
        layout_3.setContentsMargins(0, 0, 0, 0)
        # layout_3.addStretch(1)
        layout_3.addWidget(self.completeButton, 0, Qt.AlignCenter)
        self.vBoxLayout.addLayout(layout_3, 0)

        self.__adjustWidgetSize()

    def deleteFolderCard(self, folderCard):
        """delete selected folder card"""
        self.scrollLayout.removeWidget(folderCard)
        index = self.folder_cards.index(folderCard)
        self.folder_cards.pop(index)
        self.folder_paths.pop(index)
        folderCard.deleteLater()

        # adjust height
        self.__adjustWidgetSize()

    def get_folder_cards(self):
        return self.folder_cards

    def __setQss(self):
        """set style sheet"""
        self.titleLabel.setObjectName("titleLabel")
        self.contentLabel.setObjectName("contentLabel")
        self.completeButton.setObjectName("completeButton")
        self.scrollWidget.setObjectName("scrollWidget")

        FluentStyleSheet.FOLDER_LIST_DIALOG.apply(self)
        self.setStyle(QApplication.style())

        self.titleLabel.adjustSize()
        self.contentLabel.adjustSize()
        self.completeButton.adjustSize()

    def __onButtonClicked(self):
        """done button clicked slot"""
        if sorted(self.__originalPaths) != sorted(self.folder_paths):
            self.setEnabled(False)
            QApplication.processEvents()
            self.folderChanged.emit(self.folder_paths)
        self.close()

    def __adjustWidgetSize(self):
        N = len(self.folder_cards)
        h = 72 * (N + 1) + 8 * N
        self.scrollArea.setFixedHeight(min(h, 400))


