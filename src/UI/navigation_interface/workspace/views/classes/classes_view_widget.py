import logging

from PIL.ImageQt import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QHBoxLayout,
    QAbstractItemView,
    QFrame,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QGraphicsDropShadowEffect
)
from qfluentwidgets import PrimaryPushButton, FlyoutView, Flyout, TreeWidget
from qfluentwidgets.components.material import AcrylicLineEdit
from qfluentwidgets.components.widgets.flyout import FlyoutAnimationType

from UI.navigation_interface.workspace.views.classes.class_card import ClassCard
from UI.utils.flow_gallery import FlowGallery


class ClassesViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.classes = []  # Store references to ClassCard objects

        # Initialize the class gallery
        self.class_gallery = FlowGallery(self)  # Create the class gallery

        # Initialize the tree view for class hierarchy
        self.class_tree_view = TreeWidget(self)
        self.class_tree_view.setHeaderHidden(True)
        self.class_tree_view.setDragDropMode(QAbstractItemView.InternalMove)
        self.class_tree_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.class_tree_view.setStyleSheet("""
            QTreeWidget {
                background-color: #f9f9f9;
                border: none; /* Remove default border */
                padding: 5px;
                font-size: 14px;
                border-radius: 8px; /* Rounded corners */
            }
            QTreeWidget::item {
                padding-left: 20px; /* Increase padding to prevent arrow overlap */
                height: 24px;        /* Adjust item height for better spacing */
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(:/icons/arrow_closed.png); /* Replace with your arrow icon */
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(:/icons/arrow_open.png); /* Replace with your arrow icon */
            }
        """)

        # Create a frame to contain the tree view and the button
        self.tree_frame = QFrame(self)
        self.tree_frame.setFrameShape(QFrame.NoFrame)  # Remove frame border
        self.tree_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px; /* Rounded corners */
            }
        """)

        # Apply Subtle Shadow Effect to the Frame (optional, based on previous designs)
        # Uncomment the following lines if you wish to have a subtle shadow
        """
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)  # Reduced blur radius for lighter shadow
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 20))  # Less opaque shadow
        self.tree_frame.setGraphicsEffect(shadow)
        """

        # Layout for the tree view frame
        self.tree_layout = QVBoxLayout()
        self.tree_layout.setContentsMargins(10, 10, 10, 10)
        self.tree_layout.setSpacing(10)

        # Initialize the "New Class" button
        self.create_class_button = PrimaryPushButton("New Class", self.tree_frame)
        self.create_class_button.setFixedHeight(35)
        self.create_class_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.create_class_button.setStyleSheet("""
            QPushButton {
            background-color: #009faa;
            color: white;
            border: none;
            border-radius: 7px;
            font-size: 13px;
            }
            QPushButton:hover {
            background-color: #14939c;
            }
        """)
        self.create_class_button.clicked.connect(self._show_create_class_flyout)
        self.create_class_button.setToolTip("Click to add a new class to the hierarchy.")
        
        # Add the "New Class" button above the label
        self.tree_layout.addWidget(self.create_class_button)

        # Label for the tree view
        self.tree_label = QLabel("Class Hierarchy", self.tree_frame)
        self.tree_label.setAlignment(Qt.AlignCenter)
        self.tree_label.setFont(QFont("Arial", 11))
        self.tree_label.setStyleSheet("""
            QLabel {
                color: #333333;
                padding: 5px;
                border-bottom: 1px solid #d0d0d0; /* Add bottom border */
            }
        """)

        # Add the label to the layout
        self.tree_layout.addWidget(self.tree_label)

        # Add the tree view to the layout
        self.tree_layout.addWidget(self.class_tree_view, stretch=1)

        # Set the layout to the frame
        self.tree_frame.setLayout(self.tree_layout)

        # Set the size policy of tree_frame to allow vertical expansion
        self.tree_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Initialize the flow layout properties
        self.class_gallery.flow_layout.needAni = True
        self.class_gallery.flow_layout.duration = 150

        # Create a vertical layout for the tree frame (now without the button)
        self.button_tree_layout = QVBoxLayout()
        self.button_tree_layout.setContentsMargins(10, 10, 10, 10)
        self.button_tree_layout.setSpacing(15)

        # Add the tree frame to the vertical layout
        self.button_tree_layout.addWidget(self.tree_frame)

        # Set minimum width for the tree frame
        self.tree_frame.setMinimumWidth(280)

        # Main layout setup
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(20)

        # Add widgets to the main layout
        self.main_layout.addWidget(self.class_gallery, 3)  # Gallery stretches more
        self.main_layout.addLayout(self.button_tree_layout, 1)  # Side panel with tree frame

        # Set the main layout
        self.setLayout(self.main_layout)

        self.classes_presenter = None  # Initialize the presenter

    def _show_create_class_flyout(self):
        """Shows the CreateClassFlyout using FlyoutView."""
        # Create FlyoutView
        view = FlyoutView(
            title="Creating New Class...",
            content='',
            icon=None
        )

        # Add content to FlyoutView
        self.class_name_input = AcrylicLineEdit(parent=view)  # Store the line edit as a class attribute
        self.class_name_input.setPlaceholderText("Enter class name")
        view.addWidget(self.class_name_input)

        # Create Button
        create_button = PrimaryPushButton("Create", view)
        view.addWidget(create_button)
        create_button.clicked.connect(self._create_class)

        # Create the Flyout using Flyout.make
        self.create_class_flyout = Flyout.make(
            view=view,
            target=self.create_class_button,
            parent=self,
            aniType=FlyoutAnimationType.DROP_DOWN
        )

    def _create_class(self):
        """Handles the creation of a new class."""
        class_name = self.class_name_input.text().strip()  # Access line edit directly

        # Input validation (add more checks if needed)
        if not class_name:
            QMessageBox.warning(self, "Error", "Class name cannot be empty.")
            return

        if self.classes_presenter and self.classes_presenter.data_manager.get_class_by_name(class_name):  # Check for duplicates
            QMessageBox.warning(self, "Error", "A class with this name already exists.")
            return

        if self.classes_presenter:
            self.classes_presenter.create_class(class_name)

        # You can close the flyout here if you want:
        self.create_class_flyout.close()

    def create_class_card(self, class_name, class_id, class_color, preview_image_path):
        """Creates and adds a new ClassCard to the gallery."""
        card = ClassCard(preview_image_path, self.classes_presenter, class_id, self)
        card.label.setText(class_name)  # Set the class name on the card
        card.class_color = QColor(class_color)  # Set the class color
        self.classes.append(card)
        self.class_gallery.flow_layout.addWidget(card)
        return card

    def delete_class_card(self, class_id):
        """Deletes the ClassCard with the given class_id."""
        card_to_delete = next((card for card in self.classes if card.class_id == class_id), None)
        if card_to_delete:
            self.class_gallery.flow_layout.removeWidget(card_to_delete)
            self.classes.remove(card_to_delete)
            card_to_delete.deleteLater()

    def update_class_card(self, class_id, preview_image_path):
        """Updates the preview image of the ClassCard with the given class_id."""
        card_to_update = next((card for card in self.classes if card.class_id == class_id), None)
        if card_to_update:
            card_to_update.iconWidget.setPixmap(QPixmap(preview_image_path))
            card_to_update.iconWidget.setScaledContents(True)
            card_to_update.iconWidget.setFixedHeight(95)

    def set_presenter(self, presenter):
        """Sets the ClassesPresenter for this widget."""
        self.classes_presenter = presenter

    def clear_classes(self) -> None:
        """Clears all class cards from the gallery and tree view."""
        logging.info("Clearing all classes from ClassesViewWidget.")
        # Clear class cards
        for card in self.classes:
            self.class_gallery.flow_layout.removeWidget(card)
            card.deleteLater()
        self.classes.clear()

        # Clear tree view
        self.class_tree_view.clear()
        logging.info("All classes cleared from ClassesViewWidget.")
