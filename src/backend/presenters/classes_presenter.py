### backend/presenters/classes_presenter.py
import logging
import numpy as np

import os
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox, QTreeWidgetItem
from qfluentwidgets import FlyoutView, PrimaryPushButton, Flyout, FlyoutAnimationType
from qfluentwidgets.components.material import AcrylicLineEdit

from UI.dialogs.class_cluster_summary import ClassClusterSummary
from UI.dialogs.class_cluster_view import ClassClusterViewer
from backend.config import COLLAGE_RES_SCALE, IMAGES_PER_PREVIEW
from backend.data_manager import DataManager
from backend.objects.sample_class import SampleClass
from backend.utils.image_utils import merge_images_collage


class ClassesPresenter:
    """Presenter for managing classes and their display in the ClassesViewWidget."""

    def __init__(self,
                classes_view_widget,
                data_manager: DataManager,
                images_per_preview: int = 25):
        self.classes_view_widget = classes_view_widget
        self.data_manager = data_manager
        self.tree_widget = classes_view_widget.class_tree_view  # Get reference to TreeView
        self.tree_widget.show()
        self.images_per_preview = images_per_preview
        # self.tree_view.setHeaderHidden(True)

    def load_classes(self):
        """Loads existing classes and creates their cards and tree view items."""
        for class_object in self.data_manager.classes.values():
            preview_image_path = self._generate_class_preview(class_object.id)
            card = self.classes_view_widget.create_class_card(class_object.name,
                                                              class_object.id,
                                                              class_object.color,
                                                              preview_image_path)
            # Add the class to the tree view
            self.add_class_to_tree(class_object, parent_node=None)  # Add to root by default

    def add_class_to_tree(self, class_object: SampleClass, parent_node=None):
        """Adds a class to the tree view under the specified parent node."""
        print(f"Adding class to tree: {class_object.name}")
        item = QTreeWidgetItem([class_object.name])
        self._add_children_to_tree_item(class_object, item)  # Add potential children recursively
        if parent_node:
            self._get_tree_item_from_class_object(parent_node).addChild(item)
        else:
            self.tree_widget.addTopLevelItem(item)

    def _add_children_to_tree_item(self, class_object: SampleClass, item: QTreeWidgetItem):
        """Recursively adds children of an ImageClass to a QTreeWidgetItem."""
        for child_class in class_object.children:
            child_item = QTreeWidgetItem([child_class.name])
            item.addChild(child_item)
            self._add_children_to_tree_item(child_class, child_item)

    def _get_tree_item_from_class_object(self, class_object: SampleClass) -> QTreeWidgetItem:
        """Finds the corresponding QTreeWidgetItem for a given ImageClass."""
        root_item = self.tree_widget.invisibleRootItem()
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if self._find_tree_item_recursive(item, class_object):
                return item
        return None

    def _find_tree_item_recursive(self, item: QTreeWidgetItem, class_object: SampleClass) -> QTreeWidgetItem:
        """Recursively searches for the QTreeWidgetItem associated with the ImageClass."""
        if item.text(0) == class_object.name:
            return item
        for i in range(item.childCount()):
            child_item = item.child(i)
            found_item = self._find_tree_item_recursive(child_item, class_object)
            if found_item:
                return found_item
        return None

    def show_class_viewer(self, class_id):
        """Shows the ClassClusterViewer for the selected class."""
        class_object = self.data_manager.get_class(class_id)
        viewer = ClassClusterViewer(f"Class: {class_object.name}", self, self.classes_view_widget)  # Create viewer
        viewer.show()  # Show the viewer window
        for image in class_object.samples:
            viewer.add_card(image.id)
        viewer.gallery_view.viewport().update()
        print(f"Showing viewer for class: {class_object.name}")

    def create_class(self, class_name):
        """Creates a new class and adds a card for it."""
        class_object = self.data_manager.create_class(class_name)
        preview_image_path = self._generate_class_preview(class_object.id)
        self.classes_view_widget.create_class_card(class_object.name,
                                                   class_object.id,
                                                   class_object.color,
                                                   preview_image_path)
        self.add_class_to_tree(class_object, parent_node=None)

    def _generate_class_preview(self, class_id):
        """Generates a preview image for the class."""
        class_object = self.data_manager.get_class(class_id)
        image_paths = [image.path for image in class_object.samples][:self.images_per_preview]
        collage_image = merge_images_collage(image_paths, scale=COLLAGE_RES_SCALE)
        if collage_image:
            preview_path = os.path.join("temp", f"class_{class_id}_preview.png")
            os.makedirs("temp", exist_ok=True)
            collage_image.save(preview_path)
            return preview_path
        else:
            # Return a default image or placeholder if no images in class
            return "path/to/default_class_preview.png"

    def on_class_added(self, class_id: str):
        """Handles the class_added signal from the DataManager."""
        class_object = self.data_manager.get_class(class_id)
        preview_image_path = self._generate_class_preview(class_id)
        self.classes_view_widget.create_class_card(class_object.name,
                                                   class_object.id,
                                                   class_object.color,
                                                   preview_image_path)
        self.add_class_to_tree(class_object, parent_node=None)

    def on_class_updated(self, class_id):
        """Handles the class_updated signal from the DataManager."""
        # Card
        preview_image_path = self._generate_class_preview(class_id)
        self.classes_view_widget.update_class_card(class_id, preview_image_path)

    def handle_rename_class(self, class_id):
        """Handles renaming a class."""
        class_to_rename = self.data_manager.get_class(class_id)

        # Create FlyoutView for renaming
        view = FlyoutView(
            title=f"Renaming \"{class_to_rename.name}\"...",
            content='',
            icon=None
        )

        # Add content to FlyoutView
        name_input = AcrylicLineEdit(parent=view)
        name_input.setPlaceholderText("Enter new class name")
        view.addWidget(name_input)

        # Create Button
        rename_button = PrimaryPushButton("Rename", view)
        view.addWidget(rename_button)
        rename_button.clicked.connect(lambda: self._rename_class(class_id, name_input.text(), view))

        # Create the Flyout
        Flyout.make(
            view=view,
            target=next((card for card in self.classes_view_widget.classes if card.class_id == class_id), None),
            parent=self.classes_view_widget,
            aniType=FlyoutAnimationType.DROP_DOWN
        )

    def _rename_class(self, class_id, new_class_name, flyout_view: FlyoutView):
        """Renames the class and updates the UI."""
        if not new_class_name:
            QMessageBox.warning(self.classes_view_widget, "Error", "Class name cannot be empty.")
            return

        if self.data_manager.get_class_by_name(new_class_name):
            QMessageBox.warning(self.classes_view_widget, "Error", "A class with this name already exists.")
            return

        class_to_rename = self.data_manager.get_class(class_id)
        class_to_rename.name = new_class_name

        # Update the card label
        card_to_update = next((card for card in self.classes_view_widget.classes if card.class_id == class_id), None)
        if card_to_update:
            card_to_update.label.setText(new_class_name)

        # Update the tree element (stupid version for now)
        self.tree_widget.clear()
        for class_object in self.data_manager.classes.values():
            self.add_class_to_tree(class_object, parent_node=None)  # Add to root by default

        flyout_view.close()  # Close the flyout after renaming

    def delete_class(self, class_id):
        """Deletes a class, moves its images to Uncategorized, and removes its card."""
        uncategorized_class_id = self.data_manager.get_class_by_name("Uncategorized").id

        # Move images to the Uncategorized class
        class_to_delete = self.data_manager.get_class(class_id)
        image_ids = [image.id for image in class_to_delete.samples]
        self.data_manager.add_images_to_class(image_ids, uncategorized_class_id)

        # Card
        self.classes_view_widget.delete_class_card(class_id)

        # Tree
        item_to_remove = self._get_tree_item_from_class_object(class_to_delete)
        if item_to_remove:
            parent_item = item_to_remove.parent()
            if parent_item:
                parent_item.removeChild(item_to_remove)
            else:
                self.tree_widget.takeTopLevelItem(self.tree_widget.indexOfTopLevelItem(item_to_remove))

        # Delete the class
        self.data_manager.delete_class(class_id)

    @Slot(str)
    def show_summary(self, class_id):
        """Shows the summary window for the given class ID."""
        class_object = self.data_manager.get_class(class_id)
        if not class_object:
            print(f"Error: Class ID {class_id} not found.")
            return

        parameter_data = {}
        for parameter in ["area", "perimeter", "eccentricity", "solidity", "aspect_ratio", "circularity",
                          "major_axis_length", "minor_axis_length", "mean_intensity", "std_intensity",
                          "compactness", "convexity", "curl", "volume"]:
            values = [self.data_manager.masks[image.mask_id].attributes[parameter]
                      for image in class_object.samples if image.mask_id is not None]
            if values:
                avg = np.mean(values)
                std = np.std(values)
                parameter_data[parameter] = (avg, std)

        summary_window = ClassClusterSummary(f"Class Summary: {class_object.name}", parent=self.classes_view_widget)
        summary_window.set_summary_data(class_object.name, len(class_object.samples), parameter_data)
        summary_window.show()

    def clear(self) -> None:
        """Clears the presenter state and disconnects signals."""
        logging.info("Clearing ClassesPresenter state.")

        # Disconnect any signals connected to the view
        # Assuming you have connected signals like class_added, class_updated
        # try:
        #     self.class_updated.disconnect()
        # except TypeError:
        #     pass  # No connections to disconnect

        # Clear the view
        self.classes_view_widget.clear_classes()

        # Reset internal state
        self.data_manager = None
        self.classes_view_widget = None

        logging.info("ClassesPresenter cleared successfully.")
