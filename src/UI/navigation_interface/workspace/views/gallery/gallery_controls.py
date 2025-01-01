from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QLabel,
    QFrame, QGraphicsDropShadowEffect
)
from qfluentwidgets import FluentIcon as FIF, Slider, ComboBox, TogglePushButton, ToggleToolButton


class GalleryControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gallery_presenter = None

        # Main Frame with Slightly Rounded Corners and Subtle Shadow
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("galleryControlsFrame")
        self.main_frame.setStyleSheet("""
            QFrame#galleryControlsFrame {
                background-color: #ffffff;
                border-radius: 10px;
            }
        """)

        # Apply Subtle Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)  # Adjusted blur radius for subtlety
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 20))  # More transparent shadow
        self.main_frame.setGraphicsEffect(shadow)

        # Layout for the main frame
        main_layout = QHBoxLayout(self.main_frame)
        main_layout.setContentsMargins(10, 15, 10, 15)  # Increased top and bottom margins
        main_layout.setSpacing(40)  # Increased spacing between sections

        # ================== Left Section: Scale Label and Slider ==================
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        self.scaleLabel = QLabel("Scale", self.main_frame)
        self.scaleLabel.setStyleSheet("font-size: 14pt;")
        self.scaleLabel.setAlignment(Qt.AlignCenter)

        self.scale_slider = Slider(Qt.Horizontal, self.main_frame)
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setValue(100)
        self.scale_slider.setFixedWidth(270)  # Set a reasonable minimum width
        self.scale_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        left_layout.addWidget(self.scaleLabel, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.scale_slider, alignment=Qt.AlignCenter)
        
        left_layout.setSpacing(10)

        # ================== Middle Section: Sorting Label and Controls ==================
        middle_layout = QVBoxLayout()
        middle_layout.setAlignment(Qt.AlignTop)

        self.sortOrderLabel = QLabel("Sorting parameters", self.main_frame)
        self.sortOrderLabel.setStyleSheet("font-size: 14pt;")
        self.sortOrderLabel.setAlignment(Qt.AlignCenter)

        sort_controls_layout = QHBoxLayout()
        sort_controls_layout.setSpacing(10)

        self.sortAscButton = ToggleToolButton(FIF.UP, self.main_frame)
        self.sortAscButton.setToolTip("Sort Ascending")
        self.sortDescButton = ToggleToolButton(FIF.DOWN, self.main_frame)
        self.sortDescButton.setToolTip("Sort Descending")
        self.parameterComboBox = ComboBox(self.main_frame)
        self.parameterComboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.parameterComboBox.setFixedWidth(200)  # Set a reasonable fixed width

        sort_controls_layout.addWidget(self.sortAscButton, alignment=Qt.AlignVCenter)
        sort_controls_layout.addWidget(self.sortDescButton, alignment=Qt.AlignVCenter)
        sort_controls_layout.addWidget(self.parameterComboBox, alignment=Qt.AlignVCenter)

        middle_layout.addWidget(self.sortOrderLabel, alignment=Qt.AlignCenter)
        middle_layout.addLayout(sort_controls_layout)

        # Populate sorting parameters
        self.parameterComboBox.addItems(
            [
                "Area",
                "Perimeter",
                "Eccentricity",
                "Solidity",
                "Aspect Ratio",
                "Circularity",
                "Major Axis Length",
                "Minor Axis Length",
                "Mean Intensity",
                "Compactness",
                "Convexity",
                "Curl",
                "Volume"
            ]
        )

        middle_layout.setSpacing(10)

        # ================== Right Section: Mask Toggle Button ==================
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)

        self.mask_toggle = TogglePushButton(FIF.VIEW, 'Mask view', self.main_frame)
        self.mask_toggle.setFixedWidth(140)  # Keeping fixed width as per design
        self.mask_toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Use spacer to push the button to the top if needed
        right_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        right_layout.addWidget(self.mask_toggle, alignment=Qt.AlignCenter)

        # ================== Add Sections to Main Layout ==================
        main_layout.addLayout(left_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(right_layout)

        # ================== Connect Signals ==================
        self.scale_slider.valueChanged.connect(lambda value: print(f"Scale: {value}"))

        # ================== Set the Main Layout ==================
        outer_layout = QHBoxLayout(self)
        outer_layout.addWidget(self.main_frame)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(outer_layout)

        # self.main_frame.setFixedHeight(120)  # Set fixed height for the main frame

