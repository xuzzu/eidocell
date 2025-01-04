# coding:utf-8
import logging
import sys

from PySide6.QtCore import Qt, Signal, QEasingCurve
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QApplication, QFrame, QWidget
from UI.dialogs.export_dialog import ExportDialog
from UI.dialogs.settings_dialog import SettingsDialog
from backend.backend_initializer import BackendInitializer
from backend.config import DARK_THEME_QSS_PATH, LIGHT_THEME_QSS_PATH, WINDOW_WIDTH, WINDOW_HEIGHT, APP_ICON_PATH
from qfluentwidgets import FluentIcon as FIF, Flyout, InfoBarIcon, InfoBarPosition, InfoBar
from qfluentwidgets import (NavigationBar, NavigationItemPosition, isDarkTheme, PopUpAniStackedWidget)
from qframelesswindow import FramelessWindow, TitleBar

from navigation_interface.sessions.sessions_widget import FolderListDialog
from navigation_interface.workspace.workspace_widget import WorkspaceWidget


class Widget(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class StackedWidget(QFrame):
    """ Stacked widget """

    currentChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.view = PopUpAniStackedWidget(self)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.view)

        self.view.currentChanged.connect(self.currentChanged)

    def addWidget(self, widget):
        """ add widget to view """
        self.view.addWidget(widget)

    def widget(self, index: int):
        return self.view.widget(index)

    def setCurrentWidget(self, widget, popOut=False):
        if not popOut:
            self.view.setCurrentWidget(widget, duration=300)
        else:
            self.view.setCurrentWidget(
                widget, True, False, 200, QEasingCurve.InQuad)

    def setCurrentIndex(self, index, popOut=False):
        self.setCurrentWidget(self.view.widget(index), popOut)


class CustomTitleBar(TitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)

        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertSpacing(0, 20)
        self.hBoxLayout.insertWidget(
            1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setAlignment(Qt.AlignTop)
        self.buttonLayout.addWidget(self.minBtn)
        self.buttonLayout.addWidget(self.maxBtn)
        self.buttonLayout.addWidget(self.closeBtn)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addStretch(1)
        self.hBoxLayout.addLayout(self.vBoxLayout, 0)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))


