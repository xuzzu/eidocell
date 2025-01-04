
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from UI.navigation_interface.workspace.views.segmentation.preview_grid import PreviewGrid
from UI.navigation_interface.workspace.views.segmentation.segmentation_controls import SegmentationControls


class SegmentationViewWidget(QWidget):
    """Main widget for the segmentation interface"""
    def __init__(self, main_window_reference, parent=None):
        super().__init__(parent)
        self.setObjectName("segmentationView")
        self.main_window_reference = main_window_reference

        # Create main components
        self.controls = SegmentationControls()
        self.preview = PreviewGrid()

        # Main vertical layout (to accommodate the title label)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Horizontal layout for controls and preview (scaled)
        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Create wrapper layouts to control vertical alignment
        left_wrapper = QVBoxLayout()
        left_wrapper.addWidget(self.controls)
        left_wrapper.addStretch()  # Pushes controls to the top

        right_wrapper = QVBoxLayout()
        right_wrapper.addWidget(self.preview)
        right_wrapper.addStretch()  # Pushes preview grid to the top

        content_layout.addLayout(left_wrapper)
        content_layout.addLayout(right_wrapper)

        # Put the layout in the center
        main_layout.addLayout(content_layout)

        # Connect signals
        self.controls.method_selector.currentIndexChanged.connect(
            self.controls.update_parameter_settings
        )
        self.controls.method_selector.currentIndexChanged.connect(
            self.update_previews
        )
        self.controls.parameter_slider.valueChanged.connect(
            self.update_previews
        )
        self.controls.parameter_slider_2.valueChanged.connect(
            self.update_previews
        )
        self.controls.resample_button.clicked.connect(
            self.resample_preview_images
        )
        self.controls.apply_button.clicked.connect(
            self.apply_segmentation
        )

        # Initialize
        self.segmentation_presenter = None

    def set_presenter(self, presenter):
        """Set the presenter and initialize the view"""
        self.segmentation_presenter = presenter

    def update_previews(self):
        """Update preview images with current settings"""
        if self.segmentation_presenter:
            # Get the currently selected samples' paths and update previews
            print("Updating previews")
            self.segmentation_presenter.update_selected_samples(self.segmentation_presenter.selected_samples)
    
    def apply_segmentation(self):
        """Apply segmentation to all images"""
        if self.segmentation_presenter:
            self.segmentation_presenter.segment_all()

    def resample_preview_images(self):
        """Resample preview images with new samples"""
        if self.segmentation_presenter:
            self.segmentation_presenter.resample_samples()