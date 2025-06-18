"""Session and conversation memory management."""

import uuid
from datetime import datetime
from typing import List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from .database import get_database_manager
from .models import Message, MessageRole
from .models import Session as SessionModel


class SessionManager:
    """Manages conversation sessions and persistent memory."""

    def __init__(self):
        self.db_manager = get_database_manager()

    def create_session(self, name: Optional[str] = None) -> str:
        """Create a new conversation session.

        Args:
            name: Optional name for the session

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        with self.db_manager.get_session() as db_session:
            session = SessionModel(
                id=session_id,
                name=name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )
            db_session.add(session)

        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session information.

        Args:
            session_id: The session ID

        Returns:
            Session info dict or None if not found
        """
        with self.db_manager.get_session() as db_session:
            session = (
                db_session.query(SessionModel)
                .filter(SessionModel.id == session_id)
                .first()
            )

            if session:
                return {
                    "id": session.id,
                    "name": session.name,
                    "created_at": session.created_at.isoformat(),
                    "message_count": len(session.messages),
                }
            return None

    def list_sessions(self) -> List[dict]:
        """List all conversation sessions.

        Returns:
            List of session info dicts
        """
        with self.db_manager.get_session() as db_session:
            sessions = (
                db_session.query(SessionModel)
                .order_by(SessionModel.created_at.desc())
                .all()
            )

            return [
                {
                    "id": session.id,
                    "name": session.name,
                    "created_at": session.created_at.isoformat(),
                    "message_count": len(session.messages),
                }
                for session in sessions
            ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session and all its messages.

        Args:
            session_id: The session ID

        Returns:
            True if session was deleted, False if not found
        """
        with self.db_manager.get_session() as db_session:
            session = (
                db_session.query(SessionModel)
                .filter(SessionModel.id == session_id)
                .first()
            )

            if session:
                db_session.delete(session)
                return True
            return False

    def add_message(self, session_id: str, role: MessageRole, content: str) -> bool:
        """Add a message to a session.

        Args:
            session_id: The session ID
            role: MessageRole enum value
            content: Message content

        Returns:
            True if message was added, False if session not found
        """
        with self.db_manager.get_session() as db_session:
            # Check if session exists
            session = (
                db_session.query(SessionModel)
                .filter(SessionModel.id == session_id)
                .first()
            )

            if not session:
                return False

            message = Message(session_id=session_id, role=role.value, content=content)
            db_session.add(message)
            return True

    def get_messages_as_langchain(self, session_id: str) -> List[BaseMessage]:
        """Get session messages as LangChain message objects.

        Args:
            session_id: The session ID

        Returns:
            List of LangChain BaseMessage objects
        """
        with self.db_manager.get_session() as db_session:
            messages = (
                db_session.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.created_at)
                .all()
            )

            langchain_messages = []
            for msg in messages:
                if msg.role == MessageRole.USER.value:
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.role == MessageRole.ASSISTANT.value:
                    langchain_messages.append(AIMessage(content=msg.content))

            return langchain_messages

    def clear_session_messages(self, session_id: str) -> bool:
        """Clear all messages from a session.

        Args:
            session_id: The session ID

        Returns:
            True if messages were cleared, False if session not found
        """
        with self.db_manager.get_session() as db_session:
            # Check if session exists
            session = (
                db_session.query(SessionModel)
                .filter(SessionModel.id == session_id)
                .first()
            )

            if not session:
                return False

            # Delete all messages for this session
            db_session.query(Message).filter(Message.session_id == session_id).delete()

            return True


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
