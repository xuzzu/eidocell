from PySide6.QtCore import Slot, QTimer, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout
from UI.navigation_interface.workspace.views.gallery.gallery import GalleryContainer
from UI.navigation_interface.workspace.views.gallery.gallery_controls import GalleryControls


class GalleryViewWidget(QWidget):
    def __init__(self, main_window_reference, parent=None):
        super().__init__(parent)
        self.gallery_presenter = None
        self.cards = []
        self.main_layout = QVBoxLayout(self)
        self.controls = GalleryControls(self)
        self.gallery_container = GalleryContainer(self)  # Placeholder for Gallery
        self.gallery_container.installEventFilter(self)
        self.main_layout.addWidget(self.controls)
        self.main_layout.addWidget(self.gallery_container, 1)  # Gallery will stretch
        self.main_layout.setSpacing(0)
        self.main_window_reference = main_window_reference
        self.loading_more = False

        # Timer to check scroll area position
        self.scroll_check_timer = QTimer(self)  # Timer to check scrollbar value
        self.scroll_check_timer.timeout.connect(self.check_scroll_and_load)

        # Parameter states
        self.sorting_order = "Ascending"
        self.sorting_parameter = "Area"

        # Connect signals
        self.controls.scale_slider.valueChanged.connect(self.resize_tiles)
        self.resize_tiles(self.controls.scale_slider.value())  # Set initial tile size
        self.controls.sortAscButton.toggled.connect(self.updateSortingOrder)
        self.controls.sortDescButton.toggled.connect(self.updateSortingOrder)
        self.controls.parameterComboBox.currentIndexChanged.connect(self.updateSortingParameter)

    def set_presenter(self, gallery_presenter):
        self.gallery_presenter = gallery_presenter

    def handle_gallery_mouse_press(self, event):
        """Handles mouse press events on the gallery."""
        pass

    def get_card_from_widget(self, widget):
        """Traverses up the widget hierarchy to find the GalleryCard."""
        pass

    def handle_gallery_context_menu(self, event):
        """Handles context menu events on the gallery."""
        pass

    def reset_ui_elements(self):
        """Resets the gallery UI elements to their default state."""
        self.controls.mask_toggle.setChecked(False)       # Reset mask view
        self.controls.sortAscButton.setChecked(False)        # Reset sort order (ascending by default)
        self.controls.sortDescButton.setChecked(False)
        self.controls.parameterComboBox.setCurrentIndex(0)   # Reset sorting parameter ("Area" by default)
        self.sorting_order = "Ascending"  # Reset the actual sorting order
        self.sorting_parameter = "Area"  # Reset the actual sorting parameter
        self.gallery_presenter.mask_view_enabled = False
        if self.gallery_presenter:
            self.gallery_presenter.toggle_mask_view()  # Update mask view after loading

    def updateSortingOrder(self, checked):
        """Update the sorting order based on the toggled button."""
        if checked:  # Only process when the button is checked
            order = "Ascending" if self.sender() is self.controls.sortAscButton else "Descending"
            self.sorting_order = order  # Reset sorting order
            print(f"Sorting order changed to: {order}")
            if order == "Ascending":
                self.controls.sortDescButton.setChecked(False)
            else:
                self.controls.sortAscButton.setChecked(False)
            self.gallery_presenter.sort_gallery()

    def updateSortingParameter(self, index):
        """Update the current sorting parameter."""
        parameter = self.controls.parameterComboBox.itemText(index)
        self.sorting_parameter = parameter
        print(f"Sorting parameter changed to: {parameter}")
        self.gallery_presenter.sort_gallery()

    def resize_tiles(self, new_size):
        """Resizes the gallery tiles based on the slider value."""
        new_width = 100 * new_size / 100  # Scale the width based on the slider value
        new_height = int(new_width * 1.3)  # Maintain aspect ratio (e.g., height = width * 1.3)

        # Update the delegate's card size
        self.gallery_container.gallery_view.delegate.set_card_size(QSize(new_width, new_height))

        # Update the grid size of the view
        grid_size = QSize(new_width + self.gallery_container.gallery_view.spacing(), new_height + self.gallery_container.gallery_view.spacing())
        self.gallery_container.gallery_view.setGridSize(grid_size)

        # Trigger a relayout
        self.gallery_container.gallery_view.doItemsLayout()
        self.gallery_container.gallery_view.viewport().update()

    def clear_cards(self) -> None:
        """Clears all gallery cards from the view."""
        self.gallery_container.gallery_view.model.clear()

    def update_gallery_layout(self):
        """Updates the gallery layout after sorting."""
        pass

    def check_scroll_and_load(self):
        """Checks the scrollbar position and loads more cards if needed."""
        pass

    @Slot()
    def load_more_cards(self):
        """Loads more cards from the queue."""
        pass