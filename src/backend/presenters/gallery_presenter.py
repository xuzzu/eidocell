import logging

from PySide6.QtCore import Qt, QObject
from PySide6.QtCore import Signal, Slot
from qfluentwidgets import InfoBarPosition

from UI.dialogs.custom_info_bar import CustomInfoBar
from UI.navigation_interface.workspace.views.gallery.image_card import ImageCard
from backend.data_manager import DataManager
from backend.helpers.context_menu_handler import ContextMenuHandler
from backend.helpers.ctrl_helper import ControlHelper
from backend.helpers.sort_cards_thread import SortCardsThread


class GalleryPresenter(QObject):
    class_updated = Signal(str)
    gallery_sorted = Signal(list)

    def __init__(self, gallery_view_widget, data_manager: DataManager):
        super().__init__()
        self.last_clicked_card_id = None
        self.sort_ascending = None
        self.sort_parameter = None
        self.gallery_view_widget = gallery_view_widget
        self.data_manager = data_manager
        self.mask_view_enabled = False
        self.control_helper = ControlHelper(self.gallery_view_widget)
        self.ctrl_pressed = False
        self.selected_card_ids = set()
        self.cached_images = []
        self.context_menu_handler = ContextMenuHandler(self)
        self.thumbnail_quality = 75
        self.data_manager.class_updated.connect(self.on_class_updated)

        # Connect the mask view toggle signal
        self.gallery_view_widget.controls.mask_toggle.clicked.connect(self.toggle_mask_view)

    def on_card_added(self, card):
        """Handles the addition of a card to the layout."""
        try:
            self.gallery_view_widget.add_card_to_layout(card)
        except Exception as e:
            print(f"An error occurred while adding card to layout: {e}")

    def load_gallery(self):
        # self.progress_info_bar = ProgressInfoBar.new(
        #     icon=InfoBarIcon.INFORMATION,
        #     title="Loading Gallery",
        #     content="Loading images...",
        #     duration=-1,
        #     position=InfoBarPosition.BOTTOM_RIGHT,
        #     parent=self.gallery_view_widget.main_window_reference
        # )
        for image_id in self.data_manager.samples:
            img_id = image_id
            path = self.data_manager.samples[image_id].path
            class_id = self.data_manager.samples[image_id].class_id
            class_color = self.data_manager.get_class(class_id).color
            # get mask
            mask_id = self.data_manager.samples[image_id].mask_id
            try:
                masked_image_path = self.data_manager.masks[mask_id].masked_image_path
            except:
                masked_image_path = None
            image = ImageCard(
                id=img_id,
                name=image_id[:8],
                path=path,
                class_id=class_id,
                class_color=class_color,
                mask_path=masked_image_path
            )
            self.gallery_view_widget.gallery_container.gallery_view.model.addImage(image)


    def toggle_mask_view(self):
        """Toggles between displaying original images and segmentation masks."""
        self.mask_view_enabled = self.gallery_view_widget.controls.mask_toggle.isChecked()
        print(f"Mask view enabled: {self.mask_view_enabled}")

        # Check if all images have masks
        if not all([image.mask_id is not None for image in self.data_manager.samples.values()]):
            CustomInfoBar.error(
                title='Masks required',
                content=f"Please ensure all images have corresponding masks before enabling mask view.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=self.gallery_view_widget.main_window_reference
            )
            return

        self.gallery_view_widget.gallery_container.gallery_view.delegate.view_mode = 'mask' if self.mask_view_enabled else 'image'

        # Update the gallery model and view to reflect changes.
        for i in range(self.gallery_view_widget.gallery_container.gallery_view.model.rowCount()):
            index = self.gallery_view_widget.gallery_container.gallery_view.model.index(i)
            self.gallery_view_widget.gallery_container.gallery_view.model.dataChanged.emit(index, index, [Qt.DecorationRole])  # Emit dataChanged for DecorationRole


    def get_selected_images(self):
        selected_indexes = self.gallery_view_widget.gallery_container.gallery_view.selectionModel().selectedIndexes()
        selected_images = [index.data(Qt.UserRole) for index in selected_indexes]
        return selected_images

    def perform_class_assignment(self, class_name):
        selected_images = self.get_selected_images()
        image_ids = [image.id for image in selected_images]

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
                parent=self.gallery_view_widget.main_window_reference
            )
            return

        try:
            # Remove from old classes
            old_classes_to_images = {}
            for image_id in image_ids:
                image = self.data_manager.get_image(image_id)
                if image.class_id not in old_classes_to_images:
                    old_classes_to_images[image.class_id] = []
                old_classes_to_images[image.class_id].append(image_id)

            for class_id, image_ids in old_classes_to_images.items():
                self.data_manager.remove_images_from_class(image_ids, class_id)
                self.class_updated.emit(class_id)  # Update the old class

            self.data_manager.add_images_to_class(image_ids, class_object.id)
            self.class_updated.emit(class_object.id) # update the new class

            # Update class colors (MAYBE CHANGE NEEDED)
            for image in selected_images:
                image.class_color = class_object.color
            self.gallery_view_widget.gallery_container.gallery_view.viewport().update()

            CustomInfoBar.success(
                title='Class Assignment Successful',
                content=f"Successfully assigned {len(image_ids)} images to class '{class_name}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self.gallery_view_widget.main_window_reference
            )
        except Exception as e:
            print(f"Error assigning images to class '{class_name}': {e}")
            CustomInfoBar.error(
                title='Class Assignment Failed',
                content=f"An error occurred: {e}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self.gallery_view_widget.main_window_reference
            )

    def sort_gallery(self):
        """Starts the card sorting thread."""
        self.sort_thread = SortCardsThread(
            self.data_manager,
            self.gallery_view_widget.sorting_parameter,
            self.gallery_view_widget.sorting_order
        )
        self.sort_thread.sorted_data.connect(self.on_cards_sorted)
        self.sort_thread.start()

    def on_class_updated(self, class_id):
        # get class object and update class color for cards
        class_object = self.data_manager.get_class(class_id)
        image_ids = [image.id for image in class_object.samples]
        for image in self.gallery_view_widget.gallery_container.gallery_view.model._images:
            if image.id in image_ids:
                image.class_color = class_object.color
        self.gallery_view_widget.gallery_container.gallery_view.viewport().update()

    def on_segmentation_completed(self):
        # assign masked image paths to images in the gallery
        ids_to_masked_image_paths = {}
        for image_id in self.data_manager.samples:
            mask_id = self.data_manager.samples[image_id].mask_id
            masked_image_path = self.data_manager.masks[mask_id].masked_image_path if mask_id is not None else None
            ids_to_masked_image_paths[image_id] = masked_image_path
        for image in self.gallery_view_widget.gallery_container.gallery_view.model._images:
            image.mask_path = ids_to_masked_image_paths[image.id]


    @Slot(list)
    def on_cards_sorted(self, sorted_image_ids):
        """Handles the sorted_data signal from the sorting thread."""
        print("Cards sorted, updating layout...")
        self.gallery_view_widget.gallery_container.gallery_view.model.reorderImagesByIds(sorted_image_ids)


    def clear(self) -> None:
        """Clears the presenter state and disconnects signals."""
        logging.info("Clearing GalleryPresenter state.")

        # Disconnect any connected signals
        try:
            self.gallery_sorted.disconnect()
            self.class_updated.disconnect()
        except Exception:
            pass  # No connections to disconnect

        if hasattr(self, 'sort_thread') and self.sort_thread:
            if self.sort_thread.isRunning():
                self.sort_thread.quit()
                self.sort_thread.wait()
            self.sort_thread = None
            logging.info("SortCardsThread stopped and cleaned up.")

        # Clear the gallery view
        self.gallery_view_widget.clear_cards()

        # Reset internal state
        self.data_manager = None
        self.gallery_view_widget = None
        self.context_menu_handler = None

        logging.info("GalleryPresenter cleared successfully.")

