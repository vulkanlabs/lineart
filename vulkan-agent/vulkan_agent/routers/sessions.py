"""Session management router for conversation sessions."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..session import get_session_manager

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    name: Optional[str] = None


class SessionResponse(BaseModel):
    """Session information response."""

    id: str
    name: str
    created_at: str
    message_count: int


class CreateSessionResponse(BaseModel):
    """Response for session creation."""

    id: str
    name: str
    message: str


@router.post("/", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new conversation session."""
    try:
        session_manager = get_session_manager()
        session_id = session_manager.create_session(request.name)

        # Get the created session info
        session_info = session_manager.get_session(session_id)

        return CreateSessionResponse(
            id=session_id,
            name=session_info["name"],
            message="Session created successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("/", response_model=List[SessionResponse])
async def list_sessions():
    """List all conversation sessions."""
    try:
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions()

        return [SessionResponse(**session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get information about a specific session."""
    try:
        session_manager = get_session_manager()
        session_info = session_manager.get_session(session_id)

        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(**session_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a conversation session and all its messages."""
    try:
        session_manager = get_session_manager()
        success = session_manager.delete_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@router.post("/{session_id}/clear")
async def clear_session_messages(session_id: str):
    """Clear all messages from a session."""
    try:
        session_manager = get_session_manager()
        success = session_manager.clear_session_messages(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session messages cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error clearing session messages: {str(e)}"
        )
