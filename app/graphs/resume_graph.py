# ============================================
# FILE:
# app/graphs/resume_graph.py
# ============================================

import os
import json

from typing import TypedDict

from langgraph.graph import (
    StateGraph,
    END
)

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from app.db.chroma import collection 

from app.llm.openrouter import llm
from app.db.supabase import supabase
from app.services.config_service import ConfigService

def get_chat_history(session_id: str):

    if not session_id:
        return []

    response = supabase.table(
        "chat_history"
    ).select("*").eq(
        "session_id", session_id
    ).order(
        "created_at", desc=True
    ).limit(10).execute()

    return response.data


def add_message(session_id: str, question: str, answer: str):

    if not session_id:
        return

    supabase.table("chat_history").insert({
        "session_id": session_id,
        "user_message": question,
        "assistant_message": answer
    }).execute()


# ============================================
# LANGGRAPH STATE
# ============================================

class AgentState(TypedDict):

    question: str
    context: str
    answer: str
    session_id: str
    input_tokens: int
    output_tokens: int

# ============================================
# RETRIEVE NODE
# ============================================

def retrieve(state: AgentState):

    question = state["question"]

    # docs = retriever.invoke(question)
    results = collection.query(
    query_texts=[question],
    n_results=3
)

    context = "\n\n".join(
        results["documents"][0]
    )

    # context = "\n\n".join([
    #     doc.page_content for doc in docs
    # ])

    return {
        "context": context
    }

# ============================================
# GENERATE NODE
# ============================================

def generate(state: AgentState):

    question = state["question"]
    context = state["context"]
    session_id = state.get("session_id", "")

    history = get_chat_history(session_id)

    messages = []

    # ========================================
    # SYSTEM PROMPT (fetched from DB)
    # ========================================

    system_prompt = ConfigService.get_system_prompt(agent="resume")

    messages.append(
        SystemMessage(content=system_prompt)
    )

    # ========================================
    # PREVIOUS CHAT HISTORY
    # ========================================

    for msg in reversed(history):

        user_message = msg.get("user_message")

        assistant_message = msg.get(
            "assistant_message"
        )

        if user_message:

            messages.append(
                HumanMessage(content=user_message)
            )

        if assistant_message:

            messages.append(
                AIMessage(content=assistant_message)
            )
    # ========================================
    # FINAL PROMPT
    # ========================================

    final_prompt = f"""
Resume Context:
{context}

Question:
{question}
"""

    messages.append(
        HumanMessage(content=final_prompt)
    )

    # ========================================
    # LLM CALL
    # ========================================

    response = llm.invoke(messages)

    answer = response.content
    
    input_tokens = 0
    output_tokens = 0
    
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        input_tokens = response.usage_metadata.get("input_tokens", 0)
        output_tokens = response.usage_metadata.get("output_tokens", 0)

    # ========================================
    # SAVE CHAT HISTORY
    # ========================================

    add_message(session_id, question, answer)

    return {
        "answer": answer,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    }

# ============================================
# BUILD GRAPH
# ============================================

graph = StateGraph(AgentState)

graph.add_node("retrieve", retrieve)

graph.add_node("generate", generate)

graph.set_entry_point("retrieve")

graph.add_edge("retrieve", "generate")

graph.add_edge("generate", END)

# ============================================
# COMPILE GRAPH
# ============================================

resume_graph = graph.compile()