class Window(FramelessWindow):
    def __init__(self):
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))

        # use dark theme mode
        # setTheme(Theme.DARK)

        # change the theme color
        # setThemeColor('#0078d4')

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationBar = NavigationBar(self)
        self.stackWidget = StackedWidget(self)

        # create sub interface
        self.mainInterface = WorkspaceWidget(self)

        # initialize layout
        self.initLayout()

        # add items to navigation interface
        self.initNavigation()

        # initialize backend
        self.backend = BackendInitializer(workspace=self.mainInterface)

        # initialize window
        self.initWindow()

    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        self.hBoxLayout.addWidget(self.navigationBar)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

    def initNavigation(self):
        self.addSubInterface(self.mainInterface, FIF.TILES, 'Workspace')
        # self.addSubInterface(self.sessionInterface, FIF.FOLDER, 'Sessions')
        self.navigationBar.addItem(
            routeKey="Sessions",
            icon=FIF.FOLDER,
            text="Sessions",
            onClick=self.openSessionsDialog,
            selectable=False,
        )
        self.navigationBar.addItem(
            routeKey="Save",
            icon=FIF.SAVE,
            text="Save",
            onClick=self.performSave,
            selectable=False,
        )
        self.navigationBar.addItem(
            routeKey="Export",
            icon=FIF.IMAGE_EXPORT,
            text="Export",
            onClick=self.openExportDialog,
            selectable=False,
        )
        self.navigationBar.addItem(
            routeKey="Settings",
            icon=FIF.SETTING,
            text="Settings",
            onClick=self.openSettingsDialog,
            selectable=False,
        )

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.navigationBar.setCurrentItem(self.mainInterface.objectName())

        # hide the text of button when selected
        # self.navigationBar.setSelectedTextVisible(False)

        # adjust the font size of button
        # self.navigationBar.setFont(getFont(12))

    def initWindow(self):
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.setWindowTitle('BioSort')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        self.setQss()

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP, selectedIcon=None):
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationBar.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            selectedIcon=selectedIcon,
            position=position,
        )

    def setQss(self):
        color = DARK_THEME_QSS_PATH if isDarkTheme() else LIGHT_THEME_QSS_PATH
        with open(color, encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationBar.setCurrentItem(widget.objectName())

    def openSessionsDialog(self):
        """Open a dialog to select session folders."""

        # Replace get_all_sessions with list_sessions
        existing_sessions = self.backend.session_manager.list_sessions()
        sessions_data = tuple([(session.name, session.images_directory, session.id) for session in existing_sessions])

        # Replace get_sessions_paths with list comprehension
        initial_paths = [session.session_folder for session in existing_sessions]

        title = 'Select Session'
        content = "Choose existing session or create a new one"
        dialog = FolderListDialog(initial_paths, title, content, sessions_data, self)
        self.backend.init_sessions_presenter(dialog)
        dialog.folderChanged.connect(self.handleSessionsFolderSelected)
        dialog.exec()

    def openSettingsDialog(self):
        dialog = SettingsDialog(self)
        dialog.accepted.connect(self.backend.apply_settings)
        dialog.exec()

    def performSave(self):
        if not self.backend.session or not self.backend:
            print("Error: No session selected.")
            return

        try:
            # Replace save_sessions with save_session
            self.backend.session_manager.save_session(self.backend.session)
            Flyout.create(
                icon=InfoBarIcon.SUCCESS,
                title='Session Saved',
                content="Session data saved successfully.",
                target=self.navigationBar,
                parent=self,
                isClosable=True
            )
        except Exception as e:
            print(f"Error during save: {e}")
            Flyout.create(
                icon=InfoBarIcon.ERROR,
                title='Session Save Failed',
                content="Session data was not saved due to some error.",
                target=self.navigationBar,
                parent=self,
                isClosable=True
            )

    def handleSessionsFolderSelected(self, folder_paths):
        """Process the selected folder paths."""
        print(f"Selected folder paths: {folder_paths}")

    def openExportDialog(self):
        """Opens the export data dialog."""
        if not self.backend.session or not self.backend:
            print("Error: No session selected.")
            return

        dialog = ExportDialog(self)
        dialog.exec()
        dialog.accepted.connect(self.export_session_data(dialog))

    def export_session_data(self, dialog):
        """Exports session data to the selected folder."""
        logging.info("Export session data triggered.")
        export_folder_path = dialog.folderPathLabel.text()
        include_masks = dialog.includeMasksCheckBox.isChecked()
        include_clusters = dialog.includeClustersCheckBox.isChecked()
        include_params = dialog.includeCalculatedParamsCheckBox.isChecked()
        include_charts = dialog.includeChartsCheckBox.isChecked()

        if export_folder_path == "No folder selected":
            print("Error: No export folder selected.")
            return

        params = {
            "include_masks": include_masks,
            "include_clusters": include_clusters,
            "include_params": include_params,
            "include_charts": include_charts,
            "export_folder_path": export_folder_path
        }

        try:
            self.backend.data_manager.export_data(params)
            print(f"Session data exported to: {export_folder_path}")
            Flyout.create(
                icon=InfoBarIcon.SUCCESS,
                title='Export Successful',
                content=f"Session data exported to: {export_folder_path}",
                target=self.navigationBar,
                parent=self,
                isClosable=True
            )
        except Exception as e:
            print(f"Error during export: {e}")
            InfoBar.error(
                title='Export Error',
                content=f"An error '{e}' occurred during export. Please try again with different settings or report the issue.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=-1,    # won't disappear automatically
                parent=self
            )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()

    w.show()
    app.exec()
