from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFileDialog
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import PushButton, LineEdit, MessageBoxBase, SubtitleLabel


class CreateSessionDialog(MessageBoxBase):
    """Custom dialog to input the new session name and select an image folder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Enter Session Name", self)
        self.sessionNameLineEdit = LineEdit(self)
        self.sessionNameLineEdit.setFixedWidth(270)
        self.selectedFolderPath = ""  # To store the selected path
        self.folderPathLabel = QLabel("No folder selected", self)
        self.folderPathLabel.setFixedWidth(270)
        self.chooseFolderButton = PushButton(FIF.FOLDER, 'Choose images folder', self)
        self.chooseFolderButton.setFixedWidth(230)

        self.sessionNameLineEdit.setPlaceholderText("e.g., Experiment 1")
        self.sessionNameLineEdit.setClearButtonEnabled(True)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.sessionNameLineEdit)
        self.viewLayout.addWidget(self.folderPathLabel)
        self.viewLayout.addWidget(self.chooseFolderButton, alignment=Qt.AlignCenter)

        self.yesButton.setText("Create")
        self.cancelButton.setText("Cancel")

        self.widget.setMinimumWidth(350)

        # Connect the button to the folder picker
        self.chooseFolderButton.clicked.connect(self.select_image_folder)

        # Connect the buttons to the slots
        self.yesButton.clicked.connect(self.on_class_creation_button_clicked)

    def on_class_creation_button_clicked(self):
        """Handles the creation of a new class."""
        session_name = self.sessionNameLineEdit.text().strip()
        print(f"Session name: {session_name}")

    def selectImageFolder(self):
        """Open a folder dialog to choose the image folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder", "", QFileDialog.ShowDirsOnly)

        if folder_path:
            self.selectedFolderPath = folder_path
            self.folderPathLabel.setText(folder_path)

    def select_image_folder(self):
        """Open a folder dialog to choose the image folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Image Folder", "", QFileDialog.ShowDirsOnly
        )

        if folder_path:
            self.selectedFolderPath = folder_path
            self.folderPathLabel.setText(folder_path)
