import time
import uuid

from fastapi import APIRouter, Request

from fastapi.responses import (
    StreamingResponse
)

from app.models.chat_models import (
    ChatRequest
)

from app.graphs.resume_graph import (
    resume_graph,
    retrieve
)

from app.services.stream_service import (
    stream_response
)

from app.services.usage_service import (
    UsageTracker
)

router = APIRouter()

# ============================================
# NORMAL CHAT
# ============================================

@router.post("")

async def chat(
    request: ChatRequest,
    req: Request,
):

    start = time.time()
    ip = req.client.host if req.client else "unknown"
    session_id = request.session_id or str(uuid.uuid4())

    try:

        result = resume_graph.invoke({
            "question": request.message,
            "session_id": session_id
        })

        elapsed = int(
            (time.time() - start) * 1000
        )

        UsageTracker.log(
            session_id=session_id,
            ip_address=ip,
            user_message=request.message,
            response_length=len(result["answer"]),
            response_time_ms=elapsed,
            agent=request.agent,
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
        )

        return {
            "success": True,
            "response": result["answer"]
        }

    except Exception as e:

        elapsed = int(
            (time.time() - start) * 1000
        )

        UsageTracker.log(
            session_id=session_id,
            ip_address=ip,
            user_message=request.message,
            response_length=0,
            response_time_ms=elapsed,
            agent=request.agent,
            status="error",
            error_message=str(e),
        )

        raise

# ============================================
# STREAM CHAT
# ============================================

@router.post("/stream")

async def stream_chat(
    request: ChatRequest,
    req: Request,
):

    start = time.time()
    ip = req.client.host if req.client else "unknown"
    session_id = request.session_id or str(uuid.uuid4())

    result = retrieve({
        "question": request.message,
        "session_id": session_id
    })

    context = result["context"]

    metadata_out = {}

    # Wrap the stream generator to track
    # usage after the stream completes

    async def tracked_stream():

        full_response = ""

        async for chunk in stream_response(
            request.message,
            context,
            session_id,
            metadata_out
        ):
            # chunks are "data: {text}\n\n"
            text = chunk.replace(
                "data: ", ""
            ).strip()

            full_response += text

            yield chunk

        # Log after stream completes
        elapsed = int(
            (time.time() - start) * 1000
        )

        # For stream we track tokens generated during the stream (metadata_out)
        # plus the tokens used when fetching the context via resume_graph
        graph_input = result.get("input_tokens", 0)
        graph_output = result.get("output_tokens", 0)
        
        UsageTracker.log(
            session_id=session_id,
            ip_address=ip,
            user_message=request.message,
            response_length=len(full_response),
            response_time_ms=elapsed,
            agent=request.agent,
            input_tokens=graph_input + metadata_out.get("input_tokens", 0),
            output_tokens=graph_output + metadata_out.get("output_tokens", 0),
        )

    return StreamingResponse(
        tracked_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )