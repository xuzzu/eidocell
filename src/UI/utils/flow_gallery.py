# flow_widget.py
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QFrame, QGraphicsDropShadowEffect, QVBoxLayout
)
from qfluentwidgets import FlowLayout


class FlowGallery(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set object name for styling
        self.setObjectName("FlowGalleryFrame")

        # Apply rounded corners and a subtle shadow
        self.setStyleSheet("""
            #FlowGalleryFrame {
                background-color: #ffffff;
                border-radius: 10px;
            }
            /* Scrollbar Styles */
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        # Set up the scrolling area inside the frame
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("FlowGalleryScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Apply stylesheet to scroll area to make it transparent (inherits frame's background)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
            }
        """)

        # Create a container widget for the layout
        self.container = QWidget()
        self.container.setObjectName("FlowGalleryContainer")
        self.container.setStyleSheet("""
            #FlowGalleryContainer {
                background-color: transparent;
            }
        """)
        self.scroll_area.setWidget(self.container)

        # Use FlowLayout from Fluent Widgets
        self.flow_layout = FlowLayout(self.container, needAni=False, isTight=False)
        self.flow_layout.setSpacing(10)  # Adjust spacing as needed
        self.flow_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # Center tiles horizontally

        # Layout for the frame
        self.frame_layout = QVBoxLayout(self)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)  # Inner margins
        self.frame_layout.setSpacing(0)
        self.frame_layout.addWidget(self.scroll_area)

        # Set the layout to the frame
        self.setLayout(self.frame_layout)

        # Enable clipping to ensure rounded corners
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def add_item(self, widget):
        """Convenience method to add a widget to the flow layout."""
        self.flow_layout.addWidget(widget)

    def remove_item(self, widget):
        """Convenience method to remove a widget from the flow layout."""
        self.flow_layout.removeWidget(widget)
