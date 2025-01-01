# backend/data_manager.py
import csv

from datetime import datetime

import os
import json
import uuid
import random
import numpy as np
import shutil
import logging
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal, QThreadPool, QThread

import cv2

from backend.utils.file_utils import read_json, atomic_write
from backend.objects.cluster import Cluster
from backend.objects.sample import Sample
from backend.objects.sample_class import SampleClass
from backend.objects.mask import Mask
from backend.processor import Processor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Metadata file names
OBJECTS_METADATA_FILE = "objects_metadata.json"
FEATURES_METADATA_FILE = "features_metadata.json"
CLUSTERS_METADATA_FILE = "clusters_metadata.json"
CLASSES_METADATA_FILE = "classes_metadata.json"
MASKS_METADATA_FILE = "masks_metadata.json"

from PySide6.QtCore import QRunnable, Slot

class MetadataUpdateRunnable(QRunnable):
    def __init__(self, filename, data):
        super().__init__()
        self.filename = filename
        self.data = data

    @Slot()
    def run(self):
        atomic_write(self.filename, self.data)
        logging.info(f"Metadata saved: {self.filename}")

class DataManager(QObject):
    """
    Manages and stores image data, masks, features, clusters, and image classes.
    Implements the Observer pattern to notify listeners of changes.
    """

    class_added = Signal(str)
    class_updated = Signal(str)
    class_deleted = Signal(str)
    images_loaded = Signal()
    features_extracted = Signal()
    features_deleted = Signal(str)
    clustering_performed = Signal()
    cluster_split = Signal(str)
    mask_created = Signal(Mask)
    mask_deleted = Signal(str)

    def __init__(self,
                 session: Any,
                 settings: dict) -> None:
        super().__init__()
        self.session: Any = session  # Replace 'Any' with the actual type if available
        self.settings = settings
        self.samples: Dict[str, Sample] = {}
        self.clusters: Dict[str, Cluster] = {}
        self.classes: Dict[str, SampleClass] = {}
        self.masks: Dict[str, Mask] = {}
        self.features: Dict[str, str] = {}
        self.processor = Processor(model_name=self.settings['model'], execution_provider=self.settings['provider'])
        self.thread_pool = QThreadPool.globalInstance()
        self.metadata_threads = []

        # Load existing data from metadata
        self.load_images()
        self.load_masks()
        self.load_features()
        self.load_clusters()
        self.load_classes()

        # Create default class if it doesn't exist
        self._create_default_class()

    # --------------------
    # Metadata Helper Methods
    # --------------------

    def _load_metadata(self, filename: str) -> Dict[str, Any]:
        """
        Loads metadata from a JSON file.

        Args:
            filename (str): Name of the metadata file.

        Returns:
            Dict[str, Any]: Parsed JSON data.
        """
        path = os.path.join(self.session.metadata_directory, filename)
        try:
            return read_json(path)
        except FileNotFoundError:
            logging.warning(f"Metadata file not found: {path}. Returning empty data.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {path}: {e}")
            return {}

    def _save_metadata(self, filename: str, data: Dict[str, Any]) -> None:
        path = os.path.join(self.session.metadata_directory, filename)
        runnable = MetadataUpdateRunnable(path, data)
        self.thread_pool.start(runnable)

    # --------------------
    # Image Management
    # --------------------

    def load_images(self) -> None:
        """
        Loads images from objects_metadata.json.
        """
        objects_data = self._load_metadata(OBJECTS_METADATA_FILE)
        for obj in objects_data.get("objects", []):
            try:
                image = Sample.from_dict(obj)
                self.samples[image.id] = image
            except KeyError as e:
                logging.error(f"Missing key in image object: {e}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading image object: {e}")
        self.images_loaded.emit()
        self._update_objects_metadata()

        logging.info("Images loaded successfully.")

    def add_image(self, image_path: str, update_metadata: bool = True) -> Sample:
        """
        Adds a new image by referencing its path and optionally updates metadata.

        Args:
            image_path (str): The filesystem path to the image.
            update_metadata (bool): Whether to update the metadata files immediately.

        Returns:
            Sample: The newly created Image object.
        """
        image_id = str(uuid.uuid4())
        image = Sample(id=image_id, path=image_path)
        self.samples[image_id] = image
        if update_metadata:
            self._update_objects_metadata()
        return image

    def get_image(self, image_id: str) -> Optional[Sample]:
        """
        Returns the Image object with the given ID.

        Args:
            image_id (str): ID of the image.

        Returns:
            Optional[Sample]: Image object if found, else None.
        """
        return self.samples.get(image_id)

    def get_image_paths(self) -> List[str]:
        """
        Returns a list of paths to all images.

        Returns:
            List[str]: List of image paths.
        """
        return [image.path for image in self.samples.values()]

    def load_images_from_folder(self, folder_path: str) -> None:
        """
        Reads all image files from the specified folder and creates Image objects.

        Args:
            folder_path (str): Path to the folder containing image files.
        """
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        uncategorized_class = self.get_class_by_name("Uncategorized")
        images_without_class = []
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                image_path = os.path.join(folder_path, filename)
                image = self.add_image(image_path, update_metadata=False)
                images_without_class.append(image.id)
        self.add_images_to_class(images_without_class, uncategorized_class.id)
        self._update_objects_metadata()
        logging.info(f"Loaded images from {folder_path}.")

    # --------------------
    # Feature Management
    # --------------------

    def load_features(self) -> None:
        """
        Loads features from features_metadata.json.
        """
        features_data = self._load_metadata(FEATURES_METADATA_FILE)
        for feature_entry in features_data.get("features", []):
            image_id = feature_entry.get("image_id")
            feature_path = feature_entry.get("path")
            if not image_id or not feature_path:
                logging.warning(f"Invalid feature entry: {feature_entry}")
                continue
            if self._validate_path(feature_path):
                try:
                    features = np.load(feature_path)
                    image = self.samples.get(image_id)
                    if image:
                        image.features = features
                        self.features[image_id] = feature_path
                    else:
                        logging.warning(f"Image ID {image_id} not found for feature.")
                except IOError as e:
                    logging.error(f"Failed to load features from {feature_path}: {e}")
        logging.info("Features loaded successfully.")

    def _validate_path(self, path: str) -> bool:
        """
        Validates if the given path exists.
        """
        if not os.path.exists(path):
            logging.error(f"Path does not exist: {path}")
            return False
        return True

    def extract_and_set_features(self, image_id: str) -> None:
        """
        Extracts features for a given image and sets them.

        Args:
            image_id (str): ID of the image.
        """
        image = self.get_image(image_id)
        if not image:
            logging.error(f"Image ID {image_id} not found.")
            return
        try:
            features = self.processor.extract_features(image.path)
            # Save features as .npy file
            feature_file_name = f"{image_id}_features.npy"
            feature_file_path = os.path.join(self.session.features_directory, feature_file_name)
            np.save(feature_file_path, features)
            image.features = features
            self.features[image_id] = feature_file_path
            self.features_extracted.emit()
            logging.info(f"Features extracted for Image ID {image_id}.")
        except Exception as e:
            logging.error(f"Error extracting features for Image ID {image_id}: {e}")

    def delete_features(self, image_id: str) -> None:
        """
        Deletes the feature file associated with an image.

        Args:
            image_id (str): ID of the image whose features are to be deleted.
        """
        feature_path = self.features.pop(image_id, None)
        if feature_path and self._validate_path(feature_path):
            try:
                os.remove(feature_path)
                self._update_features_metadata()
                self.features_deleted.emit(image_id)
                logging.info(f"Features for Image ID {image_id} deleted successfully.")
            except IOError as e:
                logging.error(f"Error deleting features for Image ID {image_id}: {e}")
        else:
            logging.warning(f"No features found for Image ID {image_id}.")

    def _update_features_metadata(self) -> None:
        """
        Updates features_metadata.json with current features.
        """
        features_data = {
            "features": [
                {"image_id": image_id, "path": path}
                for image_id, path in self.features.items()
            ]
        }
        self._save_metadata(FEATURES_METADATA_FILE, features_data)

    def get_image_features(self, image_id: str) -> Optional[np.ndarray]:
        """
        Loads and returns the feature vector for a given image.

        Args:
            image_id (str): ID of the image.

        Returns:
            Optional[np.ndarray]: Feature vector, or None if not found.
        """
        feature_path = self.features.get(image_id)
        if feature_path and self._validate_path(feature_path):
            try:
                return np.load(feature_path)
            except IOError as e:
                logging.error(f"Failed to load features from {feature_path}: {e}")
        else:
            logging.warning(f"Feature file not found for Image ID {image_id}.")
        return None

    # --------------------
    # Cluster Management
    # --------------------

    def load_clusters(self) -> None:
        """
        Loads clusters from clusters_metadata.json.
        """
        clusters_data = self._load_metadata(CLUSTERS_METADATA_FILE)
        for cluster_entry in clusters_data.get("clusters", []):
            try:
                cluster = Cluster.from_dict(cluster_entry)
                image_ids = cluster_entry.get("images", [])
                for image_id in image_ids:
                    image = self.samples.get(image_id)
                    if image:
                        cluster.add_image(image)
                self.clusters[cluster.id] = cluster
            except KeyError as e:
                logging.error(f"Missing key in cluster entry: {e}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error in clusters: {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading cluster: {e}")
        logging.info("Clusters loaded successfully.")

    def create_cluster(self) -> Cluster:
        """
        Creates a new Cluster object with a random color.

        Returns:
            Cluster: The newly created Cluster object.
        """
        cluster_id = str(uuid.uuid4())
        color = self._generate_random_color()
        cluster = Cluster(id=cluster_id, color=color)
        self.clusters[cluster_id] = cluster
        logging.info(f"Cluster created with ID {cluster.id} and color {cluster.color}")
        return cluster

    def _generate_random_color(self) -> str:
        """
        Generates a random hex color string.

        Returns:
            str: Hex color code.
        """
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def get_cluster(self, cluster_id: str) -> Optional[Cluster]:
        """
        Returns the Cluster object with the given ID.

        Args:
            cluster_id (str): ID of the cluster.

        Returns:
            Optional[Cluster]: Cluster object if found, else None.
        """
        return self.clusters.get(cluster_id)

    def add_images_to_cluster(self, image_ids: List[str], cluster_id: str) -> None:
        """
        Adds images to a specified cluster.

        Args:
            image_ids (List[str]): List of image IDs to add.
            cluster_id (str): ID of the cluster.
        """
        cluster = self.get_cluster(cluster_id)
        if not cluster:
            logging.error(f"Cluster ID {cluster_id} does not exist.")
            return

        for image_id in image_ids:
            image = self.samples.get(image_id)
            if image:
                cluster.add_image(image)
            else:
                logging.warning(f"Image ID {image_id} does not exist.")

        logging.info(f"Added {len(image_ids)} images to Cluster ID {cluster_id}.")

    def remove_images_from_cluster(self, image_ids: List[str], cluster_id: str) -> None:
        """
        Removes images from a specified cluster.

        Args:
            image_ids (List[str]): List of image IDs to remove.
            cluster_id (str): ID of the cluster.
        """
        cluster = self.get_cluster(cluster_id)
        if not cluster:
            logging.error(f"Cluster ID {cluster_id} does not exist.")
            return

        for image_id in image_ids:
            image = self.samples.get(image_id)
            if image:
                cluster.remove_image(image)
            else:
                logging.warning(f"Image ID {image_id} does not exist.")

        logging.info(f"Removed {len(image_ids)} images from Cluster ID {cluster_id}.")

    def delete_cluster(self, cluster_id: str) -> None:
        """
        Deletes a cluster and removes it from all associated images.

        Args:
            cluster_id (str): ID of the cluster to delete.
        """
        cluster = self.clusters.pop(cluster_id, None)
        if cluster:
            # Remove cluster reference from images
            for image in cluster.samples.copy():
                image.remove_cluster(cluster)
            logging.info(f"Cluster {cluster_id} deleted successfully.")
        else:
            logging.warning(f"Cluster ID {cluster_id} does not exist.")

    def merge_clusters(self, cluster_ids: List[str]) -> Optional[Cluster]:
        """
        Merges multiple clusters into a new cluster.

        Args:
            cluster_ids (List[str]): List of cluster IDs to merge.

        Returns:
            Optional[Cluster]: The newly created merged cluster, or None if merging failed.
        """
        if len(cluster_ids) < 2:
            logging.error("Need at least two clusters to merge.")
            return None

        new_cluster = self.create_cluster()
        for cluster_id in cluster_ids:
            cluster = self.get_cluster(cluster_id)
            if cluster:
                image_ids = [image.id for image in cluster.samples]
                self.add_images_to_cluster(image_ids, new_cluster.id)
                self.delete_cluster(cluster_id)
            else:
                logging.warning(f"Cluster ID {cluster_id} does not exist and cannot be merged.")

        logging.info(f"Merged clusters {cluster_ids} into new Cluster ID {new_cluster.id}.")
        return new_cluster

    def _update_clusters_metadata(self) -> None:
        """
        Updates clusters_metadata.json with current clusters.
        """
        clusters_data = {
            "clusters": [
                {
                    "id": cluster.id,
                    "color": cluster.color,
                    "images": [image.id for image in cluster.samples]
                }
                for cluster in self.clusters.values()
            ]
        }
        self._save_metadata(CLUSTERS_METADATA_FILE, clusters_data)

    # --------------------
    # Class Management
    # --------------------

    def load_classes(self) -> None:
        """
        Loads classes from classes_metadata.json.
        """
        classes_data = self._load_metadata(CLASSES_METADATA_FILE)
        for class_entry in classes_data.get("classes", []):
            try:
                image_class = SampleClass.from_dict(class_entry)
                image_ids = class_entry.get("images", [])
                for image_id in image_ids:
                    image = self.samples.get(image_id)
                    if image:
                        image_class.add_image(image)
                self.classes[image_class.id] = image_class
            except KeyError as e:
                logging.error(f"Missing key in class entry: {e}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error in classes: {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading image class: {e}")
        logging.info("Classes loaded successfully.")

    def create_class(self, name: str, color: Optional[str] = None) -> SampleClass:
        """
        Creates a new ImageClass object.

        Args:
            name (str): Name of the class.
            color (Optional[str]): Hex color code for the class.

        Returns:
            SampleClass: The newly created ImageClass object.
        """
        class_id = str(uuid.uuid4())
        image_class = SampleClass(id=class_id, name=name, color=color or self._generate_random_color())
        self.classes[class_id] = image_class
        self.class_added.emit(image_class)
        self._update_classes_metadata()
        logging.info(f"Class created: {name} with ID {class_id} and color {image_class.color}")
        return image_class

    def get_class(self, class_id: str) -> Optional[SampleClass]:
        """
        Returns the ImageClass object with the given ID.

        Args:
            class_id (str): ID of the class.

        Returns:
            Optional[SampleClass]: ImageClass object if found, else None.
        """
        return self.classes.get(class_id)

    def get_class_by_name(self, class_name: str) -> Optional[SampleClass]:
        """
        Returns the ImageClass object with the given name.

        Args:
            class_name (str): Name of the class.

        Returns:
            Optional[SampleClass]: ImageClass object if found, else None.
        """
        for image_class in self.classes.values():
            if image_class.name.lower() == class_name.lower():
                return image_class
        return None

    def add_images_to_class(self, image_ids: List[str], class_id: str) -> None:
        """
        Adds images to a specified class.

        Args:
            image_ids (List[str]): List of image IDs to add.
            class_id (str): ID of the class.
        """
        image_class = self.get_class(class_id)
        if not image_class:
            logging.error(f"Class ID {class_id} does not exist.")
            return

        for image_id in image_ids:
            image = self.samples.get(image_id)
            if image:
                image_class.add_image(image)
            else:
                logging.warning(f"Image ID {image_id} does not exist.")

        self._update_classes_metadata()
        self._update_objects_metadata()
        self.class_updated.emit(image_class)
        logging.info(f"Added {len(image_ids)} images to Class ID {class_id}.")

    def remove_images_from_class(self, image_ids: List[str], class_id: str) -> None:
        """
        Removes images from a specified class.

        Args:
            image_ids (List[str]): List of image IDs to remove.
            class_id (str): ID of the class.
        """
        image_class = self.get_class(class_id)
        if not image_class:
            logging.error(f"Class ID {class_id} does not exist.")
            return

        for image_id in image_ids:
            image = self.samples.get(image_id)
            if image:
                image_class.remove_image(image)
            else:
                logging.warning(f"Image ID {image_id} does not exist.")

        self._update_classes_metadata()
        self._update_objects_metadata()
        self.class_updated.emit(image_class)
        logging.info(f"Removed {len(image_ids)} images from Class ID {class_id}.")

    def delete_class(self, class_id: str) -> None:
        """
        Deletes a class and removes it from all associated images.

        Args:
            class_id (str): ID of the class to delete.
        """
        image_class = self.classes.pop(class_id, None)
        if image_class:
            # Remove class reference from images
            for image in image_class.samples.copy():
                image.remove_class(image_class)
            self._update_classes_metadata()
            self._update_objects_metadata()
            self.class_deleted.emit(class_id)
            logging.info(f"Class {class_id} deleted successfully.")
        else:
            logging.warning(f"Class ID {class_id} does not exist.")

    def _update_classes_metadata(self) -> None:
        """
        Updates classes_metadata.json with current classes.
        """
        classes_data = {
            "classes": [
                {
                    "id": image_class.id,
                    "name": image_class.name,
                    "color": image_class.color,
                    "images": [image.id for image in image_class.samples]
                }
                for image_class in self.classes.values()
            ]
        }
        self._save_metadata(CLASSES_METADATA_FILE, classes_data)

    # --------------------
    # Mask Management
    # --------------------

    def load_masks(self) -> None:
        """
        Loads masks from masks_metadata.json, including mask data and masked image paths.
        """
        masks_data = self._load_metadata(MASKS_METADATA_FILE)
        for mask_entry in masks_data.get("masks", []):
            try:
                mask = Mask.from_dict(mask_entry)
                if self._validate_path(mask.path):
                    mask.mask_data = np.load(mask.path)  # Load mask data from .npy file
                    if mask.masked_image_path:
                        mask.masked_image = cv2.imread(mask.masked_image_path)
                    self.masks[mask.id] = mask
            except KeyError as e:
                logging.error(f"Missing key in mask entry: {e}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error in masks: {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading mask object: {e}")
        logging.info("Masks loaded successfully.")

    def create_mask(
            self,
            image_id: str,
            mask_data: np.ndarray,
            attributes: Optional[Dict[str, Any]] = None,
            masked_image_path: Optional[str] = None,
            masked_image: Optional[Any] = None
    ) -> Optional[Mask]:
        """
        Creates a new Mask object, saves it as a .npy file, and updates metadata.

        Args:
            image_id (str): ID of the original image.
            mask_data (np.ndarray): The pixel data of the mask.
            attributes (Optional[Dict[str, Any]]): Additional mask attributes.
            masked_image_path (Optional[str]): Path to the masked image file.
            masked_image (Optional[Any]): Masked image to display in the gallery.

        Returns:
            Optional[Mask]: The newly created Mask object, or None if creation failed.
        """
        if not self.get_image(image_id):
            logging.error(f"Error: Image ID {image_id} does not exist.")
            return None

        mask_id = str(uuid.uuid4())
        mask_file_name = f"mask_{mask_id}.npy"
        mask_file_path = os.path.join(self.session.masks_directory, mask_file_name)
        try:
            np.save(mask_file_path, mask_data)
        except IOError as e:
            logging.error(f"Failed to save mask data to {mask_file_path}: {e}")
            return None

        mask = Mask(
            id=mask_id,
            image_id=image_id,
            path=mask_file_path,
            attributes=attributes or {},
            masked_image_path=masked_image_path,
            masked_image=masked_image
        )

        self.masks[mask_id] = mask
        self.mask_created.emit(mask)
        logging.info(f"Mask created for Image ID {image_id} with Mask ID {mask_id}.")
        return mask

    def delete_mask(self, mask_id: str) -> None:
        """
        Deletes a mask by its ID, removes the file, and updates metadata.

        Args:
            mask_id (str): ID of the mask to delete.
        """
        mask = self.masks.pop(mask_id, None)
        if mask:
            try:
                if self._validate_path(mask.path):
                    os.remove(mask.path)
                self._update_masks_metadata()
                self.mask_deleted.emit(mask_id)
                logging.info(f"Mask {mask_id} deleted successfully.")
            except IOError as e:
                logging.error(f"Error deleting mask {mask_id}: {e}")
        else:
            logging.warning(f"Mask ID {mask_id} not found.")

    def _update_masks_metadata(self) -> None:
        """
        Updates masks_metadata.json with current masks.
        """
        masks_data = {
            "masks": [
                mask.to_dict()
                for mask in self.masks.values()
            ]
        }
        self._save_metadata(MASKS_METADATA_FILE, masks_data)

    def get_mask(self, mask_id: str) -> Optional[Mask]:
        """
        Returns the Mask object with the given ID.

        Args:
            mask_id (str): ID of the mask.

        Returns:
            Optional[Mask]: Mask object if found, else None.
        """
        return self.masks.get(mask_id)

    # --------------------
    # Clustering
    # --------------------

    def perform_clustering(
            self,
            n_clusters: int = 10,
            n_iter: int = 1000,
            n_redo: int = 1,
            find_k_elbow: bool = False
    ) -> None:
        """
        Performs clustering on the images.

        Args:
            n_clusters (int): Number of clusters.
            n_iter (int): Number of iterations for KMeans.
            n_redo (int): Number of KMeans runs with different initializations.
            find_k_elbow (bool): Whether to use the elbow method to find optimal k.
        """
        features = []
        image_ids = []
        for image_id, feature_path in self.features.items():
            if self._validate_path(feature_path):
                feature = np.load(feature_path)
                features.append(feature)
                image_ids.append(image_id)
            else:
                logging.warning(f"Feature file missing for Image ID {image_id}: {feature_path}")

        if not features:
            logging.error("No image features available for clustering.")
            return

        features = np.array(features, dtype=np.float32)

        try:
            reduced_features = self.processor.reduce_dimensions(features)  # Reduce dimensions
            cluster_labels = self.processor.cluster_images(
                reduced_features, n_clusters, n_iter, n_redo, find_k_elbow
            )
        except Exception as e:
            logging.error(f"Error during clustering: {e}")
            return

        # Create a mapping from label to cluster
        label_to_cluster: Dict[int, Cluster] = {}
        unique_labels = set(cluster_labels)
        for label in unique_labels:
            label_to_cluster[label] = self.create_cluster()

        # Assign images to clusters
        for i, image_id in enumerate(image_ids):
            label = cluster_labels[i]
            cluster = label_to_cluster[label]
            image = self.samples.get(image_id)
            if image:
                cluster.add_image(image)

        self.clustering_performed.emit()
        logging.info("Clustering completed successfully.")

    def split_cluster(
            self,
            cluster_id: str,
            n_clusters: int = 2,
            n_iter: int = 300,
            n_redo: int = 5
    ) -> None:
        """
        Splits a cluster into sub-clusters.

        Args:
            cluster_id (str): ID of the cluster to split.
            n_clusters (int): Number of sub-clusters to create.
            n_iter (int): Number of iterations for KMeans.
            n_redo (int): Number of KMeans runs with different initializations.
        """
        cluster = self.get_cluster(cluster_id)
        if not cluster:
            logging.error(f"Error: Cluster ID {cluster_id} not found.")
            return

        cluster_images = list(cluster.samples)
        if len(cluster_images) < n_clusters:
            logging.error(f"Not enough images in cluster {cluster_id} to split into {n_clusters} sub-clusters.")
            return

        # Extract features for the cluster
        features = []
        image_ids = []
        for image in cluster_images:
            feature_path = self.features.get(image.id)
            if self._validate_path(feature_path):
                feature = np.load(feature_path)
                features.append(feature)
                image_ids.append(image.id)
            else:
                logging.warning(f"Feature file missing for Image ID {image.id}: {feature_path}")

        if not features:
            logging.error("No features available for splitting the cluster.")
            return

        features = np.array(features, dtype=np.float32)

        try:
            reduced_features = self.processor.reduce_dimensions(features)
            new_labels = self.processor.cluster_images(
                reduced_features, n_clusters, n_iter, n_redo, find_k_elbow=False
            )
        except Exception as e:
            logging.error(f"Error during cluster splitting: {e}")
            return

        # Create new clusters and assign images
        new_clusters: Dict[int, Cluster] = {}
        for i, label in enumerate(new_labels):
            if label not in new_clusters:
                new_clusters[label] = self.create_cluster()
            image = self.samples.get(image_ids[i])
            if image:
                new_clusters[label].add_image(image)

        # Delete the original cluster
        self.delete_cluster(cluster_id)

        logging.info(f"Cluster {cluster_id} split into {n_clusters} sub-clusters successfully.")

    # --------------------
    # Utility Methods
    # --------------------

    def _create_default_class(self) -> None:
        """
        Creates the default "Uncategorized" class if it doesn't exist.
        """
        if self.get_class_by_name("Uncategorized") is None:
            self.create_class("Uncategorized", color="#A9A9A9")
            logging.info("Default 'Uncategorized' class created.")

    # --------------------
    # Additional Methods
    # --------------------

    def delete_image(self, image_id: str) -> None:
        """
        Deletes an image and all associated data (features, masks, cluster/class associations).

        Args:
            image_id (str): ID of the image to delete.
        """
        image = self.samples.pop(image_id, None)
        if image:
            # Delete associated feature
            self.delete_features(image_id)

            # Remove image from clusters
            for cluster in self.clusters.values():
                if image in cluster.samples:
                    cluster.remove_image(image)

            # Remove image from classes
            class_id = image.class_id
            if class_id:
                image_class = self.get_class(class_id)
                if image_class:
                    image_class.remove_image(image)
                    self.class_updated.emit(image_class)

            # Remove associated masks
            masks_to_delete = [mask_id for mask_id, mask in self.masks.items() if mask.image_id == image_id]
            for mask_id in masks_to_delete:
                self.delete_mask(mask_id)

            self._update_objects_metadata()
            logging.info(f"Image {image_id} and all associated data deleted successfully.")
        else:
            logging.warning(f"Image ID {image_id} does not exist.")

    def _update_objects_metadata(self) -> None:
        """
        Updates objects_metadata.json with current images, including feature references.
        """
        objects_data = {
            "objects": [
                {
                    "id": image.id,
                    "path": image.path,
                    "features_file": self.features.get(image.id, ""),
                    "class_id": image.class_id,
                    "cluster_ids": list(image.cluster_ids),
                    "mask_id": image.mask_id
                }
                for image in self.samples.values()
            ]
        }
        self._save_metadata(OBJECTS_METADATA_FILE, objects_data)
        logging.info("Objects metadata updated successfully.")


    def export_data(self, params: dict) -> None:
        include_masks = params.get("include_masks", False)
        include_clusters = params.get("include_clusters", False)
        include_params = params.get("include_params", False)
        include_charts = params.get("include_charts", False)
        export_folder_path = params.get("export_folder_path", "")

        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        session_name = self.session.name
        export_folder_name = f"{session_name} [EXPORT - {timestamp}]"
        export_folder_path = os.path.normpath(export_folder_path)  # Normalize path separators
        full_export_path = os.path.join(export_folder_path, export_folder_name)
        full_export_path = os.path.normpath(full_export_path)  # Normalize again after joining

        os.makedirs(full_export_path, exist_ok=True)  # Create the main export folder

        # 1. Export Classes
        classes_folder = os.path.join(full_export_path, "Classes")
        os.makedirs(classes_folder, exist_ok=True)
        for class_id, class_object in self.classes.items():
            class_folder = os.path.join(classes_folder, class_object.name)
            os.makedirs(class_folder, exist_ok=True)
            for image in class_object.samples:
                shutil.copy2(image.path, class_folder)  # Copy image to class folder

        # 2. Export Masks (if selected)
        if include_masks:
            masks_folder = os.path.join(full_export_path, "Masks")
            os.makedirs(masks_folder, exist_ok=True)
            for mask in self.masks.values():
                mask_image_path = os.path.join(masks_folder, f"{mask.image_id}.npy")
                shutil.copy2(mask.path, mask_image_path)  # Copy mask file

        # 3. Export Clusters (if selected)
        if include_clusters:
            clusters_folder = os.path.join(full_export_path, "Clusters")
            os.makedirs(clusters_folder, exist_ok=True)
            for cluster_id, cluster in self.clusters.items():
                cluster_folder = os.path.join(clusters_folder, cluster_id[:8])
                os.makedirs(cluster_folder, exist_ok=True)
                for image in cluster.samples:
                    shutil.copy2(image.path, cluster_folder)

        # 4. Export Calculated Parameters (if selected)
        if include_params:
            print("Exporting calculated parameters...")
            params_folder = os.path.join(full_export_path, "Calculated Parameters")
            os.makedirs(params_folder, exist_ok=True)
            params_file = os.path.join(params_folder, "parameters.csv")
            with open(params_file, 'w', newline='') as csvfile:
                # Adjust fieldnames based on available mask attributes
                # Assuming all masks have the same set of attributes
                mask_example = next(iter(self.masks.values()), None)
                if mask_example:
                    attribute_keys = list(mask_example.attributes.keys())
                else:
                    attribute_keys = []
                fieldnames = ['Image Path', 'Class'] + attribute_keys
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for image in self.samples.values():
                    row = {'Image Path': image.path, 'Class': self.get_class(image.class_id).name if image.class_id else "Uncategorized"}
                    mask = next((mask for mask in self.masks.values() if mask.image_id == image.id), None)
                    if mask:
                        row.update(mask.attributes)
                    else:
                        for key in attribute_keys:
                            row[key] = ""
                    writer.writerow(row)

        if include_charts:
            print("Exporting charts...")
            charts_folder = os.path.join(full_export_path, "Charts")
            os.makedirs(charts_folder, exist_ok=True)

            for filename in os.listdir("temp"):
                if filename.startswith("plot_") and (filename.endswith(".png") or filename.endswith(".html")):
                    source_path = os.path.join("temp", filename)
                    destination_path = os.path.join(charts_folder, filename)
                    shutil.copy2(source_path, destination_path)
