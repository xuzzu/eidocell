### backend/presenters/session_presenter.py
from PySide6.QtCore import Signal, QObject

from UI.navigation_interface.sessions.sessions_widget import FolderListDialog, FolderCard
from backend.session_manager import SessionManager


class SessionPresenter(QObject):
    """Presenter for handling session related actions."""
    session_chosen = Signal(str)

    def __init__(self, session_manager: SessionManager, session_view_widget: FolderListDialog):
        super().__init__()
        self.session_manager = session_manager
        self.session_view_widget = session_view_widget

        self.session_view_widget.session_created.connect(self.create_session)
        self.session_view_widget.session_chosen.connect(self.choose_session)

    def choose_session(self, session_id):
        """Loads the selected session."""
        session = self.session_manager.open_session(session_id)
        if session:
            print(f"Loaded session: {session.name}")
            self.session_chosen.emit(session_id)
            return session
        else:
            print(f"Error loading session with ID {session_id}")

    def create_session(self, folder_card: FolderCard):
        """Creates a new session."""

        print('Started session creation')
        session_name = folder_card.get_session_name()
        images_directory = folder_card.get_folder_path()
        session = self.session_manager.create_session(session_name, images_directory)
        if session:
            print(f"Created session: {session.name}")
            folder_card.set_session_id(session.id)
            self.session_manager._save_sessions_index()
        else:
            print("Error creating session.")

    def delete_session(self, session_id):
        """Deletes the selected session."""
        try:
            self.session_manager.delete_session(session_id)
            self.session_manager._save_sessions_index()

            for folder_card in self.session_view_widget.get_folder_cards():
                if folder_card.get_session_id() == session_id:
                    self.session_view_widget.deleteFolderCard(folder_card)

            print(f"Deleted session with ID {session_id}")
        except:
            print(f"Error deleting session with ID {session_id}")

