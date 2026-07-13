from app.graphs.resume_graph import (
    get_chat_history,
    add_message
)

from app.llm.openrouter import llm
from app.services.config_service import ConfigService

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

async def stream_response(
    question: str,
    context: str,
    session_id: str,
    metadata_out: dict = None
):

    history = get_chat_history(session_id)

    messages = []

    # Fetch system prompt from DB (with cache)
    system_prompt = ConfigService.get_system_prompt(agent="resume")

    messages.append(
        SystemMessage(content=system_prompt)
    )

    for msg in reversed(history):

        if msg.get("user_message"):

            messages.append(
                HumanMessage(
                    content=msg["user_message"]
                )
            )

        if msg.get("assistant_message"):

            messages.append(
                AIMessage(
                    content=msg["assistant_message"]
                )
            )

    final_prompt = f"""
Resume Context:
{context}

Question:
{question}
"""

    messages.append(
        HumanMessage(content=final_prompt)
    )

    full_response = ""

    async for chunk in llm.astream(messages):

        if chunk.content:

            full_response += chunk.content

            yield f"data: {chunk.content}\n\n"
        
        if metadata_out is not None and hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
            metadata_out["input_tokens"] = chunk.usage_metadata.get("input_tokens", 0)
            metadata_out["output_tokens"] = chunk.usage_metadata.get("output_tokens", 0)

    # Save the streamed response to chat history
    add_message(session_id, question, full_response)