# backend/delegates/gallery_delegate.py

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPixmap, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import QStyledItemDelegate, QStyle


class GalleryDelegate(QStyledItemDelegate):
    """
    Custom delegate to render gallery items efficiently with enhanced layout and styling.
    Supports dynamic resizing of gallery cards.
    """

    def __init__(self, parent=None, view_mode='image', card_size=QSize(100, 130)):
        """
        Initializes the GalleryDelegate.

        Parameters:
            parent (QObject): Parent object.
            view_mode (str): Current view mode ('image' or 'mask').
            card_size (QSize): Initial size of the gallery card.
        """
        super().__init__(parent)
        self.view_mode = view_mode  # 'image' or 'mask'
        self.card_size = card_size  # QSize object representing card dimensions

        # Define brushes and pens for selection and default states
        self.selected_brush = QBrush(QColor("#ADD8E6"))  # Light blue for selection
        self.default_brush = QBrush(QColor("#FFFFFF"))   # White background
        self.error_pen = QPen(QColor("#FF0000"))         # Red pen for errors
        self.text_pen = QPen(QColor("#000000"))          # Black pen for text

    def set_card_size(self, new_size: QSize):
        """
        Sets a new size for the gallery card and triggers a repaint.

        Parameters:
            new_size (QSize): The new size for the gallery card.
        """
        if new_size != self.card_size:
            self.card_size = new_size
            # Notify the view that all items have changed size
            self.parent().viewport().update()

    def paint(self, painter, option, index):
        painter.save()

        # Retrieve data from the model
        name = index.data(Qt.DisplayRole)
        image = index.data(Qt.UserRole)

        # Load the appropriate pixmap based on view mode
        if self.view_mode == 'mask':
            pixmap = image.load_mask_pixmap()
        else:
            pixmap = image.load_pixmap()

        # Handle cases where pixmap might be None
        if pixmap is None or pixmap.isNull():
            # If pixmap failed to load, display an error message
            painter.setPen(self.error_pen)
            painter.drawText(option.rect, Qt.AlignCenter, "Failed to load")
            painter.restore()
            return

        # Define the main rectangle
        rect = option.rect
        padding = 10
        text_height = 25
        badge_radius = 8

        # Draw background with rounded corners
        painter.setRenderHint(QPainter.Antialiasing)
        radius = 10  # Adjust the radius as needed

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)
        painter.fillPath(path, painter.brush())

        if option.state & QStyle.State_MouseOver:
            painter.setBrush(QColor("#E0F7FA"))  # Light cyan background on hover
            painter.drawRoundedRect(rect, radius, radius)
        if option.state & QStyle.State_Selected:
            pen = QPen(QColor("#02d1ca"), 2)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)

        # Calculate available area for the image
        image_area_x = rect.x() + padding
        image_area_y = rect.y() + padding
        image_area_width = rect.width() - 2 * padding
        image_area_height = rect.height() - 2 * padding - text_height

        # Draw pixmap (image or mask)
        if isinstance(pixmap, QPixmap) and not pixmap.isNull():
            # Scale pixmap based on available image area, maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                QSize(image_area_width, image_area_height),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Calculate position to center the image
            offset_x = (image_area_width - scaled_pixmap.width()) / 2
            offset_y = (image_area_height - scaled_pixmap.height()) / 2

            pixmap_x = image_area_x + offset_x
            pixmap_y = image_area_y + offset_y

            # Draw the pixmap
            painter.drawPixmap(int(pixmap_x), int(pixmap_y), scaled_pixmap)

            # Now, determine pixmap_rect for later use (e.g., badge positioning)
            pixmap_rect = QRect(
                int(pixmap_x),
                int(pixmap_y),
                scaled_pixmap.width(),
                scaled_pixmap.height()
            )
        elif isinstance(pixmap, QPixmap) and pixmap.isNull():
            # If pixmap failed to load, display an error message
            painter.setPen(self.error_pen)
            painter.drawText(QRect(image_area_x, image_area_y, image_area_width, image_area_height), Qt.AlignCenter, "Failed to load")
        else:
            # Handle case when pixmap is None
            pass

        # Draw image name
        text_rect = QRect(
            rect.x() + padding,
            rect.y() + rect.height() - padding - text_height,
            rect.width() - 2 * padding,
            text_height
        )
        painter.setPen(self.text_pen)
        painter.drawText(text_rect, Qt.AlignCenter, name)

        # Draw class color marker (badge)
        if hasattr(image, 'class_color'):
            class_color = QColor(image.class_color)
        else:
            class_color = QColor("#000000")  # Default to black if not specified

    # Define the rectangle at the top center of the card
        plank_width = rect.width() // 3  # Adjust width as desired
        plank_height = rect.height() // 20  # Adjust height as desired
        plank_rect = QRect(
            rect.x() + (rect.width() - plank_width) // 2,
            rect.y() + 1,  # Positioning below the top edge
            plank_width,
            plank_height
        )
        painter.setBrush(QBrush(class_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(plank_rect)


        painter.restore()


    def sizeHint(self, option, index):
        """
        Provides the size hint for each gallery item with adjusted dimensions.

        Parameters:
            option (QStyleOptionViewItem): Style options.
            index (QModelIndex): Index of the item.

        Returns:
            QSize: Recommended size for the item.
        """
        return self.card_size  # Return dynamic card size
