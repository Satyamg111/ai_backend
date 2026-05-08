from app.agents.resume_agent import ResumeAgent

class AgentService:

    def __init__(self):

        self.agents = {
            "resume": ResumeAgent(),
        }

    async def execute(
        self,
        agent_name: str,
        message: str
    ):

        if agent_name not in self.agents:
            return "Agent not found"

        agent = self.agents[agent_name]

        return await agent.run(message)