# backend/objects/session.py

import os
import json
from datetime import datetime


class Session:
    def __init__(self,
                 id: str,
                 name: str,
                 creation_date: str,
                 last_opening_date: str,
                 images_directory: str,
                 session_folder: str,
                 masks_directory: str,
                 metadata_directory: str,
                 features_directory: str,
                 masked_images_directory: str,
                 processor_model: str):
        self.id = id
        self.name = name
        self.creation_date = creation_date
        self.last_opening_date = last_opening_date
        self.images_directory = images_directory
        self.session_folder = session_folder
        self.masks_directory = masks_directory
        self.metadata_directory = metadata_directory
        self.features_directory = features_directory
        self.masked_images_directory = masked_images_directory
        self.processor_model = processor_model

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "creation_date": self.creation_date,
            "last_opening_date": self.last_opening_date,
            "images_directory": self.images_directory,
            "session_folder": self.session_folder,
            "masks_directory": self.masks_directory,
            "metadata_directory": self.metadata_directory,
            "features_directory": self.features_directory,
            "masked_images_directory": self.masked_images_directory,
            "processor_model": self.processor_model
        }

    @staticmethod
    def from_dict(data):
        required_keys = [
            "id",
            "name",
            "creation_date",
            "last_opening_date",
            "images_directory",
            "session_folder",
            "masks_directory",
            "metadata_directory",
            "features_directory",
            "masked_images_directory",
            "processor_model"
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing key {key} in session data.")

        return Session(
            id=data["id"],
            name=data["name"],
            creation_date=data["creation_date"],
            last_opening_date=data["last_opening_date"],
            images_directory=data["images_directory"],
            session_folder=data["session_folder"],
            masks_directory=data["masks_directory"],
            metadata_directory=data["metadata_directory"],
            features_directory=data["features_directory"],
            masked_images_directory=data["masked_images_directory"],
            processor_model=data["processor_model"]
        )

    @property
    def session_info_path(self):
        """
        Returns the path to the session_info.json file.
        """
        return os.path.join(self.session_folder, "session_info.json")
