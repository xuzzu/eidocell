### backend/presenters/analysis_presenter.py
from PySide6.QtCore import Slot, QTimer, Signal, QObject
from qfluentwidgets import InfoBarIcon

from UI.dialogs.progress_dialog import ProgressDialog
from UI.dialogs.progress_infobar import ProgressInfoBar
from UI.navigation_interface.workspace.views.analysis.analysis_view_widget import AnalysisViewWidget
from backend.data_manager import DataManager
from backend.helpers.segmentation_thread import SegmentationThread
from backend.segmentation import SegmentationModel


class AnalysisPresenter(QObject):
    """Presenter for handling analysis tasks, including segmentation."""
    segmentation_completed = Signal()

    def __init__(self, analysis_view_widget: AnalysisViewWidget, data_manager: DataManager, segmentation_model: SegmentationModel):
        super().__init__()
        self.analysis_view_widget = analysis_view_widget
        self.data_manager = data_manager
        self.segmentation_model = segmentation_model

        # Connect signals
        self.analysis_view_widget.runSegmentationButton.clicked.connect(self.run_segmentation)

    def run_segmentation(self):
        """Performs image segmentation and updates the analysis view."""
        self.progress_info_bar = ProgressInfoBar.new(
            icon=InfoBarIcon.INFORMATION,
            title="Segmentation Progress",
            content="Segmenting images...",
            duration=-1,
            parent=self.analysis_view_widget.main_window_reference
        )

        self.segmentation_thread = SegmentationThread(list(self.data_manager.samples.keys()),
                                                      self.segmentation_model,
                                                      self.data_manager)
        self.segmentation_thread.progress_updated.connect(self.progress_info_bar.set_progress)
        self.segmentation_thread.mask_created.connect(self.handle_mask_created)
        self.segmentation_thread.finished.connect(self.on_segmentation_finished)
        self.segmentation_thread.start()

    def on_segmentation_finished(self):
        """Handles the completion of segmentation."""
        self.progress_info_bar.set_progress(100)
        self.progress_info_bar.set_title('Segmentation Complete')
        self.progress_info_bar.set_content('All images segmented')
        print("Segmentation finished.")
        QTimer.singleShot(1000, self.progress_info_bar.customClose)
        self.segmentation_completed.emit()
        self.data_manager._update_objects_metadata()
        self.data_manager._update_masks_metadata()


    @Slot(str, object, object, str)
    def handle_mask_created(self, image_id, mask, attributes, masked_image_path, masked_image):
        """Handles mask creation in the main thread."""
        mask_obj = self.data_manager.create_mask(image_id, mask, attributes, masked_image_path, masked_image)
        self.data_manager.samples[image_id].set_mask_id(mask_obj.id)
