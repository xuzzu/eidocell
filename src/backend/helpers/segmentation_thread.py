### backend/helpers/segmentation_thread.py
import cv2
import os

from PySide6.QtCore import QThread, Signal
from pyqtgraph import image

from backend.utils.image_utils import combine_image_and_mask


class SegmentationThread(QThread):
    """Thread for running image segmentation in the background."""
    progress_updated = Signal(int)
    mask_created = Signal(str, object, object, object, object)

    def __init__(self, image_ids, segmentation_model, data_manager, method="otsu", param1=None, param2=None):
        super().__init__()
        self.image_ids = image_ids
        self.segmentation_model = segmentation_model
        self.data_manager = data_manager

        self.method = method
        self.param1 = param1
        self.param2 = param2

        # Connect to segmentation progress signal
        self.processed_images = 0

    def run(self):
        """Runs image segmentation for each image ID."""
        
        total_images = len(self.image_ids)

        for image_id in self.image_ids:
            if self.method == "Otsu's Thresholding":
                mask = self.segmentation_model.predict_mask_otsu(self.data_manager.samples[image_id].path, max_distance_ratio=self.param1/100, min_component_size=self.param2) # Use max_distance_ratio
            elif self.method == "Adaptive Thresholding":
                mask = self.segmentation_model.predict_mask_adaptive(self.data_manager.samples[image_id].path, block_size=self.param1, c=self.param2) # Use block_size and C
            elif self.method == "Watershed":
                mask = self.segmentation_model.predict_mask_watershed(self.data_manager.samples[image_id].path, foreground_threshold=self.param1/100, morph_kernel_size=(self.param2, self.param2)) # Use foreground_threshold 
            masked_image = combine_image_and_mask(self.data_manager.samples[image_id].path, mask)
            masked_image_file_name = f"masked_image_{image_id}.png"
            masked_image_file_path = os.path.join(self.data_manager.session.masked_images_directory, masked_image_file_name)
            cv2.imwrite(masked_image_file_path, masked_image)
            attributes = self.segmentation_model.get_object_properties(self.data_manager.samples[image_id].path, mask)

            # Emit mask created signal
            self.mask_created.emit(image_id, mask, attributes, masked_image_file_path, masked_image)
            self.processed_images += 1
            overall_progress = int((self.processed_images / total_images) * 100)
            self.progress_updated.emit(overall_progress)

    def _update_progress(self, image_progress):
        """Updates the overall progress based on individual image segmentation."""
        pass