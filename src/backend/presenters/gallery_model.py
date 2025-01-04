# backend/models/gallery_model.py

from collections import OrderedDict

from PySide6.QtCore import QThreadPool, QRunnable
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex
from PySide6.QtGui import QPixmap


class LoadPixmapTask(QRunnable):
    def __init__(self, image, callback):
        super().__init__()
        self.image = image
        self.callback = callback

    def run(self):
        pixmap = QPixmap(self.image.path)
        self.callback(self.image.id, pixmap)

class GalleryModel(QAbstractListModel):
    """
    Custom model to manage gallery images efficiently.
    """

    def __init__(self, images=None, parent=None):
        """
        Initializes the GalleryModel.

        Parameters:
            images (list of Sample): Initial list of Image objects.
            parent (QObject): Parent object.
        """
        super().__init__(parent)
        self._images = images or []  # List of Image objects
        self._pixmap_cache = OrderedDict()
        self._max_cache_size = 1000  # Adjust based on memory constraints
        self.placeholder_path = r""

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the number of rows in the model.

        Parameters:
            parent (QModelIndex): Parent index.

        Returns:
            int: Number of images.
        """
        return len(self._images)

    def loadPixmapAsync(self, image):
        def onPixmapLoaded(image_id, pixmap):
            self._pixmap_cache[image_id] = pixmap
            row = self._images.index(image)
            idx = self.index(row)
            self.dataChanged.emit(idx, idx, [Qt.DecorationRole])

        task = LoadPixmapTask(image, onPixmapLoaded)
        QThreadPool.globalInstance().start(task)

    def data(self, index, role=Qt.DisplayRole):
        """
        Provides data to the view based on the role and index.

        Parameters:
            index (QModelIndex): Index of the data.
            role (int): Role for which data is requested.

        Returns:
            QVariant: Data corresponding to the role.
        """
        if not index.isValid():
            return None
        if not (0 <= index.row() < self.rowCount()):
            return None

        image = self._images[index.row()]

        if role == Qt.DisplayRole:
            return image.name
        ### for async loading ###
        # elif role == Qt.DecorationRole:
        #     if image.id in self._pixmap_cache:
        #         return self._pixmap_cache[image.id]
        #     else:
        #         # Return placeholder pixmap
        #         placeholder = QPixmap(self.placeholder_path)
        #         self.loadPixmapAsync(image)
        #         return placeholder
        elif role == Qt.DecorationRole:
            # Efficient Pixmap Caching without scaling
            if image.id in self._pixmap_cache:
                return self._pixmap_cache[image.id]
            else:
                pixmap = QPixmap(image.path)
                if not pixmap.isNull():
                    self._pixmap_cache[image.id] = pixmap
                    if len(self._pixmap_cache) > self._max_cache_size:
                        self._pixmap_cache.popitem(last=False)  # Remove oldest
                    return pixmap
                else:
                    return QPixmap()  # Return empty pixmap if loading failed
        elif role == Qt.UserRole:
            return image  # Return the Image object for further use
        return None

    def flags(self, index):
        """
        Returns the item flags for the given index.

        Parameters:
            index (QModelIndex): Index of the item.

        Returns:
            Qt.ItemFlags: Flags indicating the item's properties.
        """
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def addImage(self, image):
        """
        Adds a new image to the model.

        Parameters:
            image (Sample): Image object to add.
        """
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._images.append(image)
        self.endInsertRows()

    def removeImage(self, row):
        """
        Removes an image from the model at the specified row.

        Parameters:
            row (int): Row index of the image to remove.
        """
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(QModelIndex(), row, row)
            image = self._images.pop(row)
            if image.id in self._pixmap_cache:
                del self._pixmap_cache[image.id]
            self.endRemoveRows()

    def clear(self):
        """
        Clears all images from the model.
        """
        self.beginResetModel()
        self._images.clear()
        self._pixmap_cache.clear()
        self.endResetModel()

    def updateImage(self, row, new_image):
        """
        Updates an existing image in the model.

        Parameters:
            row (int): Row index of the image to update.
            new_image (Sample): New Image object to replace the existing one.
        """
        if 0 <= row < self.rowCount():
            self._images[row] = new_image
            self.dataChanged.emit(self.index(row), self.index(row), [Qt.DisplayRole, Qt.DecorationRole])
            if new_image.id in self._pixmap_cache:
                del self._pixmap_cache[new_image.id]

    def reorderImagesByIds(self, sorted_image_ids):
        """
        Reorders the images in the model according to the list of sorted image IDs.

        Parameters:
            sorted_image_ids (list of str): The sorted list of image IDs.
        """
        id_to_image = {image.id: image for image in self._images}

        # Create a new list of images in the sorted order
        new_images = [id_to_image[image_id] for image_id in sorted_image_ids if image_id in id_to_image]

        # If there are images in the model not in sorted_image_ids, decide whether to keep them
        # For this example, we'll keep them at the end of the list
        remaining_images = [image for image in self._images if image.id not in sorted_image_ids]
        new_images.extend(remaining_images)

        self.layoutAboutToBeChanged.emit()
        self._images = new_images
        self.layoutChanged.emit()

    def get_selected_images(self):
        """
        Returns a list of selected images.

        Returns:
            list[Sample]: List of selected images.
        """
        selected_indices = self.selectedIndexes()
        selected_images = [self._images[idx.row()] for idx in selected_indices]
        return selected_images