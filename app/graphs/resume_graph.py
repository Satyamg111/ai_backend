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

def get_chat_history():

    response = supabase.table(
        "chat_history"
    ).select("*").order(
        "created_at"
    ).limit(10).execute()

    return response.data


def add_message(question, answer):

    supabase.table("chat_history").insert({
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

    history = get_chat_history()

    messages = []

    # ========================================
    # SYSTEM PROMPT
    # ========================================

    system_prompt = """
You are a professional AI interview assistant.

IMPORTANT RULES:
- Always respond in English
- Answer ONLY using the resume context
- Never say you are another AI model
- Never introduce yourself as Tencent, Hunyuan, ChatGPT, etc.
- Speak professionally like the candidate
- Keep responses concise and natural
- If information is unavailable, say:
  'This information is not available in the resume.'
"""

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

    # ========================================
    # SAVE CHAT HISTORY
    # ========================================

    add_message(question, answer)

    return {
        "answer": answer
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