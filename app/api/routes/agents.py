from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_agents():

    return {
        "agents": [
            "resume",
        ]
    }