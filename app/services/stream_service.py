from app.graphs.resume_graph import (
    get_chat_history
)

from app.llm.openrouter import llm

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

async def stream_response(
    question: str,
    context: str
):

    history = get_chat_history()

    messages = []

    system_prompt = """
You are a professional AI interview assistant.

IMPORTANT RULES:
- Always respond in English
- Answer ONLY using the resume context
- Speak professionally
"""

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

    # save history later if needed