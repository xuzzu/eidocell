from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from qfluentwidgets import MessageBoxBase, SegmentedWidget, SubtitleLabel, Slider
from qfluentwidgets import ComboBox
from backend.config import MODELS, DEFAULT_SETTINGS, load_settings, save_settings


class SettingsDialog(MessageBoxBase):
    """Dialog for configuring application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")

        # Load settings
        self.settings = load_settings()

        self.titleLabel = SubtitleLabel("General Settings", self)
        self.themeSelector = SegmentedWidget(self)
        self.themeSelector.setFixedHeight(30)
        self.modelLabel = QLabel("Feature extractor model:", self)
        self.modelLabel.setStyleSheet("font-size: 12pt")
        self.modelComboBox = ComboBox(self)
        self.providerLabel = QLabel("ONNX execution provider:", self)
        self.providerLabel.setStyleSheet("font-size: 12pt")
        self.providerComboBox = ComboBox(self)

        # Thumbnail Quality Settings (with value label)
        self.thumbnailQualityLabel = QLabel("Thumbnail quality:", self)
        self.thumbnailQualityLabel.setStyleSheet("font-size: 12pt")
        self.thumbnailQualitySlider = Slider(Qt.Horizontal, self)
        self.thumbnailQualitySlider.setRange(1, 100)
        self.thumbnailQualityValueLabel = QLabel(str(self.settings["thumbnail_quality"]), self)
        self.thumbnailQualitySlider.setValue(self.settings["thumbnail_quality"])

        # Collage Images Settings (with value label)
        self.collageImagesLabel = QLabel("Images per collage:", self)
        self.collageImagesLabel.setStyleSheet("font-size: 12pt")
        self.collageImagesSlider = Slider(Qt.Horizontal, self)
        self.collageImagesSlider.setRange(1, 25)
        self.collageImagesValueLabel = QLabel(str(self.settings["images_per_collage"]), self)
        self.collageImagesSlider.setValue(self.settings["images_per_collage"])

        self.__initWidget()

    def __initWidget(self):
        """Initialize the layout and widgets within the dialog."""
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.themeSelector)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.modelLabel)
        self.viewLayout.addWidget(self.modelComboBox)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.providerLabel)
        self.viewLayout.addWidget(self.providerComboBox)
        self.viewLayout.addSpacing(10)

        # Thumbnail Quality Layout
        thumbnailQualityLayout = QHBoxLayout()
        thumbnailQualityLayout.addWidget(self.thumbnailQualityLabel)
        thumbnailQualityLayout.addWidget(self.thumbnailQualitySlider)
        thumbnailQualityLayout.addWidget(self.thumbnailQualityValueLabel)
        self.viewLayout.addLayout(thumbnailQualityLayout)
        self.viewLayout.addSpacing(10)

        # Collage Images Layout
        collageImagesLayout = QHBoxLayout()
        collageImagesLayout.addWidget(self.collageImagesLabel)
        collageImagesLayout.addWidget(self.collageImagesSlider)
        collageImagesLayout.addWidget(self.collageImagesValueLabel)
        self.viewLayout.addLayout(collageImagesLayout)
        self.viewLayout.addSpacing(10)

        self.yesButton.setText("Apply")
        self.cancelButton.setText("Cancel")
        self.widget.setMinimumWidth(400)

        # Add theme options
        self.themeSelector.addItem(routeKey='light', text='Light')
        self.themeSelector.addItem(routeKey='dark', text='Dark')
        self.themeSelector.setCurrentItem(self.settings["theme"])  # Load saved theme

        # Add model options
        for model_name in MODELS.keys():
            self.modelComboBox.addItem(model_name)
        self.modelComboBox.setCurrentText(self.settings["model"])  # Load saved model

        # Add provider options
        self.providerComboBox.addItem("CPUExecutionProvider")
        self.providerComboBox.addItem("CUDAExecutionProvider")  # Add if CUDA is available
        self.providerComboBox.setCurrentText(self.settings["provider"])  # Load saved provider

        # Connect slider value changed signals to update labels
        self.thumbnailQualitySlider.valueChanged.connect(
            lambda value: self.thumbnailQualityValueLabel.setText(str(value))
        )
        self.collageImagesSlider.valueChanged.connect(
            lambda value: self.collageImagesValueLabel.setText(str(value))
        )

    def accept(self):
        """Save settings when the dialog is accepted."""
        self.settings["theme"] = self.themeSelector.currentRouteKey()
        self.settings["model"] = self.modelComboBox.currentText()
        self.settings["provider"] = self.providerComboBox.currentText()
        self.settings["thumbnail_quality"] = self.thumbnailQualitySlider.value()
        self.settings["images_per_collage"] = self.collageImagesSlider.value()

        save_settings(self.settings)
        super().accept()  # Call the base class accept method