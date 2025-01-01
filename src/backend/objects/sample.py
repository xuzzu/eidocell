# backend/objects/sample.py

import json


class Sample:
    def __init__(self, id, path, features_file="", features=None, class_id=None, cluster_ids=None, mask_id=None):
        self.id = id
        self.path = path
        self.features_file = features_file  # Path to the features .npy file
        self.features = features if features else []
        self.class_id = class_id
        self.cluster_ids = cluster_ids if cluster_ids else set()
        self.mask_id = mask_id

    def set_features(self, features):
        self.features = features

    def set_mask_id(self, mask_id):
        self.mask_id = mask_id

    def add_cluster(self, cluster):
        self.cluster_ids.add(cluster.id)
        cluster.add_image(self)

    def remove_cluster(self, cluster):
        self.cluster_ids.discard(cluster.id)
        cluster.remove_image(self)

    def add_class(self, image_class):
        self.class_id = image_class.id
        image_class.add_image(self)

    def remove_class(self, image_class):
        if self.class_id == image_class.id:
            self.class_id = None
            image_class.remove_image(self)

    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path,
            "features_file": self.features_file,
            "features": self.features,
            "class_id": self.class_id,
            "cluster_ids": list(self.cluster_ids),
            "mask_id": self.mask_id
        }

    @staticmethod
    def from_dict(data):
        return Sample(
            id=data["id"],
            path=data["path"],
            features_file=data.get("features_file", ""),
            features=data.get("features", []),
            class_id=data.get("class_id"),
            cluster_ids=set(data.get("cluster_ids", [])),
            mask_id=data.get("mask_id", None)
        )
