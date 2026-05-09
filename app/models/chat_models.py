from pydantic import BaseModel

class ChatRequest(BaseModel):

    agent: str = "resume"

    message: str