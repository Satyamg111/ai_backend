from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent_service import (
    AgentService
)

router = APIRouter()

agent_service = AgentService()

class ChatRequest(BaseModel):
    agent: str
    message: str

@router.post("/")

async def chat(request: ChatRequest):

    response = await agent_service.execute(
        request.agent,
        request.message
    )

    return {
        "success": True,
        "agent": request.agent,
        "response": response
    }