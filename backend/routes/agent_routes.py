import logging
from fastapi import APIRouter
from backend.agent import FinanceTrackerAgent, AgentStateResponse, MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Agent"])

agent = FinanceTrackerAgent()


@router.get("/status", response_model=AgentStateResponse)
def agent_status():
    state = agent.get_state()
    return AgentStateResponse(
        thinking_state=state["thinking_state"],
        current_cycle=state["current_cycle"],
        task_complete=state["task_complete"],
        error_count=state["error_count"],
        executed_actions=state["executed_actions"],
        memory_summary=state["memory_summary"],
        memory_log=state["memory_log"],
    )


@router.post("/reset", response_model=MessageResponse)
def reset_agent():
    agent.reset()
    return {"message": "Agent reset successfully"}
