# backend/backend_initializer.py

import logging
from typing import Optional, Any

from PySide6.QtWidgets import QWidget
from backend.config import load_settings
from backend.data_manager import DataManager  # Ensure DataManager is correctly imported
from backend.presenters.analysis_presenter import AnalysisPresenter
from backend.presenters.classes_presenter import ClassesPresenter
from backend.presenters.clusters_presenter import ClustersPresenter
from backend.presenters.gallery_presenter import GalleryPresenter
from backend.presenters.segmentation_presenter import SegmentationPresenter
from backend.presenters.sessions_presenter import SessionPresenter
from backend.processor import Processor
from backend.segmentation import SegmentationModel
from backend.session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BackendInitializer:
    """Initializes the backend components and connects them."""

    def __init__(self, workspace: QWidget):
        """
        Initializes the BackendInitializer with the given workspace.

        Args:
            workspace (QWidget): The main workspace widget of the application.
        """
        # Load settings
        self.settings = load_settings()

        # Essential data
        self.session_manager: SessionManager = SessionManager()
        self.session_presenter: Optional[SessionPresenter] = None
        self.session: Optional[Any] = None
        self.workspace: QWidget = workspace
        self.workspace.setDisabled(True)
        self.segmentation_model: SegmentationModel = SegmentationModel() # later add configuration option (settings)

        # DataManager
        self.data_manager: Optional[DataManager] = None

        # Presenters
        self.gallery_presenter: Optional[GalleryPresenter] = None
        self.classes_presenter: Optional[ClassesPresenter] = None
        self.clusters_presenter: Optional[ClustersPresenter] = None
        self.analysis_presenter: Optional[AnalysisPresenter] = None
        self.segmentation_presenter: Optional[SegmentationPresenter] = None

    def apply_settings(self):
        """Applies the changes made in the settings dialog."""
        # Update settings in config.py
        self.settings = load_settings()

        # Update or re-initialize components
        if self.data_manager:
            self.data_manager.settings = self.settings
            self.data_manager.processor = Processor(self.settings["model"])
            print(f"Processor re-initialized with model: {self.settings['model']}")

            self.classes_presenter.images_per_preview = self.settings["images_per_collage"]
            self.clusters_presenter.images_per_preview = self.settings["images_per_collage"]
            self.gallery_presenter.thumbnail_quality = self.settings["thumbnail_quality"]

            self.classes_presenter.classes_view_widget.clear_classes()
            self.clusters_presenter.clusters_view_widget.clear_clusters()
            self.gallery_presenter.gallery_view_widget.clear_cards()

            self.classes_presenter.load_classes()
            self.clusters_presenter.load_clusters()
            self.gallery_presenter.load_gallery()

    def on_session_chosen(self, session_id: str) -> None:
        """Handles the event when a session is selected."""

        logging.info(f"Session chosen with ID: {session_id}")
        self.workspace.setEnabled(True)

        # Retrieve the selected session
        self.session = self.session_manager.get_session(session_id)
        if not self.session:
            logging.error(f"Session with ID {session_id} not found.")
            return

        # Initialize DataManager with the selected session
        self.data_manager = DataManager(self.session, self.settings)
        logging.info("DataManager initialized.")

        # If no images are loaded per metadata json, load them from images_directory
        if len(self.data_manager.samples) == 0:
            self.data_manager.load_images_from_folder(self.session.images_directory)
            self.session_manager.save_session(self.session)
            logging.info('Loaded new images and saved the session.')

        # Clean up presenters from previous session if any
        self._cleanup_presenters()

        # Initialize presenters with the new DataManager
        try:
            self.init_gallery_presenter(self.workspace.galleryView)
            self.gallery_presenter.load_gallery()
        except Exception as e:
            logging.error(f"Error initializing GalleryPresenter: {e}")

        try:
            self.init_classes_presenter(self.workspace.classesView)
            self.classes_presenter.load_classes()
        except Exception as e:
            logging.error(f"Error initializing ClassesPresenter: {e}")

        try:
            self.init_clusters_presenter(self.workspace.clustersView, self.workspace.clustersView.controlPanel)
            self.clusters_presenter.load_clusters()
        except Exception as e:
            logging.error(f"Error initializing ClustersPresenter: {e}")

        try:
            self.init_analysis_presenter(self.workspace.analysisView)
            # self.analysis_presenter.load_analysis()  # Assuming a load method exists
        except Exception as e:
            logging.error(f"Error initializing AnalysisPresenter: {e}")

        try:
            self.init_segmentation_presenter(self.workspace.segmentationView)
            self.segmentation_presenter.resample_samples()  # Assuming a load method exists
        except Exception as e:
            logging.error(f"Error initializing SegmentationPresenter: {e}")
            

        # Connect signals between presenters
        if self.gallery_presenter and self.classes_presenter:
            self.gallery_presenter.class_updated.connect(self.classes_presenter.on_class_updated)
            logging.info("Connected gallery_presenter.class_updated to classes_presenter.on_class_updated.")

        if self.clusters_presenter and self.classes_presenter:
            self.clusters_presenter.class_updated.connect(self.classes_presenter.on_class_updated)
            logging.info("Connected clusters_presenter.class_updated to classes_presenter.on_class_updated.")

        if self.clusters_presenter and self.gallery_presenter:
            self.clusters_presenter.class_updated.connect(self.gallery_presenter.on_class_updated)
            logging.info("Connected clusters_presenter.class_updated to gallery_presenter.on_class_updated.")

        if self.gallery_presenter and self.segmentation_presenter:
            self.segmentation_presenter.segmentation_completed.connect(self.gallery_presenter.on_segmentation_completed)
            logging.info("Connected gallery_presenter.on_segmentation_completed to segmentation_presenter.segmentation_completed.")

        # Switch to the gallery view
        self.workspace.pivot.setCurrentItem(self.workspace.galleryView.objectName())
        self.workspace.stackedWidget.setCurrentWidget(self.workspace.galleryView)
        self.workspace.galleryView.reset_ui_elements()

    def _cleanup_presenters(self) -> None:
        """Cleans up existing presenters to prevent duplication."""
        presenters = [
            ('classes_presenter', self.classes_presenter),
            ('clusters_presenter', self.clusters_presenter),
            ('gallery_presenter', self.gallery_presenter),
            ('analysis_presenter', self.analysis_presenter)
        ]

        for name, presenter in presenters:
            if presenter:
                # If presenters have specific cleanup methods, call them
                if hasattr(presenter, 'clear'):
                    presenter.clear()
                    logging.info(f"Cleared data for {name}.")

                # Disconnect signals if necessary

                # Delete presenter instance
                del presenter
                setattr(self, name, None)
                logging.info(f"Deleted {name}.")

    def init_sessions_presenter(self, session_view_widget: QWidget) -> None:
        """Initializes the SessionPresenter."""

        if self.session_presenter:
            self.session_presenter.session_chosen.disconnect(self.on_session_chosen)
            del self.session_presenter
            logging.info("Disconnected and deleted existing sessions presenter.")

        self.session_presenter = SessionPresenter(self.session_manager, session_view_widget)
        self.session_presenter.session_chosen.connect(self.on_session_chosen)
        logging.info("Initialized new sessions presenter.")

    def init_gallery_presenter(self, gallery_view_widget: QWidget) -> None:
        """Initializes the GalleryPresenter."""

        if not self.data_manager:
            logging.error("Error: DataManager not initialized before initializing gallery presenter.")
            return

        self.gallery_presenter = GalleryPresenter(gallery_view_widget, self.data_manager)
        gallery_view_widget.set_presenter(self.gallery_presenter)
        logging.info("Initialized gallery presenter.")

    def init_classes_presenter(self, classes_view_widget: QWidget) -> None:
        """Initializes the ClassesPresenter."""

        if not self.data_manager:
            logging.error("Error: DataManager not initialized before initializing classes presenter.")
            return

        self.classes_presenter = ClassesPresenter(classes_view_widget, self.data_manager)
        classes_view_widget.set_presenter(self.classes_presenter)
        logging.info("Initialized classes presenter.")

    def init_clusters_presenter(self, clusters_view_widget: QWidget, control_panel: QWidget) -> None:
        """Initializes the ClustersPresenter."""

        if not self.data_manager:
            logging.error("Error: DataManager not initialized before initializing clusters presenter.")
            return

        self.clusters_presenter = ClustersPresenter(clusters_view_widget, self.data_manager, control_panel)
        clusters_view_widget.set_presenter(self.clusters_presenter)
        logging.info("Initialized clusters presenter.")

    def init_analysis_presenter(self, analysis_view_widget: QWidget) -> None:
        """Initializes the AnalysisPresenter."""

        if not self.data_manager:
            logging.error("Error: DataManager not initialized before initializing analysis presenter.")
            return

        self.analysis_presenter = AnalysisPresenter(analysis_view_widget, self.data_manager, self.segmentation_model)
        analysis_view_widget.set_presenter(self.analysis_presenter)
        logging.info("Initialized analysis presenter.")

    def init_segmentation_presenter(self, segmentation_view_widget: QWidget) -> None:
        """Initializes the SegmentationPresenter."""

        if not self.data_manager:
            logging.error("Error: DataManager not initialized before initializing segmentation presenter.")
            return

        self.segmentation_presenter = SegmentationPresenter(segmentation_view_widget, self.data_manager, self.segmentation_model)
        segmentation_view_widget.set_presenter(self.segmentation_presenter)
        logging.info("Initialized segmentation presenter.")