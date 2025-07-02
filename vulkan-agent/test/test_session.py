"""Tests for session.py - session and conversation management functionality."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from vulkan_agent.models import Message, MessageRole
from vulkan_agent.session import SessionManager, get_session_manager


class TestSessionManager:
    """Test SessionManager functionality."""

    @patch("vulkan_agent.session.get_database_manager")
    def test_init(self, mock_get_db_manager):
        """Test SessionManager initialization."""
        mock_db_manager = MagicMock()
        mock_get_db_manager.return_value = mock_db_manager

        manager = SessionManager()

        assert manager.db_manager == mock_db_manager
        mock_get_db_manager.assert_called_once()

    @patch("vulkan_agent.session.get_database_manager")
    def test_get_session_exists(self, mock_get_db_manager):
        """Test getting an existing session."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        # Mock session data
        mock_session = MagicMock()
        mock_session.id = "test-session-1"
        mock_session.name = "Test Session"
        mock_session.created_at = datetime(2025, 1, 1, 10, 0, 0)
        mock_session.messages = [MagicMock(), MagicMock()]  # 2 messages

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_session
        )

        manager = SessionManager()
        result = manager.get_session("test-session-1")

        assert result is not None
        assert result["id"] == "test-session-1"
        assert result["name"] == "Test Session"
        assert result["created_at"] == "2025-01-01T10:00:00"
        assert result["message_count"] == 2

    @patch("vulkan_agent.session.get_database_manager")
    def test_get_session_not_exists(self, mock_get_db_manager):
        """Test getting a non-existent session."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        manager = SessionManager()
        result = manager.get_session("non-existent-session")

        assert result is None

    @patch("vulkan_agent.session.get_database_manager")
    def test_list_sessions(self, mock_get_db_manager):
        """Test listing all sessions."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        # Mock sessions data
        mock_session1 = MagicMock()
        mock_session1.id = "session-1"
        mock_session1.name = "Session 1"
        mock_session1.created_at = datetime(2025, 1, 1, 10, 0, 0)
        mock_session1.messages = [MagicMock()]

        mock_session2 = MagicMock()
        mock_session2.id = "session-2"
        mock_session2.name = "Session 2"
        mock_session2.created_at = datetime(2025, 1, 1, 11, 0, 0)
        mock_session2.messages = [MagicMock(), MagicMock()]

        mock_db_session.query.return_value.order_by.return_value.all.return_value = [
            mock_session1,
            mock_session2,
        ]

        manager = SessionManager()
        result = manager.list_sessions()

        assert len(result) == 2
        assert result[0]["id"] == "session-1"
        assert result[0]["message_count"] == 1
        assert result[1]["id"] == "session-2"
        assert result[1]["message_count"] == 2

    @patch("vulkan_agent.session.get_database_manager")
    def test_delete_session_exists(self, mock_get_db_manager):
        """Test deleting an existing session."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        mock_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_session
        )

        manager = SessionManager()
        result = manager.delete_session("test-session-1")

        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_session)

    @patch("vulkan_agent.session.get_database_manager")
    def test_delete_session_not_exists(self, mock_get_db_manager):
        """Test deleting a non-existent session."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        manager = SessionManager()
        result = manager.delete_session("non-existent-session")

        assert result is False
        mock_db_session.delete.assert_not_called()

    @patch("vulkan_agent.session.get_database_manager")
    def test_add_message(self, mock_get_db_manager):
        """Test adding a message to a session."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        manager = SessionManager()
        manager.add_message("session-1", MessageRole.USER, "Hello there!")

        # Verify message was added
        mock_db_session.add.assert_called_once()
        message_call = mock_db_session.add.call_args[0][0]
        assert isinstance(message_call, Message)
        assert message_call.session_id == "session-1"
        assert message_call.role == MessageRole.USER.value
        assert message_call.content == "Hello there!"

    @patch("vulkan_agent.session.get_database_manager")
    def test_get_messages(self, mock_get_db_manager):
        """Test getting messages from a session."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        # Mock messages data
        mock_message1 = MagicMock()
        mock_message1.id = 1
        mock_message1.role = MessageRole.USER.value
        mock_message1.content = "Hello"
        mock_message1.created_at = datetime(2025, 1, 1, 10, 0, 0)

        mock_message2 = MagicMock()
        mock_message2.id = 2
        mock_message2.role = MessageRole.ASSISTANT.value
        mock_message2.content = "Hi there!"
        mock_message2.created_at = datetime(2025, 1, 1, 10, 0, 1)

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_message1,
            mock_message2,
        ]

        manager = SessionManager()
        result = manager.get_session_messages("session-1")

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["role"] == MessageRole.USER.value
        assert result[0]["content"] == "Hello"
        assert result[1]["id"] == 2
        assert result[1]["role"] == MessageRole.ASSISTANT.value
        assert result[1]["content"] == "Hi there!"

    @patch("vulkan_agent.session.get_database_manager")
    def test_get_langchain_memory(self, mock_get_db_manager):
        """Test getting LangChain-compatible memory."""
        mock_db_manager = MagicMock()
        mock_db_session = MagicMock()
        mock_db_manager.get_session.return_value.__enter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        # Mock messages data
        mock_message1 = MagicMock()
        mock_message1.role = MessageRole.USER.value
        mock_message1.content = "Hello"

        mock_message2 = MagicMock()
        mock_message2.role = MessageRole.ASSISTANT.value
        mock_message2.content = "Hi there!"

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_message1,
            mock_message2,
        ]

        manager = SessionManager()
        result = manager.get_messages_as_langchain("session-1")

        assert len(result) == 2
        assert result[0].content == "Hello"
        assert result[1].content == "Hi there!"
        # Should be LangChain message objects


def test_get_session_manager():
    """Test getting the global session manager."""
    # Should return a SessionManager instance
    manager = get_session_manager()
    assert isinstance(manager, SessionManager)

    # Should return the same instance on subsequent calls
    manager2 = get_session_manager()
    assert manager is manager2
