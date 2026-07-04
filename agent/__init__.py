import importlib.util
import os
import sys

from agent.goal_planner_agent import GoalPlannerAgent
from agent.budget_monitor_agent import BudgetMonitorAgent

# Load ReACTAgent from root-level agent.py (shadowed by this package)
_agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent.py")
_spec = importlib.util.spec_from_file_location("_root_agent", _agent_path)
_root_agent = importlib.util.module_from_spec(_spec)
sys.modules["_root_agent"] = _root_agent
_spec.loader.exec_module(_root_agent)
ReACTAgent = _root_agent.ReACTAgent

__all__ = ["GoalPlannerAgent", "BudgetMonitorAgent", "ReACTAgent"]
