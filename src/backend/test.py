# test_data_manager.py
import os
import shutil
import unittest

from data_manager import DataManager
from objects.cluster import Cluster
from objects.sample import Sample
from objects.sample_class import SampleClass
from processor import Processor


class TestDataManager(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.test_dir = r"test-images"
        self.processor = Processor(model_name='mobilenetv3s')  # Initialize a Processor
        self.data_manager = DataManager(self.processor)

    def tearDown(self):
        """Clean up after test methods."""
        pass

    # Image Management Tests
    def test_create_image(self):
        image = self.data_manager.create_image("test_path.jpg")
        self.assertIsInstance(image, Sample)
        self.assertIn(image.id, self.data_manager.samples)

    def test_get_image(self):
        image1 = self.data_manager.create_image("test_path1.jpg")
        image2 = self.data_manager.get_image(image1.id)
        self.assertEqual(image1, image2)

    def test_get_image_paths(self):
        image1 = self.data_manager.create_image("test_path1.jpg")
        image2 = self.data_manager.create_image("test_path2.jpg")
        paths = self.data_manager.get_image_paths()
        self.assertIn("test_path1.jpg", paths)
        self.assertIn("test_path2.jpg", paths)

    def test_get_and_set_image_features(self):
        image = self.data_manager.create_image("test_path.jpg")
        features = [1.0, 2.0, 3.0]
        self.data_manager.set_image_features(image.id, features)
        self.assertEqual(self.data_manager.get_image_features()[0], features)

    # Cluster Management Tests
    def test_create_cluster(self):
        cluster = self.data_manager.create_cluster()
        self.assertIsInstance(cluster, Cluster)
        self.assertIn(cluster.id, self.data_manager.clusters)

    def test_get_cluster(self):
        cluster1 = self.data_manager.create_cluster()
        cluster2 = self.data_manager.get_cluster(cluster1.id)
        self.assertEqual(cluster1, cluster2)

    def test_add_and_remove_image_to_cluster(self):
        image = self.data_manager.create_image("test_path.jpg")
        cluster = self.data_manager.create_cluster()
        self.data_manager.add_image_to_cluster(image.id, cluster.id)
        self.assertIn(image, cluster.samples)
        self.data_manager.remove_image_from_cluster(image.id, cluster.id)
        self.assertNotIn(image, cluster.samples)

    def test_delete_cluster(self):
        image = self.data_manager.create_image("test_path.jpg")
        cluster = self.data_manager.create_cluster()
        self.data_manager.add_image_to_cluster(image.id, cluster.id)
        self.data_manager.delete_cluster(cluster.id)
        self.assertNotIn(cluster.id, self.data_manager.clusters)

    def test_merge_clusters(self):
        cluster1 = self.data_manager.create_cluster()
        cluster2 = self.data_manager.create_cluster()
        image1 = self.data_manager.create_image("test_path1.jpg")
        image2 = self.data_manager.create_image("test_path2.jpg")
        self.data_manager.add_image_to_cluster(image1.id, cluster1.id)
        self.data_manager.add_image_to_cluster(image2.id, cluster2.id)

        self.data_manager.merge_clusters([cluster1.id, cluster2.id])
        self.assertNotIn(cluster1.id, self.data_manager.clusters)
        self.assertNotIn(cluster2.id, self.data_manager.clusters)

        merged_cluster = list(self.data_manager.clusters.values())[0]
        self.assertIn(image1, merged_cluster.samples)
        self.assertIn(image2, merged_cluster.samples)

    # Class Management Tests
    def test_create_class(self):
        class_object = self.data_manager.create_class("Test Class", "#FF0000")
        self.assertIsInstance(class_object, SampleClass)
        self.assertIn(class_object.id, self.data_manager.classes)
        self.assertEqual(class_object.name, "Test Class")
        self.assertEqual(class_object.color, "#FF0000")

    def test_get_class(self):
        class1 = self.data_manager.create_class("Test Class 1", "#FF0000")
        class2 = self.data_manager.get_class(class1.id)
        self.assertEqual(class1, class2)

    def test_get_class_by_name(self):
        class1 = self.data_manager.create_class("Test Class 1", "#FF0000")
        class2 = self.data_manager.get_class_by_name("Test Class 1")
        self.assertEqual(class1, class2)

    def test_add_and_remove_image_to_class(self):
        image = self.data_manager.create_image("test_path.jpg")
        class_object = self.data_manager.create_class("Test Class", "#FF0000")
        self.data_manager.add_image_to_class(image.id, class_object.id)
        self.assertIn(image, class_object.samples)
        self.assertEqual(image.class_id, class_object.id)
        self.assertEqual(image.class_name, class_object.name)
        self.data_manager.remove_image_from_class(image.id, class_object.id)
        self.assertNotIn(image, class_object.samples)
        self.assertIsNone(image.class_id)
        self.assertIsNone(image.class_name)

    def test_delete_class(self):
        image = self.data_manager.create_image("test_path.jpg")
        class_object = self.data_manager.create_class("Test Class", "#FF0000")
        self.data_manager.add_image_to_class(image.id, class_object.id)
        self.data_manager.delete_class(class_object.id)
        self.assertNotIn(class_object.id, self.data_manager.classes)
        self.assertIsNone(image.class_id)
        self.assertIsNone(image.class_name)

    # Data Loading and Processing Tests
    def test_load_images_from_folder(self):
        self.data_manager.load_images_from_folder(self.test_dir)
        self.assertEqual(len(self.data_manager.samples), 4)

    def test_extract_and_set_features(self):
        self.data_manager.load_images_from_folder(self.test_dir)
        self.data_manager.extract_and_set_features()
        for image in self.data_manager.samples.values():
            self.assertIsNotNone(image.features)

    def test_perform_clustering(self):
        self.data_manager.load_images_from_folder(self.test_dir)
        self.data_manager.extract_and_set_features()
        self.assertEqual(len(self.data_manager.samples), 4)
        self.assertEqual(len(self.data_manager.clusters), 0)
        self.data_manager.perform_clustering(n_clusters=2)
        self.assertEqual(len(self.data_manager.clusters), 2)  # Check if 2 clusters were created

    # def test_split_cluster(self):
    #     self.data_manager.load_images_from_folder(self.test_dir)
    #     self.data_manager.extract_and_set_features()
    #     self.data_manager.perform_clustering(n_clusters=1)  # Start with one cluster
    #     original_cluster_id = list(self.data_manager.clusters.keys())[0]
    #     self.data_manager.split_cluster(original_cluster_id, n_clusters=2)
    #     self.assertEqual(len(self.data_manager.clusters), 2)  # Check if split into two clusters
    #     self.assertNotIn(original_cluster_id, self.data_manager.clusters)

# test_processor.py
import unittest
import os
import numpy as np
from app.processor import Processor


class TestProcessor(unittest.TestCase):
    def setUp(self):
        """Set up for test methods."""
        self.processor = Processor(model_name='mobilenetv3s')
        self.test_image_path = os.path.join(os.path.dirname(__file__), "test-images", "image_1.png")
        # Create a dummy test image
        open(self.test_image_path, 'a').close()

    def tearDown(self):
        """Clean up after test methods."""
        pass

    def test_get_model_path(self):
        self.assertTrue(os.path.exists(self.processor._get_model_path("mobilenetv3s")))
        with self.assertRaises(ValueError):
            self.processor._get_model_path("invalid_model")

    def test_get_model_dimension(self):
        self.assertEqual(self.processor._get_model_dimension("mobilenetv3s"), 1024)

    def test_extract_features(self):
        features = self.processor.extract_features(self.test_image_path)
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape[0], self.processor.feature_dim)

    def test_reduce_dimensions(self):
        features = np.random.rand(10, 1024)  # Example high-dimensional features
        reduced_features = self.processor.reduce_dimensions(features, n_components=5)
        self.assertEqual(reduced_features.shape[1], 5)

    def test_cluster_images(self):
        features = np.random.rand(10, 50)  # Example features (already reduced)
        cluster_labels = self.processor.cluster_images(features, n_clusters=3)
        self.assertEqual(len(cluster_labels), 10)
        self.assertTrue(all(0 <= label < 3 for label in cluster_labels))

    # def test_find_optimal_k(self):
    #     features = np.random.rand(100, 50)  # Example features for elbow method
    #     optimal_k = self.processor._find_optimal_k(features, max_clusters=10, n_iter=10, n_redo=1)
    #     self.assertTrue(1 <= optimal_k <= 10)

    def test_split_cluster(self):
        features = np.random.rand(10, 50)
        cluster_labels = [0, 0, 0, 0, 1, 1, 1, 2, 2, 2]
        new_labels = self.processor.split_cluster(
            features, cluster_labels.copy(), cluster_to_split=0, n_clusters=2
        )
        self.assertEqual(len(new_labels), 10)
        self.assertEqual(len(set(new_labels)), 4)  # Should have 4 unique clusters now

