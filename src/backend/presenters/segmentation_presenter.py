### backend/presenters/clusters_presenter.py
import random

import logging
import numpy as np

import os
from PySide6.QtCore import QEvent, Qt, Signal, QObject, Slot, QTimer
from qfluentwidgets import InfoBarPosition, InfoBar, InfoBarIcon

from UI.dialogs.progress_infobar import ProgressInfoBar
from UI.navigation_interface.workspace.views.clusters.clusters_controls import ControlPanel
from UI.navigation_interface.workspace.views.segmentation.segmentation_view_widget import SegmentationViewWidget
from backend.config import COLLAGE_RES_SCALE, IMAGES_PER_PREVIEW
from backend.data_manager import DataManager
from backend.helpers.context_menu_handler import ContextMenuHandler
from backend.helpers.segmentation_thread import SegmentationThread
from backend.segmentation import SegmentationModel
from PySide6.QtWidgets import QApplication

class SegmentationPresenter(QObject):
    """Presenter for managing clusters and their display in the ClustersViewWidget."""
    class_updated = Signal(str)
    segmentation_completed = Signal()

    def __init__(self,
                 segmentation_view_widget: SegmentationViewWidget,
                 data_manager: DataManager,
                 segmentation_model: SegmentationModel):
        super().__init__()
        self.segmentation_view_widget = segmentation_view_widget
        self.data_manager = data_manager
        self.segmentation_model = segmentation_model
        self.context_menu_handler = ContextMenuHandler(self)
        self.selected_samples = []
        # VERY STUPID SOLUTION TO CRASHING THREADS (FOR NOW)
        self.segmentation_threads = []
        
    def resample_samples(self):
        # get 6 random samples from the dataset
        random_samples = random.choices(list(self.data_manager.samples.keys()), k=8)
        self.selected_samples = random_samples
        self.update_selected_samples(random_samples)

    def update_selected_samples(self, sample_ids: list):
        """Updates the selected samples' masks after any change of parameters was triggered."""
        self.selected_samples = sample_ids
        self.segment_selected(sample_ids)

    def segment_selected(self, image_ids: list):
        """Segments the selected images."""
        method = self.segmentation_view_widget.controls.method_selector.currentText()
        param1 = self.segmentation_view_widget.controls.parameter_slider.value()
        param2 = self.segmentation_view_widget.controls.parameter_slider_2.value()

        self.segmentation_threads.append(SegmentationThread(image_ids,
                                                            self.segmentation_model,
                                                            self.data_manager,
                                                            method=method,
                                                            param1=param1,
                                                            param2=param2))
        self.segmentation_threads[-1].mask_created.connect(self.handle_mask_created)
        self.segmentation_threads[-1].finished.connect(self.selected_segmentation_finished)
        self.segmentation_threads[-1].start()
    
    def selected_segmentation_finished(self):
        """Handles the completion of segmentation."""
        
        # Update previews
        mask_ids = [self.data_manager.samples[sample_id].mask_id for sample_id in self.selected_samples]
        masked_image_paths = [self.data_manager.masks[mask_id].masked_image_path for mask_id in mask_ids]
        
        self.segmentation_view_widget.preview.update_previews(masked_image_paths)
    
    def segment_all(self):
        """Performs image segmentation and updates the analysis view."""
        print("Segmenting all images...")
        print("****************************************")
        self.progress_info_bar = ProgressInfoBar.new(
            icon=InfoBarIcon.INFORMATION,
            title="Segmentation Progress",
            content="Segmenting images...",
            duration=-1,
            parent=self.segmentation_view_widget.main_window_reference
        )

        method = self.segmentation_view_widget.controls.method_selector.currentText()
        param1 = self.segmentation_view_widget.controls.parameter_slider.value()
        param2 = self.segmentation_view_widget.controls.parameter_slider_2.value()

        self.segmentation_threads.append(SegmentationThread(list(self.data_manager.samples.keys()),
                                                      self.segmentation_model,
                                                      self.data_manager,
                                                      method=method,
                                                      param1=param1,
                                                      param2=param2))
        self.segmentation_threads[-1].progress_updated.connect(self.progress_info_bar.set_progress)
        self.segmentation_threads[-1].mask_created.connect(self.handle_mask_created)
        self.segmentation_threads[-1].finished.connect(self.on_segmentation_finished)
        self.segmentation_threads[-1].start()

    def on_segmentation_finished(self):
        """Handles the completion of segmentation."""
        self.progress_info_bar.set_progress(100)
        self.progress_info_bar.set_title('Segmentation Complete')
        self.progress_info_bar.set_content('All images segmented')
        QTimer.singleShot(1000, self.progress_info_bar.customClose)

        print("Segmentation finished.")
        self.segmentation_completed.emit()
        self.data_manager._update_objects_metadata()
        self.data_manager._update_masks_metadata()

    @Slot(str, object, object, str)
    def handle_mask_created(self, image_id, mask, attributes, masked_image_path, masked_image):
        """Handles mask creation in the main thread."""
        mask_obj = self.data_manager.create_mask(image_id, mask, attributes, masked_image_path, masked_image)
        self.data_manager.samples[image_id].set_mask_id(mask_obj.id)
