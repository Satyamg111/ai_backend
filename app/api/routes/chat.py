from fastapi import APIRouter

from fastapi.responses import (
    StreamingResponse
)

from app.models.chat_models import (
    ChatRequest
)

from app.graphs.resume_graph import (
    resume_graph
)

from app.services.stream_service import (
    stream_response
)

router = APIRouter()

# ============================================
# NORMAL CHAT
# ============================================

@router.post("")

async def chat(
    request: ChatRequest
):

    result = resume_graph.invoke({
        "question": request.message
    })

    return {
        "success": True,
        "response": result["answer"]
    }

# ============================================
# STREAM CHAT
# ============================================

@router.post("/stream")

async def stream_chat(
    request: ChatRequest
):

    result = resume_graph.invoke({
        "question": request.message
    })

    context = result["context"]

    generator = stream_response(
        request.message,
        context
    )

    return StreamingResponse(
    generator,
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
)