# test_session_manager.py
import unittest
import os
import shutil
from app.session_manager import SessionManager, Session

class TestSessionManager(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.sessions_file = "test_sessions.pickle"
        self.session_manager = SessionManager(self.sessions_file)

    def tearDown(self):
        """Clean up after test methods."""
        if os.path.exists(self.sessions_file):
            os.remove(self.sessions_file)

    def test_create_session(self):
        session = self.session_manager.create_session("Test Session", "/test/workdir", "/test/images")
        self.assertIsInstance(session, Session)
        self.assertIn(session.id, self.session_manager.sessions)

    def test_get_session(self):
        session1 = self.session_manager.create_session("Test Session", "/test/workdir", "/test/images")
        session2 = self.session_manager.get_session(session1.id)
        self.assertEqual(session1, session2)

    def test_list_sessions(self):
        session1 = self.session_manager.create_session("Test Session 1", "/test/workdir1", "/test/images1")
        session2 = self.session_manager.create_session("Test Session 2", "/test/workdir2", "/test/images2")
        sessions = self.session_manager.list_sessions()
        self.assertIn(session1, sessions)
        self.assertIn(session2, sessions)

    def test_delete_session(self):
        session = self.session_manager.create_session("Test Session", "/test/workdir", "/test/images")
        self.session_manager.delete_session(session.id)
        self.assertNotIn(session.id, self.session_manager.sessions)

    def test_open_session(self):
        session = self.session_manager.create_session("Test Session", "/test/workdir", "/test/images")
        opened_session = self.session_manager.open_session(session.id)
        self.assertEqual(session, opened_session)

    def test_save_and_load_sessions(self):
        session1 = self.session_manager.create_session("Test Session 1", "/test/workdir1", "/test/images1")
        session2 = self.session_manager.create_session("Test Session 2", "/test/workdir2", "/test/images2")

        # Simulate closing and reopening the session manager
        self.session_manager = SessionManager(self.sessions_file)
        loaded_sessions = self.session_manager.list_sessions()
        self.assertEqual(len(loaded_sessions), 2)  # Check if 2 sessions were loaded

        # Additional checks to make sure the data is correct (example)
        loaded_session1 = self.session_manager.get_session(session1.id)
        self.assertEqual(loaded_session1.name, "Test Session 1")
        self.assertEqual(loaded_session1.working_directory, "/test/workdir1")

# test_image_class.py
import unittest
from app.objects.image_class import ImageClass
from app.objects.image import Image

class TestImageClass(unittest.TestCase):

    def test_generate_random_color(self):
        class_object = SampleClass("123", "Test Class")
        color = class_object._generate_random_color()
        self.assertTrue(color.startswith("#"))  # Check if it's a hex color code
        self.assertEqual(len(color), 7)  # Check if it has the correct length

    def test_add_and_remove_image(self):
        class_object = SampleClass("123", "Test Class", color="#FF0000")
        image = Sample("456", "test_path.jpg")
        class_object.add_image(image)
        self.assertIn(image, class_object.samples)
        class_object.remove_image(image)
        self.assertNotIn(image, class_object.samples)

# test_cluster.py
import unittest
from app.objects.cluster import Cluster
from app.objects.image import Image

class TestCluster(unittest.TestCase):

    def test_add_and_remove_image(self):
        cluster = Cluster("123")
        image = Sample("456", "test_path.jpg")
        cluster.add_image(image)
        self.assertIn(image, cluster.samples)
        cluster.remove_image(image)
        self.assertNotIn(image, cluster.samples)

if __name__ == '__main__':
    unittest.main()