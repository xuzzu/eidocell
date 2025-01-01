# backend/objects/sample.py
from PySide6.QtCore import Qt
from dataclasses import dataclass, field
from typing import Optional
from PySide6.QtGui import QPixmap
import os

@dataclass
class ImageCard:
    """
    Represents an image in the gallery.

    Attributes:
        id (str): Unique identifier for the sample.
        name (str): Display name of the sample.
        path (str): File path to the image.
        class_id (str): Identifier for the class/category the image belongs to.
        class_color (str): Color associated with the image's class for visual indicators.
        mask_path (Optional[str]): File path to the mask image, if applicable.
        # Add additional fields as necessary, e.g., features, metadata, etc.
    """
    id: str
    name: str
    path: str
    class_id: str
    class_color: str
    mask_path: Optional[str] = None
    _pixmap_cache: Optional[QPixmap] = field(default=None, init=False, repr=False)
    _mask_pixmap_cache: Optional[QPixmap] = field(default=None, init=False, repr=False)


    def __post_init__(self):
        """
        Post-initialization processing. Can be used to validate paths or preprocess data.
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Image path does not exist: {self.path}")

        if self.mask_path:
            if not os.path.exists(self.mask_path):
                print(f"Warning: Mask path does not exist for sample {self.id}: {self.mask_path}")

    def load_pixmap(self) -> Optional[QPixmap]:
        """Loads the image as a QPixmap."""
        if self._pixmap_cache:
            return self._pixmap_cache
        pixmap = QPixmap(self.path)
        if pixmap.isNull():
            print(f"Failed to load pixmap for Sample ID {self.id}: {self.path}")
            return None
        self._pixmap_cache = pixmap
        return pixmap

    def load_mask_pixmap(self) -> Optional[QPixmap]:
        """Loads the mask image as a QPixmap."""
        if not self.mask_path:
            return None
        if self._mask_pixmap_cache:
            return self._mask_pixmap_cache
        pixmap = QPixmap(self.mask_path)
        if pixmap.isNull():
            print(f"Failed to load mask pixmap for Sample ID {self.id}: {self.mask_path}")
            return None
        self._mask_pixmap_cache = pixmap
        return pixmap
