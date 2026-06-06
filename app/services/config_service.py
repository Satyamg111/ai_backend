import time
from app.db.supabase import supabase

# ============================================
# DEFAULT PROMPTS PER AGENT
# ============================================

AGENT_DEFAULT_PROMPTS = {
    "resume": """You are a warm, human-like virtual assistant representing Satyam on his portfolio website.
Your goal is to answer questions about Satyam's experience, skills, and background in a friendly, conversational, and enthusiastic tone.

IMPORTANT RULES:
- Always respond in English.
- Be warm and welcoming. Use emojis occasionally if they fit naturally.
- Answer ONLY using the provided context, but act as if you already know this information natively.
- NEVER use robotic phrases like "based on the resume", "according to the context", or "as per the document". Answer directly.
- Never say you are an AI model like ChatGPT or Hunyuan. You are simply Satyam's virtual assistant.
- Keep responses concise, engaging, and conversational rather than strict or overly formal.
- If information is unavailable, politely say something like:
  'I don't have that specific detail right now, but feel free to reach out to Satyam directly!'""",
}

# Generic fallback for any unlisted agent
GENERIC_DEFAULT_PROMPT = """You are a helpful AI assistant. Answer the user's question clearly and concisely."""


class ConfigService:
    """
    Manages per-agent system prompts stored in Supabase.
    Keys in the `system_configs` table follow the pattern:
        system_prompt:<agent_name>
    e.g. system_prompt:resume
    """

    _cache: dict = {}           # { agent: (prompt, fetched_at) }
    _CACHE_TTL: int = 300       # 5 minutes

    # ==========================================
    # HELPERS
    # ==========================================

    @classmethod
    def _db_key(cls, agent: str) -> str:
        return f"system_prompt:{agent}"

    @classmethod
    def _default_for(cls, agent: str) -> str:
        return AGENT_DEFAULT_PROMPTS.get(agent, GENERIC_DEFAULT_PROMPT)

    # ==========================================
    # GET
    # ==========================================

    @classmethod
    def get_system_prompt(cls, agent: str = "resume") -> str:
        """Fetch system prompt for a given agent. Uses cache; falls back to default."""
        now = time.time()
        cached = cls._cache.get(agent)

        if cached:
            prompt, fetched_at = cached
            if now - fetched_at < cls._CACHE_TTL:
                return prompt

        try:
            db_key = cls._db_key(agent)
            response = (
                supabase.table("system_configs")
                .select("value")
                .eq("key", db_key)
                .execute()
            )
            if response.data:
                prompt = response.data[0]["value"]
                cls._cache[agent] = (prompt, now)
                return prompt

        except Exception as e:
            print(f"[ConfigService] Error fetching prompt for agent '{agent}': {e}")

        return cls._default_for(agent)

    # ==========================================
    # UPDATE
    # ==========================================

    @classmethod
    def update_system_prompt(cls, agent: str, new_prompt: str) -> bool:
        """Upsert the system prompt for a given agent in Supabase and refresh cache."""
        try:
            db_key = cls._db_key(agent)
            existing = (
                supabase.table("system_configs")
                .select("key")
                .eq("key", db_key)
                .execute()
            )
            if existing.data:
                supabase.table("system_configs").update(
                    {"value": new_prompt}
                ).eq("key", db_key).execute()
            else:
                supabase.table("system_configs").insert(
                    {"key": db_key, "value": new_prompt}
                ).execute()

            cls._cache[agent] = (new_prompt, time.time())
            return True

        except Exception as e:
            print(f"[ConfigService] Error updating prompt for agent '{agent}': {e}")
            return False

    # ==========================================
    # LIST ALL AGENTS
    # ==========================================

    @classmethod
    def list_agents(cls) -> list:
        """Return all agent names that have a system prompt in the DB."""
        try:
            response = (
                supabase.table("system_configs")
                .select("key, value")
                .like("key", "system_prompt:%")
                .execute()
            )
            return [
                {
                    "agent": row["key"].removeprefix("system_prompt:"),
                    "preview": row["value"][:80] + "..." if len(row["value"]) > 80 else row["value"],
                }
                for row in response.data
            ]
        except Exception as e:
            print(f"[ConfigService] Error listing agents: {e}")
            return []
