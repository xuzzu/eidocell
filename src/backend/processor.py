import cv2
import faiss
import numpy as np
import onnxruntime as ort
import os
from PIL import Image
from PySide6.QtCore import Signal, QObject
from kneed import KneeLocator
from sklearn.decomposition import PCA
from tqdm import tqdm


class Processor:
    """
    Handles image feature extraction, dimensionality reduction, and clustering.
    Works independently of the DataManager.
    """

    def __init__(self, model_name, execution_provider='CPUExecutionProvider'):
        """
        Initializes the Processor.

        Args:
            model_name (str): Name of the feature extraction model (e.g., 'dinov2s').
            execution_provider (str, optional): ONNX Runtime execution provider.
                                                  Defaults to 'CPUExecutionProvider'.
        """
        super().__init__()
        self.model_name = model_name
        self.model_path = self._get_model_path(model_name)
        self.feature_dim = self._get_model_dimension(model_name)
        self.execution_provider = execution_provider
        self.ort_session = None
        self._initialize_ort_session()

    def _get_model_path(self, model_name):
        """
        Gets the path to the ONNX model file based on the model name.

        Args:
            model_name (str): Name of the model.

        Returns:
            str: Path to the model file.
        Raises:
            ValueError: If the model name is invalid.
            FileNotFoundError: If the model file is not found.
        """
        model_dir = os.path.join(os.path.dirname(__file__), "resources")  # Use relative path
        model_filename = {
            'dinov2s': 'dinov2_small.onnx',
            'dinov2b': 'dinov2_base.onnx',
            'mobilenetv3l': 'mobilenetv3_large_extractor.onnx',
            'mobilenetv3s': 'mobilenetv3_small_extractor.onnx',
            'hiera_huge': 'hiera_huge.onnx'
        }.get(model_name.lower())

        if model_filename is None:
            raise ValueError(f"Invalid model name: {model_name}")

        model_path = os.path.join(model_dir, model_filename)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

        return model_path

    def _get_model_dimension(self, model_name):
        """
        Gets the output feature vector dimensionality for the given model.

        Args:
            model_name (str): Name of the model.

        Returns:
            int: Dimensionality of the feature vector.
        """
        return {
            'dinov2s': 384,
            'dinov2b': 384,
            'hiera_huge': 384,
            'mobilenetv3s': 1024,
            'mobilenetv3l': 1280,
        }.get(model_name.lower())

    def _initialize_ort_session(self):
        """Initializes the ONNX Runtime inference session."""
        available_providers = ort.get_available_providers()
        if self.execution_provider in available_providers:
            self.ort_session = ort.InferenceSession(
                self.model_path, providers=[self.execution_provider]
            )
        else:
            print(
                f"Warning: {self.execution_provider} not available. "
                f"Falling back to CPUExecutionProvider."
            )
            self.ort_session = ort.InferenceSession(
                self.model_path, providers=['CPUExecutionProvider']
            )

    def extract_features(self, image_path):
        """
        Extracts features from an image using the ONNX model.

        Args:
            image_path (str): Path to the image file.

        Returns:
            np.ndarray: Feature vector for the image.
        """
        image = self._load_and_preprocess_image(image_path)
        if image is None:
            print(f"Error: Could not read image data for {image_path}")
            return None

        input_name = self.ort_session.get_inputs()[0].name

        # Determine target size based on the model
        if 'mobilevit' in self.model_name:
            target_size = (256, 256)
        else:
            target_size = (224, 224)
        image = cv2.resize(image, target_size)
        image = image.transpose(2, 0, 1).astype(np.float32) / 255.0
        image = image[np.newaxis, ...]  # Add batch dimension

        outputs = self.ort_session.run(None, {input_name: image})
        feature_vector = outputs[0]
        return feature_vector.reshape(-1)

    def _load_and_preprocess_image(self, image_path):
        """
        Loads an image from the given path and preprocesses it.

        Args:
            image_path (str): Path to the image file.

        Returns:
            np.ndarray: The loaded image as a NumPy array, or None if loading fails.
        """
        try:
            image = Image.open(image_path)
            image = np.array(image)
            if image.ndim == 2:  # Grayscale
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            return image
        except Exception as e:
            print(f"Error reading image {image_path}: {e}")
            return None

    def reduce_dimensions(self, features, n_components=0.95):
        """
        Reduces the dimensionality of the features using PCA.

        Args:
            features (np.ndarray): Feature vectors (NumPy array).
            n_components (int or float, optional): Number of components to keep
                                                   (or variance explained).
                                                   Defaults to 0.95.

        Returns:
            np.ndarray: Reduced feature vectors.
        """
        print(f"Original feature shape: {features.shape}")
        reducer = PCA(n_components=n_components)
        reduced_features = reducer.fit_transform(features)
        print(f"Reduced feature shape: {reduced_features.shape}")
        return reduced_features

    def cluster_images(self, features, n_clusters=10, n_iter=1000, n_redo=1, find_k_elbow=False):
        """
        Clusters image features using Faiss KMeans.

        Args:
            features (np.ndarray): Feature vectors of the images.
            n_clusters (int): Number of clusters.
            n_iter (int): Number of iterations for KMeans.
            n_redo (int): Number of KMeans runs with different initializations.
            find_k_elbow (bool): Whether to use the elbow method to find optimal k.

        Returns:
            list: A list of cluster assignments for each image.
        """
        if find_k_elbow:
            n_clusters = self._find_optimal_k(features, n_clusters, n_iter, n_redo)

        kmeans = faiss.Kmeans(
            features.shape[1], n_clusters, niter=n_iter, nredo=n_redo, verbose=True
        )
        kmeans.train(features)
        _, cluster_labels = kmeans.index.search(features, 1)
        return cluster_labels.reshape(-1).tolist()  # Return as a list

    def _find_optimal_k(self, features, max_clusters, n_iter, n_redo):
        """
        Finds the optimal number of clusters (K) using the elbow method.

        Args:
            features (np.ndarray): Reduced feature vectors.
            max_clusters (int): Max number of clusters to try.
            n_iter (int): Number of iterations for KMeans.
            n_redo (int): Number of KMeans runs with different initializations.

        Returns:
            int: The optimal K value.
        """
        distortions = []
        K_range = range(1, max_clusters + 1)
        for k in tqdm(K_range, desc="Finding Optimal K"):
            kmeans = faiss.Kmeans(
                features.shape[1],
                k,
                niter=n_iter,
                nredo=n_redo,
                verbose=False
            )
            kmeans.train(features)
            distortions.append(kmeans.obj[-1])

        knee = KneeLocator(
            K_range, distortions, curve="convex", direction="decreasing"
        )
        optimal_k = knee.elbow
        print(f"Optimal K found using elbow method: {optimal_k}")
        return optimal_k

    def split_cluster(self, features, n_clusters=2, n_iter=300, n_redo=5):
        """
        Splits a specified cluster into sub-clusters.

        Args:
            features (np.ndarray): Feature vectors of the images.
            n_clusters (int): Number of sub-clusters to create.
            n_iter (int): Number of iterations for KMeans.
            n_redo (int): Number of KMeans runs with different initializations.

        Returns:
            list: Updated cluster labels with the split cluster divided.
        """

        kmeans = faiss.Kmeans(
            features.shape[1],
            n_clusters,
            niter=n_iter,
            nredo=n_redo,
            verbose=True
        )

        kmeans.train(features)
        _, new_labels = kmeans.index.search(features, 1)
        new_labels = new_labels.reshape(-1)

        return new_labels.tolist()

