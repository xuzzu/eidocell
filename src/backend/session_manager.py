# backend/session_manager.py

import uuid
import os
import shutil
from datetime import datetime

from backend.objects.session import Session
from backend.utils.file_utils import atomic_write, read_json


class SessionManager:
    """
    Manages analysis sessions, including loading, saving, and creation.
    Operates independently from the UI.
    """

    def __init__(self, sessions_dir="sessions"):
        """
        Initializes the SessionManager.

        Args:
            sessions_dir (str, optional): Directory where session folders are stored. Defaults to "sessions".
        """
        self.sessions_dir = sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)

        self.index_file = os.path.join(os.getcwd(), "sessions_index.json")
        self.sessions = {}  # {session_id: Session}
        self._load_sessions_index()

    def _load_sessions_index(self):
        """
        Loads the sessions index from sessions_index.json.
        Initializes the index file if it does not exist.
        """
        if not os.path.exists(self.index_file):
            atomic_write(self.index_file, {"sessions": []})
            print(f"Created new sessions index file at {self.index_file}")

        data = read_json(self.index_file)
        for session_data in data.get("sessions", []):
            session = self._load_session(session_data["path"])
            if session:
                self.sessions[session.id] = session

    def _save_sessions_index(self):
        """
        Saves the current sessions to sessions_index.json.
        """
        data = {"sessions": []}
        for session in self.sessions.values():
            data["sessions"].append({
                "id": session.id,
                "name": session.name,
                "creation_date": session.creation_date,
                "last_opened": session.last_opening_date,
                "path": session.session_folder
            })
        atomic_write(self.index_file, data)
        print(f"Sessions index updated at {self.index_file}")

    def _load_session(self, session_folder):
        """
        Loads a session from its session_info.json file.

        Args:
            session_folder (str): Path to the session folder.

        Returns:
            Session: The loaded session object, or None if loading fails.
        """
        session_info_path = os.path.join(session_folder, "session_info.json")
        if not os.path.exists(session_info_path):
            print(f"Session info file not found: {session_info_path}")
            return None

        try:
            session_data = read_json(session_info_path)
            session = Session.from_dict(session_data)
            # Validate required fields
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
            if not all(key in session_data for key in required_keys):
                raise ValueError(f"Session data missing required keys in {session_info_path}")

            return session
        except Exception as e:
            print(f"Error loading session from {session_info_path}: {e}")
            return None

    def create_session(self, name, images_directory, processor_model_name='mobilenetv3s'):
        """
        Creates a new analysis session.

        Args:
            name (str): Name of the session.
            images_directory (str): Path to the directory containing images.
            processor_model_name (str, optional): Name of the processor model. Defaults to 'mobilenetv3s'.

        Returns:
            Session: The newly created session object.
        """
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(self.sessions_dir, f"{name} [BioSort]")
        os.makedirs(session_folder, exist_ok=True)
        print(f"Created session folder at {session_folder}")

        # Create subdirectories
        masks_dir = os.path.join(session_folder, "masks")
        metadata_dir = os.path.join(session_folder, "metadata")
        features_dir = os.path.join(session_folder, "features")
        masked_images_dir = os.path.join(session_folder, "masked_images")
        os.makedirs(masks_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        os.makedirs(features_dir, exist_ok=True)
        os.makedirs(masked_images_dir, exist_ok=True)
        print(f"Created subdirectories: masks at {masks_dir}, metadata at {metadata_dir}, features at {features_dir}", f"masked_images at {masked_images_dir}")

        # Initialize empty metadata files
        objects_metadata_path = os.path.join(metadata_dir, "objects_metadata.json")
        clusters_metadata_path = os.path.join(metadata_dir, "clusters_metadata.json")
        classes_metadata_path = os.path.join(metadata_dir, "classes_metadata.json")
        masks_metadata_path = os.path.join(metadata_dir, "masks_metadata.json")
        features_metadata_path = os.path.join(metadata_dir, "features_metadata.json")
        session_info_path = os.path.join(session_folder, "session_info.json")

        initial_metadata = {
            "objects": [],
            "clusters": [],
            "classes": [],
            "masks": [],
            "features": [],
            "masked_images": []
        }

        # Write metadata files
        atomic_write(objects_metadata_path, {"objects": []})
        atomic_write(clusters_metadata_path, {"clusters": []})
        atomic_write(classes_metadata_path, {"classes": []})
        atomic_write(masks_metadata_path, {"masks": []})
        atomic_write(features_metadata_path, {"features": []})
        print(f"Initialized metadata files in {metadata_dir}")

        # Initialize Session object
        session_info = {
            "version": "1.0",
            "id": session_id,
            "name": name,
            "creation_date": datetime.now().isoformat(),
            "last_opening_date": datetime.now().isoformat(),
            "images_directory": os.path.abspath(images_directory),
            "session_folder": os.path.abspath(session_folder),
            "masks_directory": os.path.abspath(masks_dir),
            "metadata_directory": os.path.abspath(metadata_dir),
            "features_directory": os.path.abspath(features_dir),
            "masked_images_directory": os.path.abspath(masked_images_dir),
            "processor_model": processor_model_name
        }

        session = Session.from_dict(session_info)
        self.sessions[session.id] = session
        print(f"Session {session.id} ('{session.name}') created successfully.")

        # Save the sessions index
        self._save_sessions_index()

        return session

    def save_session(self, session):
        """
        Saves the session's current state to its session_info.json file and updates the sessions index.

        Args:
            session (Session): The session object to save.
        """
        session_data = session.to_dict()
        session_info_path = session.session_info_path
        atomic_write(session_info_path, session_data)
        print(f"Session data saved to {session_info_path}")

        self._save_sessions_index()

    def open_session(self, session_id):
        """
        Opens an existing session by updating its last opened date.

        Args:
            session_id (str): ID of the session to open.

        Returns:
            Session: The opened session object, or None if not found.
        """
        session = self.sessions.get(session_id)
        if session:
            # Update last opened date
            session.last_opening_date = datetime.now().isoformat()
            self.save_session(session)
            print(f"Session {session_id} ('{session.name}') opened successfully.")
            return session
        else:
            print(f"Session with ID {session_id} not found.")
            return None

    def delete_session(self, session_id):
        """
        Deletes a session and removes its directory and metadata.

        Args:
            session_id (str): ID of the session to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        session = self.sessions.pop(session_id, None)
        if session:
            try:
                shutil.rmtree(session.session_folder, ignore_errors=False)
                print(f"Session folder {session.session_folder} deleted successfully.")
            except Exception as e:
                print(f"Error deleting session folder {session.session_folder}: {e}")
                return False

            self._save_sessions_index()
            print(f"Session {session_id} ('{session.name}') deleted successfully.")
            return True
        else:
            print(f"Session with ID {session_id} does not exist.")
            return False

    def get_session(self, session_id):
        """
        Retrieves a session by its ID.

        Args:
            session_id (str): ID of the session to retrieve.

        Returns:
            Session: The session object, or None if not found.
        """
        return self.sessions.get(session_id)

    def list_sessions(self):
        """
        Lists all available sessions.

        Returns:
            list: List of Session objects.
        """
        return list(self.sessions.values())

    def update_session_last_opened(self, session_id):
        """
        Updates the last opened date of a session.

        Args:
            session_id (str): ID of the session to update.
        """
        session = self.sessions.get(session_id)
        if session:
            session.last_opening_date = datetime.now().isoformat()
            self.save_session(session)
            print(f"Session {session_id} last opened date updated.")
        else:
            print(f"Session with ID {session_id} not found.")
