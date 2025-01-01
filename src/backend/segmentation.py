import cv2
import numpy as np
import onnxruntime as ort
from PySide6.QtCore import Signal, QObject
from scipy import ndimage
from scipy.spatial import ConvexHull
from skimage.measure import regionprops

from backend.config import SEGMENTATION_MODEL_PATH


class SegmentationModel(QObject):
    progress_updated = Signal(int)
    segmentation_progress = Signal(int)

    def __init__(self, model_path=SEGMENTATION_MODEL_PATH):
        # Load the ONNX model
        super().__init__()
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def predict_mask(self, image_path):
        # Load and preprocess the image
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (224, 224))
        image = image.astype(np.float32) / 255.0  # Normalize image
        image = np.expand_dims(image, axis=0)  # Add batch dimension

        self.progress_updated.emit(0)  # Signal 0% progress

        # Run inference
        mask = self.session.run([self.output_name], {self.input_name: image})[0]

        # Post-process the output mask
        mask = (mask.squeeze() > 0.5).astype(np.uint8) * 255

        return mask

    def predict_mask_otsu(self, image_path, grayscale=True, max_distance_ratio=0.3, min_component_size=10):
        """
        Create a binary mask using Otsu's thresholding and retain connected components near the center.

        Parameters:
        - image (numpy.ndarray): Input image.
        - max_distance_ratio (float): Maximum distance from the center as a fraction of the image's diagonal.
        - grayscale (bool): If True, convert image to grayscale before thresholding.
        - min_component_size (int): Minimum size (in pixels) for components to be included in the mask.
        
        Returns:
        - mask_selected (numpy.ndarray): Binary mask with selected connected components.
        """
        image = cv2.imread(image_path)

        if grayscale and len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Apply Otsu's thresholding
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        mask = mask // 255  # Binary mask

        # Label connected components
        labeled_mask, num_features = ndimage.label(mask)

        # Calculate image center
        height, width = mask.shape
        center_y, center_x = height / 2, width / 2
        image_diagonal = np.sqrt(height**2 + width**2)
        max_distance = max_distance_ratio * image_diagonal

        # Initialize an empty mask for selected components
        mask_selected = np.zeros_like(mask, dtype=np.uint8)

        for component in range(1, num_features + 1):
            component_mask = (labeled_mask == component)
            if np.any(component_mask):
                # Calculate component size
                component_size = np.sum(component_mask)
                if component_size < min_component_size:
                    continue  # Skip small components
                
                # Calculate centroid
                centroid = ndimage.center_of_mass(component_mask)
                distance = np.sqrt((centroid[0] - center_y)**2 + (centroid[1] - center_x)**2)
                if distance <= max_distance:
                    mask_selected[component_mask] = 1

        # invert the mask
        mask_selected = 1 - mask_selected

        return mask_selected

    def predict_mask_adaptive(self, image_path, grayscale=True, block_size=35, c=10):
        """
        Create a binary mask using adaptive thresholding.

        Parameters:
        - image (numpy.ndarray): Input image.
        - grayscale (bool): If True, convert image to grayscale before thresholding.
        - block_size (int): Size of a pixel neighborhood used to calculate threshold.
        - C (int): Constant subtracted from the mean or weighted mean.

        Returns:
        - mask (numpy.ndarray): Binary mask.
        """
        image = cv2.imread(image_path)

        if grayscale and len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        mask = cv2.adaptiveThreshold(gray, 
                                     255, 
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 
                                     block_size, 
                                     c)
        mask = mask // 255  # Convert to binary
        return mask

    def predict_mask_watershed(self, image_path, grayscale=True, foreground_threshold=0.7, morph_kernel_size=(3,3)):
        """
        Create a binary mask using the watershed algorithm.

        Parameters:
        - image_path (str): Path to input image.
        - grayscale (bool): If True, convert image to grayscale before processing.
        - foreground_threshold (float): Threshold for sure foreground area.
        - morph_kernel_size (tuple): Kernel size for morphological dilation.

        Returns:
        - mask (numpy.ndarray): Binary mask.
        """
        image = cv2.imread(image_path)

        if grayscale and len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Noise removal
        blur = cv2.GaussianBlur(gray, (5,5), 0)

        # Thresholding
        ret, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Sure background area
        kernel = np.ones(morph_kernel_size, np.uint8)
        sure_bg = cv2.dilate(thresh, kernel, iterations=3)

        # Finding sure foreground area
        dist_transform = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
        ret, sure_fg = cv2.threshold(dist_transform, foreground_threshold * dist_transform.max(), 255, 0)

        # Finding unknown region
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)

        # Marker labeling
        ret, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        # Apply watershed
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if len(image.shape) == 3 else image.copy()
        markers = cv2.watershed(image_bgr, markers)
        mask = np.zeros_like(gray, dtype=np.uint8)
        mask[markers > 1] = 1
        return mask

    def get_valid_contours(self, contours, image_size, min_area_ratio=0.05):
        min_contour_area = min_area_ratio * image_size
        return [c for c in contours if cv2.contourArea(c) > min_contour_area]

    def get_object_properties(self, image_path, mask, min_area_ratio=0.05):
        # Load the image
        image = cv2.imread(image_path)
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Check if both image and mask have the same dimensions
        if image.shape[:2] != mask.shape:
            raise ValueError("Image and mask dimensions do not match.")

        image_size = image.shape[0] * image.shape[1]

        # Find contours from the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours based on size
        valid_contours = self.get_valid_contours(contours, image_size, min_area_ratio)

        if not valid_contours:
            # return dictionary with zero values
            return {
                "area": 0,
                "perimeter": 0,
                "eccentricity": 0,
                "solidity": 0,
                "aspect_ratio": 0,
                "circularity": 0,
                "major_axis_length": 0,
                "minor_axis_length": 0,
                "mean_intensity": 0,
                "std_intensity": 0,
                "compactness": 0,
                "convexity": 0,
                "curl": 0,
                "volume": 0
            }
            # or none (fix in the future)
            # return None

        # 1. Overlapping region (segmented object) image
        combined_mask = np.zeros_like(mask)
        for c in valid_contours:
            cv2.drawContours(combined_mask, [c], -1, 255, thickness=cv2.FILLED)

        # 2. Cumulative area in pixels
        area = np.sum([cv2.contourArea(c) for c in valid_contours])

        # 3. Cumulative perimeter in pixels
        perimeter = np.sum([cv2.arcLength(c, True) for c in valid_contours])

        # 4. Eccentricity, solidity, and aspect ratio
        all_points = np.concatenate([c.reshape(-1, 2) for c in valid_contours], axis=0)
        hull = ConvexHull(all_points)
        hull_area = hull.volume
        solidity = area / hull_area if hull_area != 0 else 0

        if len(all_points) >= 5:
            (x, y), (major_axis_length, minor_axis_length), angle = cv2.fitEllipse(all_points)
            eccentricity = np.sqrt(1 - (minor_axis_length / major_axis_length) ** 2)
        else:
            major_axis_length = minor_axis_length = eccentricity = 0

        x, y, w, h = cv2.boundingRect(all_points)
        aspect_ratio = float(w) / h if h != 0 else 0

        # 5. Circularity
        circularity = 4 * np.pi * (area / (perimeter ** 2)) if perimeter != 0 else 0

        # 6. Mean intensity
        mean_intensity = cv2.mean(image_gray, mask=combined_mask)[0]

        # 7. Std of intensity
        std_intensity = np.std(image_gray[combined_mask == 255])

        # 8. Compactness
        compactness = (perimeter ** 2) / (4 * np.pi * area) if area != 0 else 0

        # 9. Convexity
        if hull.points.size > 0 and len(hull.points) >= 2:
            hull_points = all_points[hull.vertices]
            hull_perimeter = cv2.arcLength(hull_points.astype(np.float32), True)
            convexity = perimeter / hull_perimeter if hull_perimeter != 0 else 0
        else:
            convexity = 0


    # 10. Curl
        curl = perimeter / (2 * np.sqrt(np.pi * area)) if area != 0 else 0

        # 11. Approximate volume (assuming spherical object)
        diameter = perimeter / np.pi
        volume = (4 / 3) * np.pi * (diameter / 2) ** 3

        properties = {
            "area": area,
            "perimeter": perimeter,
            "eccentricity": eccentricity,
            "solidity": solidity,
            "aspect_ratio": aspect_ratio,
            "circularity": circularity,
            "major_axis_length": major_axis_length,
            "minor_axis_length": minor_axis_length,
            "mean_intensity": mean_intensity,
            "std_intensity": std_intensity,
            "compactness": compactness,
            "convexity": convexity,
            "curl": curl,
            "volume": volume
        }

        return properties
