from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):

    agent: str = "resume"

    message: str

    session_id: Optional[str] = None