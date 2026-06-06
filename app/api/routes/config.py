from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.auth.admin_auth import verify_admin
from app.services.config_service import ConfigService, AGENT_DEFAULT_PROMPTS

router = APIRouter()


class PromptUpdateRequest(BaseModel):
    prompt: str


# ============================================
# LIST ALL AGENTS WITH PROMPTS IN DB
# ============================================

@router.get("/agents")
async def list_agents(admin=Depends(verify_admin)):
    """List all agents that have a system prompt stored in the DB."""
    return {"agents": ConfigService.list_agents()}


# ============================================
# GET PROMPT FOR AN AGENT
# ============================================

@router.get("/prompt")
async def get_prompt(
    agent: str = Query(default="resume"),
    admin=Depends(verify_admin)
):
    """Fetch the active system prompt for the given agent (served from cache/DB)."""
    return {
        "agent": agent,
        "system_prompt": ConfigService.get_system_prompt(agent=agent)
    }


# ============================================
# UPDATE PROMPT FOR AN AGENT
# ============================================

@router.put("/prompt")
async def update_prompt(
    request: PromptUpdateRequest,
    agent: str = Query(default="resume"),
    admin=Depends(verify_admin)
):
    """Update or create the system prompt for the given agent in the DB."""
    success = ConfigService.update_system_prompt(
        agent=agent,
        new_prompt=request.prompt
    )
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update system prompt for agent '{agent}'."
        )
    return {
        "success": True,
        "agent": agent,
        "message": f"System prompt for '{agent}' successfully updated."
    }


# ============================================
# RESET PROMPT FOR AN AGENT TO DEFAULT
# ============================================

@router.delete("/prompt")
async def reset_prompt(
    agent: str = Query(default="resume"),
    admin=Depends(verify_admin)
):
    """Reset an agent's system prompt to its built-in default."""
    default = AGENT_DEFAULT_PROMPTS.get(agent)
    if not default:
        raise HTTPException(
            status_code=404,
            detail=f"No built-in default prompt found for agent '{agent}'."
        )
    success = ConfigService.update_system_prompt(agent=agent, new_prompt=default)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset prompt.")
    return {
        "success": True,
        "agent": agent,
        "message": f"System prompt for '{agent}' reset to default."
    }
