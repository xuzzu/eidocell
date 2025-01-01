from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSpacerItem, QSizePolicy, QLabel, QComboBox,
    QGroupBox, QFrame, QGraphicsDropShadowEffect
)
from qfluentwidgets import Slider, PrimaryPushButton, setCustomStyleSheet, ComboBox

from backend.config import CLUSTERING_N_ITER, CLUSTERING_DEFAULT_N_CLUSTERS, MODELS
from qfluentwidgets import (SubtitleLabel, PushButton, isDarkTheme)


class ControlPanel(QWidget):
    """Control panel for adjusting clustering parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent

        # Main Frame with Slightly Rounded Corners and Subtle Shadow
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("controlPanelFrame")
        self.main_frame.setStyleSheet("""
            QFrame#controlPanelFrame {
                background-color: #ffffff;
                border-radius: 10px;
            }
        """)

        # Apply Subtle Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)  # Reduced blur radius for lighter shadow
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 30))  # Less opaque shadow
        self.main_frame.setGraphicsEffect(shadow)

        # Layout for the main frame
        self.vBoxLayout = QVBoxLayout(self.main_frame)
        self.vBoxLayout.setContentsMargins(15, 15, 15, 15)
        self.vBoxLayout.setSpacing(10)

        # Clustering Label
        self.clustering_label = QLabel("Clustering", self.main_frame)
        self.clustering_label.setAlignment(Qt.AlignCenter)
        self.clustering_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #333333;
            }
        """)

        # Clustering Method Selector
        self.clustering_method_selector = ComboBox(self.main_frame)
        self.clustering_method_selector.addItems([
            "K-means", "Deep Clustering", "Connected Components"
        ])
        self.clustering_method_selector.setFixedHeight(30)
        self.clustering_method_selector.setStyleSheet("""
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #cccccc;
                border-left-style: solid;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down_arrow.png); /* Replace with your arrow icon path */
            }
        """)

        # K-means Parameters GroupBox
        self.kmeans_params_group = QGroupBox("K-means Parameters", self.main_frame)
        self.kmeans_params_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: normal; /* Removed bold font weight */
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        kmeans_layout = QVBoxLayout(self.kmeans_params_group)
        kmeans_layout.setContentsMargins(15, 15, 15, 15)
        kmeans_layout.setSpacing(8)

        # Iterations Slider and Label
        self.iterationsLabel = QLabel(f"Iterations: {CLUSTERING_N_ITER}", self.kmeans_params_group)
        self.iterationsLabel.setFont(QFont("Arial", 11))  # Refined font size
        self.iterationsLabel.setStyleSheet("color: #555555;")
        self.iterationsSlider = Slider(Qt.Horizontal, self.kmeans_params_group)
        self.iterationsSlider.setRange(50, 1000)
        self.iterationsSlider.setValue(CLUSTERING_N_ITER)
        self.iterationsSlider.setSingleStep(50)
        self.iterationsSlider.setFixedHeight(18)
        self.iterationsSlider.setStyleSheet("""
            QSlider::handle:horizontal {
                background-color: #0078d4;
                border: 1px solid #5c5c5c;
                width: 14px;
                height: 14px;
                margin: -6px 0;
                border-radius: 7px;
            }
            QSlider::groove:horizontal {
                background-color: #e0e0e0;
                height: 3px;
                border-radius: 1.5px;
            }
            QSlider::sub-page:horizontal {
                background-color: #0078d4;
                height: 3px;
                border-radius: 1.5px;
            }
            QSlider::add-page:horizontal {
                background-color: #e0e0e0;
                height: 3px;
                border-radius: 1.5px;
            }
            QSlider::tick-mark {
                background-color: #000000;
                width: 2px;
                height: 3px;
            }
        """)
        self.iterationsSlider.valueChanged.connect(
            lambda value: self.iterationsLabel.setText(f"Iterations: {value}")
        )

        # Clusters Slider and Label
        self.clustersLabel = QLabel(f"Clusters: {CLUSTERING_DEFAULT_N_CLUSTERS}", self.kmeans_params_group)
        self.clustersLabel.setFont(QFont("Arial", 11))  # Refined font size
        self.clustersLabel.setStyleSheet("color: #555555;")
        self.clustersSlider = Slider(Qt.Horizontal, self.kmeans_params_group)
        self.clustersSlider.setRange(2, 100)
        self.clustersSlider.setValue(CLUSTERING_DEFAULT_N_CLUSTERS)
        self.clustersSlider.setFixedHeight(18)
        self.clustersSlider.setStyleSheet("""
            QSlider::handle:horizontal {
                background-color: #0078d4;
                border: 1px solid #5c5c5c;
                width: 14px;
                height: 14px;
                margin: -6px 0;
                border-radius: 7px;
            }
            QSlider::groove:horizontal {
                background-color: #e0e0e0;
                height: 3px;
                border-radius: 1.5px;
            }
            QSlider::sub-page:horizontal {
                background-color: #0078d4;
                height: 3px;
                border-radius: 1.5px;
            }
            QSlider::add-page:horizontal {
                background-color: #e0e0e0;
                height: 3px;
                border-radius: 1.5px;
            }
            QSlider::tick-mark {
                background-color: #000000;
                width: 2px;
                height: 3px;
            }
        """)
        self.clustersSlider.valueChanged.connect(
            lambda value: self.clustersLabel.setText(f"Clusters: {value}")
        )

        # Feature Extractor Model Selector
        self.model_label = QLabel("Feature Extractor Model:", self.kmeans_params_group)
        self.model_label.setStyleSheet("color: #555555;")
        self.kmeans_model_selector = ComboBox(self.kmeans_params_group)
        self.kmeans_model_selector.setFixedHeight(28)
        self.kmeans_model_selector.setStyleSheet("""
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #cccccc;
                border-left-style: solid;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down_arrow.png); /* Replace with your arrow icon path */
            }
        """)

        # Populate K-means model selector
        for model_name in MODELS:
            self.kmeans_model_selector.addItem(model_name)

        # Load default model from parent settings, if available
        if self.parent_widget and hasattr(self.parent_widget, 'main_window'):
            settings = self.parent_widget.main_window.backend.settings
            self.kmeans_model_selector.setCurrentText(settings.get("model", MODELS[0]))

        # Add widgets to K-means layout
        kmeans_layout.addWidget(self.iterationsLabel, alignment=Qt.AlignHCenter)
        kmeans_layout.addWidget(self.iterationsSlider)
        kmeans_layout.addWidget(self.clustersLabel, alignment=Qt.AlignHCenter)
        kmeans_layout.addWidget(self.clustersSlider)
        kmeans_layout.addWidget(self.model_label, alignment=Qt.AlignLeft)
        kmeans_layout.addWidget(self.kmeans_model_selector)

        # Buttons
        self.startButton = PrimaryPushButton("Start Analysis", self.main_frame)
        self.resetButton = PrimaryPushButton("Reset Analysis", self.main_frame)
        self.startButton.setFixedHeight(35)
        self.resetButton.setFixedHeight(35)

        # Style Buttons
        self.startButton.setStyleSheet("""
            QPushButton {
                background-color: #009faa;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #14939c;
            }
        """)
        self.resetButton.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #333333;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c0c0c0;
            }
        """)

        # Spacer for layout
        self.spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add widgets to the main layout
        self.vBoxLayout.addWidget(self.clustering_label)
        self.vBoxLayout.addWidget(self.clustering_method_selector)
        self.vBoxLayout.addWidget(self.kmeans_params_group)
        self.vBoxLayout.addSpacerItem(self.spacer)
        self.vBoxLayout.addWidget(self.startButton)
        self.vBoxLayout.addWidget(self.resetButton)

        # Clustering method change handler
        self.clustering_method_selector.currentIndexChanged.connect(self.update_parameter_visibility)

        # Button connections
        self.startButton.clicked.connect(self.startAnalysis)
        self.resetButton.clicked.connect(self.resetAnalysis)

        # Set the main layout to include the frame
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.main_frame)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)

        # Set own width
        self.setFixedWidth(280)

    def update_parameter_visibility(self, index):
        """Show or hide parameter controls based on selected clustering method."""
        method = self.clustering_method_selector.itemText(index)
        self.kmeans_params_group.setVisible(method == "K-means")

    def startAnalysis(self):
        """Placeholder function for starting the analysis."""
        print("Start Analysis button clicked!")

    def resetAnalysis(self):
        """Placeholder function for resetting the analysis."""
        print("Reset Analysis button clicked!")
