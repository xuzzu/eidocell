### backend/presenters/clusters_presenter.py
import logging
import numpy as np

import os
from PySide6.QtCore import QEvent, Qt, Signal, QObject, Slot, QTimer
from qfluentwidgets import InfoBarPosition, InfoBar, InfoBarIcon

from UI.dialogs.class_cluster_summary import ClassClusterSummary
from UI.dialogs.class_cluster_view import ClassClusterViewer
from UI.dialogs.custom_info_bar import CustomInfoBar
from UI.dialogs.progress_dialog import ProgressDialog
from UI.dialogs.progress_infobar import ProgressInfoBar
from UI.navigation_interface.workspace.views.clusters.clusters_controls import ControlPanel
from backend.config import COLLAGE_RES_SCALE, IMAGES_PER_PREVIEW
from backend.data_manager import DataManager
from backend.helpers.context_menu_handler import ContextMenuHandler
from backend.helpers.ctrl_helper import ControlHelper
from backend.helpers.feature_extraction_thread import FeatureExtractionThread
from backend.utils.image_utils import merge_images_collage


class ClustersPresenter(QObject):
    """Presenter for managing clusters and their display in the ClustersViewWidget."""
    class_updated = Signal(str)

    def __init__(self,
                clusters_view_widget,
                data_manager: DataManager,
                control_panel: ControlPanel,
                images_per_preview: int = 25):
        super().__init__()
        self.last_clicked_card_id = None
        self.clusters_view_widget = clusters_view_widget
        self.control_helper = ControlHelper(self.clusters_view_widget)
        self.data_manager = data_manager
        self.control_panel = control_panel
        self.selected_card_ids = set()
        self.ctrl_pressed = False
        self.context_menu_handler = ContextMenuHandler(self)
        self.images_per_preview = images_per_preview

        # Connect signals from ControlPanel
        self.control_panel.startButton.clicked.connect(self.start_analysis)
        self.control_panel.resetButton.clicked.connect(self.reset_analysis)

        self.control_helper.ctrl_signal.connect(self.set_ctrl_pressed)

    def load_clusters(self, cluster_ids: list = None):
        """
        Loads existing clusters from the DataManager and creates cards.

        Args:
            cluster_ids (list): List of cluster IDs to load. If None, all clusters are loaded.
        """
        if cluster_ids is None:
            for cluster_id, cluster in self.data_manager.clusters.items():
                preview_image_path = self._generate_cluster_preview(cluster_id)
                card = self.clusters_view_widget.create_cluster_card(cluster_id, preview_image_path)
                card.cluster_color = cluster.color
                card.card_clicked.connect(self.on_card_clicked)
                card.split_requested.connect(self.split_selected_cluster)
                card.merge_requested.connect(self.merge_selected_clusters)
                card.assign_class_requested.connect(self.assign_clusters_to_class)
                card.cluster_double_clicked.connect(self.show_cluster_viewer)
        else:
            for cluster_id in cluster_ids:
                cluster = self.data_manager.get_cluster(cluster_id)
                preview_image_path = self._generate_cluster_preview(cluster_id)
                card = self.clusters_view_widget.create_cluster_card(cluster_id, preview_image_path)
                card.cluster_color = cluster.color
                card.card_clicked.connect(self.on_card_clicked)
                card.split_requested.connect(self.split_selected_cluster)
                card.merge_requested.connect(self.merge_selected_clusters)
                card.assign_class_requested.connect(self.assign_clusters_to_class)
                card.cluster_double_clicked.connect(self.show_cluster_viewer)
        self.data_manager._update_clusters_metadata()

    def start_analysis(self):
        """Performs clustering and creates cluster cards."""
        if len(self.clusters_view_widget.clusters) > 0:
            self.reset_analysis()

        n_clusters = self.control_panel.clustersSlider.value()
        n_iter = self.control_panel.iterationsSlider.value()

        # Extract true labels from filenames
        true_labels = []
        for image in self.data_manager.samples.values():
            filename = os.path.basename(image.path)
            true_label = filename.split('_')[0]  # Extract label before the first underscore
            true_labels.append(true_label)

        # Extract features if not already done
        if any(len(sample.features) == 0 for sample in self.data_manager.samples.values()):
            self.progress_info_bar = ProgressInfoBar.new(
                icon=InfoBarIcon.INFORMATION,
                title="Extracting Features",
                content="Extracting image features...",
                duration=-1,
                position=InfoBarPosition.BOTTOM_RIGHT,
                parent=self.clusters_view_widget
            )
            self.feature_extraction_thread = FeatureExtractionThread(list(self.data_manager.samples.keys()),
                                                                     self.data_manager)
            self.feature_extraction_thread.progress_updated.connect(self.progress_info_bar.set_progress)
            self.feature_extraction_thread.finished.connect(self.on_feature_extraction_finished)
            self.feature_extraction_thread.start()
        else:
            self.data_manager.perform_clustering(n_clusters=n_clusters, n_iter=n_iter)  # Perform clustering
            self.load_clusters()  # Load the newly created clusters

        # Calculate ARI and NMI
        predicted_labels = []
        for image in self.data_manager.samples.values():  # Iterate through images in DataManager
            # Get the cluster ID of the image
            for cluster_id, cluster in self.data_manager.clusters.items():
                if image in cluster.samples:
                    predicted_labels.append(cluster_id)  # Append to predicted_labels
                    break

    def on_feature_extraction_finished(self):
        """Handles the completion of feature extraction."""
        self.progress_info_bar.set_progress(100)
        self.progress_info_bar.set_title('Feature Extraction Complete')
        self.progress_info_bar.set_content('All features extracted')
        print("Feature extraction finished.")
        QTimer.singleShot(1000, self.progress_info_bar.customClose)

        n_clusters = self.control_panel.clustersSlider.value()
        n_iter = self.control_panel.iterationsSlider.value()
        self.data_manager.perform_clustering(n_clusters=n_clusters, n_iter=n_iter)  # Perform clustering
        self.load_clusters()  # Load the newly created clusters

    def reset_analysis(self):
        """Clears all clusters."""
        cluster_ids = list(self.data_manager.clusters.keys())  # Get a list of cluster IDs
        for cluster_id in cluster_ids:
            self.data_manager.delete_cluster(cluster_id)
        self.selected_card_ids.clear()
        self.clusters_view_widget.clear_cluster_cards()

    @Slot(str, Qt.KeyboardModifiers, Qt.MouseButton)
    def on_card_clicked(self, card_id, modifiers, button):
        """Handles card click events."""
        if button == Qt.RightButton:  # Right-click (RMB)
            if len(self.selected_card_ids) == 0:  # No cards selected
                self.select_card(card_id)  # Select the clicked card
            else:
                if card_id not in self.selected_card_ids:
                    self.select_card(card_id)  # Select the clicked card if not already selected
        else:  # Left-click
            if modifiers == Qt.ControlModifier:  # Ctrl/Cmd click
                if card_id in self.selected_card_ids:
                    self.deselect_card(card_id)
                else:
                    self.select_card(card_id)
            elif modifiers == Qt.ShiftModifier:  # Shift click
                # TODO: Implement range selection logic here.
                pass
            else:  # Single click (no modifiers)
                self.clear_selection()
                self.select_card(card_id)

        self.last_clicked_card_id = card_id  # Update last clicked card

    def select_card(self, card_id: str):
        """Selects the card with the given ID."""
        self.selected_card_ids.add(card_id)
        # find the card with the given ID
        for card in self.clusters_view_widget.clusters:
            if card.cluster_id == card_id:
                card.selected = True
                card.update()

    def deselect_card(self, card_id: str):
        """Deselects the card with the given ID."""
        self.selected_card_ids.discard(card_id)
        for card in self.clusters_view_widget.clusters:
            if card.cluster_id == card_id:
                card.selected = False
                card.update()

    def clear_selection(self):
        """Clears the current selection."""
        # Update visuals for selected cards
        for selected_card_id in self.selected_card_ids:
            for card in self.clusters_view_widget.clusters:
                if card.cluster_id == selected_card_id:
                    card.selected = False
                    card.update()
        self.selected_card_ids.clear()

    def _generate_cluster_preview(self, cluster_id):
        """Generates a preview collage for the cluster."""
        cluster = self.data_manager.get_cluster(cluster_id)
        image_paths = [image.path for image in cluster.samples][:self.images_per_preview]
        collage_image = merge_images_collage(image_paths, scale=COLLAGE_RES_SCALE)
        if collage_image:
            preview_path = os.path.join("temp", f"cluster_{cluster_id}_preview.png")
            os.makedirs("temp", exist_ok=True)
            collage_image.save(preview_path)
            return preview_path
        else:
            # Return a default image path if no images in the cluster
            return "path/to/default_cluster_preview.png"

    def split_selected_cluster(self):
        """Splits the selected cluster."""
        cluster_ids = list(self.selected_card_ids)
        cluster_id = cluster_ids[0]
        print(f"Splitting cluster: {cluster_id}")
        n_clusters = self.control_panel.clustersSlider.value()
        self.data_manager.split_cluster(cluster_id, n_clusters=n_clusters)
        self.clusters_view_widget.clear_cluster_cards()  # Clear existing cards
        self.load_clusters()  # Reload clusters to reflect the changes

    def merge_selected_clusters(self, selected_card_ids):
        """Merges the selected clusters."""
        print(f"Merging clusters: {selected_card_ids}")

        # Check if there are at least two clusters to merge
        if len(selected_card_ids) < 2:
            print("Error: Need at least two clusters to merge.")
            return

        # Merge clusters in the DataManager
        cluster_ids = list(selected_card_ids)
        new_cluster = self.data_manager.merge_clusters(cluster_ids)

        # Update the UI by removing old cards and creating a new one for the merged cluster
        print(cluster_ids)
        self.clusters_view_widget.clear_cluster_cards(cluster_ids)  # Clear existing cards
        self.load_clusters([new_cluster.id])  # Reload clusters to reflect the changes

    def assign_clusters_to_class(self, class_name):
        """Assigns the images in the selected clusters to a class."""
        cluster_ids = list(self.selected_card_ids)
        if not cluster_ids:
            return  # Nothing selected
        class_object = self.data_manager.get_class_by_name(class_name)

        if not class_object:
            print(f"Error: Class '{class_name}' not found.")
            CustomInfoBar.error(
                title='Class Assignment Failed',
                content=f"Class '{class_name}' not found",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self.clusters_view_widget  # Assuming you have a reference to the main window
            )
            return

        try:
            image_ids = []
            for cluster_id in cluster_ids:
                cluster = self.data_manager.get_cluster(cluster_id)
                if cluster:
                    image_ids.extend([image.id for image in cluster.samples])
            old_classes_to_images = {}
            for image_id in image_ids:
                image = self.data_manager.get_image(image_id)
                if image.class_id not in old_classes_to_images:
                    old_classes_to_images[image.class_id] = []
                old_classes_to_images[image.class_id].append(image_id)

            # remove images from old classes
            for class_id, image_ids in old_classes_to_images.items():
                self.data_manager.remove_images_from_class(image_ids, class_id)
                self.class_updated.emit(class_id)  # Emit signal to update old class previews

            # assign images to class
            self.data_manager.add_images_to_class(image_ids, class_object.id)
            self.class_updated.emit(class_object.id)
            self.clear_selection()
            CustomInfoBar.success(
                title='Class Assignment Successful',
                content=f"Successfully assigned {len(cluster_ids)} clusters to class '{class_name}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=5,
                duration=3000,
                parent=self.clusters_view_widget
            )
        except Exception as e:
            print(f"Error assigning clusters to class '{class_name}': {e}")
            CustomInfoBar.error(
                title='Class Assignment Failed',
                content=f"An error occurred: {e}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self.clusters_view_widget
            )

    def clear_selections(self, except_card=None):
        """Clears the selection state of all cards except the specified card."""
        for card in self.selected_card_ids:
            if card != except_card:
                card.selected = False
                self.selected_card_ids.remove(card)
                card.update()

    def set_ctrl_pressed(self, ctrl_pressed):
        """Sets the Ctrl key pressed state."""
        self.ctrl_pressed = ctrl_pressed

    def show_cluster_viewer(self, cluster_id):
        """Shows the ClassClusterViewer for the selected cluster."""
        cluster = self.data_manager.get_cluster(cluster_id)
        viewer = ClassClusterViewer(f"Cluster: {cluster_id[:8]}", self, self.clusters_view_widget)  # Create viewer
        viewer.show()  # Show the viewer window
        for image in cluster.samples:
            viewer.add_card(image.id)
        viewer.gallery_view.viewport().update()

    @Slot(str)
    def show_summary(self, cluster_id):
        """Shows the summary window for the given cluster ID."""
        cluster = self.data_manager.get_cluster(cluster_id)
        if not cluster:
            print(f"Error: Cluster ID {cluster_id} not found.")
            return

        parameter_data = {}
        for parameter in ["area", "perimeter", "eccentricity", "solidity", "aspect_ratio", "circularity",
                          "major_axis_length", "minor_axis_length", "mean_intensity", "std_intensity",
                          "compactness", "convexity", "curl", "volume"]:
            values = [self.data_manager.masks[image.mask_id].attributes[parameter]
                      for image in cluster.samples if image.mask_id is not None]
            if values:
                avg = np.mean(values)
                std = np.std(values)
                parameter_data[parameter] = (avg, std)

        summary_window = ClassClusterSummary(f"Cluster Summary: {cluster.id[:8]}",
                                             parent=self.clusters_view_widget)
        summary_window.set_summary_data(cluster.id[:8], len(cluster.samples), parameter_data)
        summary_window.show()

    def clear(self) -> None:
        """Clears the presenter state and disconnects signals."""
        logging.info("Clearing ClustersPresenter state.")

        # Disconnect ControlPanel signals
        self.control_panel.startButton.clicked.disconnect(self.start_analysis)
        self.control_panel.resetButton.clicked.disconnect(self.reset_analysis)

        # Disconnect ControlHelper signals
        self.control_helper.ctrl_signal.disconnect(self.set_ctrl_pressed)

        # Disconnect presenter-specific signals
        self.class_updated.disconnect()

        # Stop and clean up worker threads
        if hasattr(self, 'feature_extraction_thread') and self.feature_extraction_thread:
            if self.feature_extraction_thread.isRunning():
                self.feature_extraction_thread.quit()
                self.feature_extraction_thread.wait()
            self.feature_extraction_thread = None
            logging.info("FeatureExtractionThread stopped and cleaned up.")

        # Reset internal state
        self.last_clicked_card_id = None
        self.selected_card_ids.clear()
        self.ctrl_pressed = False

        # Clear selected clusters
        self.clusters_view_widget.clear_cluster_cards()

        # Remove references to data_manager and control_panel
        self.data_manager = None
        self.control_panel = None
        self.control_helper = None
        self.context_menu_handler = None

        logging.info("ClustersPresenter cleared successfully.")