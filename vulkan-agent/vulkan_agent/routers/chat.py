"""Chat router for the Vulkan AI Agent with documentation management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..agent import (
    VulkanAgent,
    get_agent_status,
    get_global_agent,
    refresh_global_agent,
)
from ..config import config_manager
from ..schemas import AgentConfigResponse, ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


class AgentStatus(BaseModel):
    """Status of the agent and its components."""

    agent_configured: bool
    documentation_available: bool
    tools_count: int
    available_tools: list[str]


class DocumentationFile(BaseModel):
    """Model for documentation file operations."""

    relative_path: str
    content: str


class DocumentationFileList(BaseModel):
    """Model for listing documentation files."""

    files: list[str]


class DocumentationUpdate(BaseModel):
    """Model for documentation update response."""

    status: str
    message: str
    files_updated: int = 0


def get_agent_config() -> AgentConfigResponse:
    """Dependency to get the current agent configuration."""
    if not config_manager.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Agent not configured. Please configure the agent first via /api/config",
        )
    config = config_manager.get_config()
    if config is None:
        raise HTTPException(status_code=500, detail="Agent configuration error")
    return config


def get_agent_dependency(
    config: AgentConfigResponse = Depends(get_agent_config),
) -> VulkanAgent:
    """Dependency to get the agent instance."""
    try:
        return get_global_agent()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error initializing agent: {str(e)}"
        )


@router.get("/status", response_model=AgentStatus)
async def get_agent_status_endpoint():
    """Get the current status of the agent and its components."""
    try:
        status = get_agent_status()
        return AgentStatus(**status)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking agent status: {str(e)}"
        )


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest, agent: VulkanAgent = Depends(get_agent_dependency)
):
    """Send a message to the Vulkan AI Agent."""
    try:
        response = await agent.chat(request.message, request.session_id)

        # Check if tools were used (from agent status)
        agent_status = agent.get_status()
        tools_used = agent_status["tools_count"] > 0

        return ChatResponse(
            response=response, session_id=request.session_id, tools_used=tools_used
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        )


@router.post("/clear")
async def clear_conversation(
    session_id: str = None, agent: VulkanAgent = Depends(get_agent_dependency)
):
    """Clear conversation memory for a specific session."""
    try:
        if session_id:
            agent.clear_memory(session_id)
            return {
                "status": "success",
                "message": f"Session {session_id} memory cleared",
            }
        else:
            return {"status": "error", "message": "session_id parameter is required"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error clearing conversation: {str(e)}"
        )


# Documentation Management Endpoints


@router.get("/docs/list", response_model=DocumentationFileList)
async def list_documentation_files():
    """List all documentation files."""
    try:
        from ..knowledge_base import get_documentation_loader

        loader = get_documentation_loader()
        files = loader.list_documentation_files()

        return DocumentationFileList(files=files)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing documentation files: {str(e)}"
        )


@router.get("/docs/file/{file_path:path}")
async def get_documentation_file(file_path: str):
    """Get content of a specific documentation file."""
    try:
        from ..knowledge_base import get_documentation_loader

        loader = get_documentation_loader()
        full_path = loader.docs_path / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Documentation file not found")

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"relative_path": file_path, "content": content}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Documentation file not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading documentation file: {str(e)}"
        )


@router.put("/docs/file")
async def update_documentation_file(doc_file: DocumentationFile):
    """Update or create a documentation file."""
    try:
        from ..knowledge_base import get_documentation_loader

        loader = get_documentation_loader()
        loader.update_documentation_file(doc_file.relative_path, doc_file.content)

        # Refresh the global agent to pick up the updated documentation
        refresh_global_agent()

        return DocumentationUpdate(
            status="success",
            message=f"Documentation file updated: {doc_file.relative_path}",
            files_updated=1,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating documentation file: {str(e)}"
        )


@router.delete("/docs/file/{file_path:path}")
async def delete_documentation_file(file_path: str):
    """Delete a documentation file."""
    try:
        from ..knowledge_base import get_documentation_loader

        loader = get_documentation_loader()
        loader.delete_documentation_file(file_path)

        # Refresh the global agent to pick up the updated documentation
        refresh_global_agent()

        return DocumentationUpdate(
            status="success", message=f"Documentation file deleted: {file_path}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting documentation file: {str(e)}"
        )


@router.post("/docs/reload")
async def reload_documentation():
    """Reload all documentation from disk."""
    try:
        from ..knowledge_base import refresh_documentation_loader

        refresh_documentation_loader()

        # Refresh the global agent to pick up the reloaded documentation
        refresh_global_agent()

        return DocumentationUpdate(
            status="success", message="Documentation reloaded successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reloading documentation: {str(e)}"
        )
