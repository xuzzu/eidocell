### UI/class_cluster_viewer.py
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QListView
from PySide6.QtWidgets import QMenu
# import qspaceritem, qsizepolicy, qscrollarea, qslider, qhboxlayout, qvboxlayout, qwidget, qlabel
from PySide6.QtWidgets import QSpacerItem, QSizePolicy, QHBoxLayout
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from UI.navigation_interface.workspace.views.gallery.gallery_delegate import GalleryDelegate
# from UI.navigation_interface.workspace.views.gallery.gallery import GalleryView
from UI.navigation_interface.workspace.views.gallery.image_card import ImageCard
from backend.presenters.gallery_model import GalleryModel
from qfluentwidgets import Slider


# Doing like that for now because did not figure out the context menu handling for the class-cluster viewer yet.
class GalleryView(QListView):
    """
    Custom QListView to display gallery cards efficiently.
    """

    def __init__(self, parent=None):
        """
        Initializes the GalleryView.

        Parameters:
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)

        # Initialize the model
        self.model = GalleryModel()
        self.setModel(self.model)

        # Initialize the delegate
        self.delegate = GalleryDelegate(self)
        self.setItemDelegate(self.delegate)

        # Configure the view
        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setResizeMode(QListView.Adjust)
        self.setSpacing(10)
        self.setUniformItemSizes(False)
        self.setSelectionMode(QListView.ExtendedSelection)
        self.setMovement(QListView.Static)
        self.setWrapping(True)
        self.setMouseTracking(True)

        # Enable smooth scrolling for better performance
        self.setVerticalScrollMode(QListView.ScrollPerPixel)
        self.setHorizontalScrollMode(QListView.ScrollPerPixel)

        # Enable drag and drop if needed
        # self.setDragEnabled(True)
        # self.setAcceptDrops(True)
        # self.setDropIndicatorShown(True)

        # Optional: Set minimum size
        self.setMinimumSize(200, 200)

class ClassClusterViewer(QWidget):
    """Widget for viewing the contents of a class or cluster."""

    def __init__(self, title, presenter, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Window)  # Set window flags to make it a separate window
        self.layout = QVBoxLayout(self)
        self.label = QLabel(title, self)  # Display the class/cluster name
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        self.presenter = presenter
        
        # Set initial geometry
        self.setGeometry(200, 200, 800, 600)

        # set fluent design style
        self.setStyleSheet("background-color: #FFF; color: #000;")

        # Scale controls layout
        self.scale_controls_layout = QHBoxLayout()
        self.scale_label = QLabel("Scale:", self)
        self.scale_slider = Slider(Qt.Horizontal, self)
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setValue(100)  # Default scale
        self.scale_slider.setFixedWidth(200)  # Adjust width as needed
        spacer_left = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacer_right = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.scale_controls_layout.addItem(spacer_left)
        self.scale_controls_layout.addWidget(self.scale_label)
        self.scale_controls_layout.addWidget(self.scale_slider)
        self.scale_controls_layout.addItem(spacer_right)

        self.layout.addLayout(self.scale_controls_layout) # Add scale controls at the top
        self.layout.addWidget(self.label)  # Title label remains below the slider

        # Initialize GalleryView and GalleryDelegate
        self.gallery_view = GalleryView(self)
        self.gallery_delegate = GalleryDelegate(self.gallery_view)
        self.gallery_view.setItemDelegate(self.gallery_delegate)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.gallery_view)
        self.layout.addWidget(self.scroll_area)

        # Connect slider
        self.scale_slider.valueChanged.connect(self.resize_tiles)

        # Resize tiles (initial size)
        self.resize_tiles(100)

    def add_card(self, image_id: str):  # Add type hint
        """Adds an ImageCard to the viewer immediately."""
        # Retrieve image data from the presenter's DataManager
        image_data = self.presenter.data_manager.samples[image_id]
        class_color = self.presenter.data_manager.classes[image_data.class_id].color if image_data.class_id else None
        try:
            image = ImageCard(id=image_id,
                            name=image_id[:8],
                            path=image_data.path,
                            mask_path=self.presenter.data_manager.masks[image_data.mask_id].masked_image_path,
                            class_id=image_data.class_id,
                            class_color=class_color
                            )
        except Exception as e:
            image = ImageCard(id=image_id,
                                        name=image_id[:8],
                                        path=image_data.path,
                                        mask_path=None,
                                        class_id=image_data.class_id,
                                        class_color=class_color
                                        )

        self.gallery_view.model.addImage(image)

    def resize_tiles(self, new_size):
        new_width = 100 * new_size / 100
        aspect_ratio = 1.3  # Or calculate from initial image size
        new_height = new_width * aspect_ratio

        self.gallery_delegate.set_card_size(QSize(new_width, new_height))
        grid_size = QSize(new_width + self.gallery_view.spacing(), new_height + self.gallery_view.spacing()) #Corrected attribute
        self.gallery_view.setGridSize(grid_size)
        self.gallery_view.doItemsLayout()
        self.gallery_view.viewport().update()  # Ensure update

    def contextMenuEvent(self, event):
        index = self.gallery_view.indexAt(event.pos())
        if index.isValid():
            menu = QMenu(self)
            menu.setStyleSheet("QMenu {background-color: #234f4b; color: white;}")
            assign_class_menu = menu.addMenu("Assign Class")

            for class_object in self.presenter.data_manager.classes.values():
                action = QAction(class_object.name, menu)
                action.triggered.connect(
                    lambda checked=False, name=class_object.name:
                    self.assign_class_to_selected(name)
                )
                assign_class_menu.addAction(action)

            menu.exec_(event.globalPos())

    def assign_class_to_selected(self, class_name):
        """Assigns the selected samples in the viewer to the given class."""
        selected_indexes = self.gallery_view.selectionModel().selectedIndexes()
        image_ids = [index.data(Qt.UserRole).id for index in selected_indexes]

        if not image_ids:
            return

        class_object = self.presenter.data_manager.get_class_by_name(class_name)  # Access data_manager through presenter
        if not class_object:
            print(f"Error: Class '{class_name}' not found.") # Handle error as needed
            return

        try:
            # REMOVE FROM OLD CLASSES
            old_classes_to_images = {}
            for image_id in image_ids:
                image = self.presenter.data_manager.get_image(image_id)
                old_class_id = image.class_id

                if old_class_id:
                    if old_class_id not in old_classes_to_images:
                        old_classes_to_images[old_class_id] = []
                    old_classes_to_images[old_class_id].append(image_id)

            # Now remove images from the old classes
            for old_class_id, images_to_remove in old_classes_to_images.items():
                self.presenter.data_manager.remove_images_from_class(images_to_remove, old_class_id)

                # Notify the classes presenter about the update in the DataManager
                self.presenter.class_updated.emit(old_class_id)

            # ADD TO NEW CLASS
            self.presenter.data_manager.add_images_to_class(image_ids, class_object.id)

            # Notify classes presenter
            self.presenter.class_updated.emit(class_object.id)

            # Update card colors in the viewer:
            for index in selected_indexes:
                card = index.data(Qt.UserRole)
                card.class_color = class_object.color
            self.gallery_view.viewport().update()

        except Exception as e:
            print(f"Error assigning class in viewer: {e}")  # Or show a message box

    def closeEvent(self, event):
        """Stop the layout updater thread when closing."""
        super().closeEvent(event)
        