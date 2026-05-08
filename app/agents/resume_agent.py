from app.graphs.resume_graph import (
    resume_graph
)

class ResumeAgent:

    async def run(self, message: str):

        result = resume_graph.invoke({
            "question": message
        })

        return result["answer"]