import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AgentMemory:
    def __init__(self) -> None:
        self.thought_process: List[Dict[str, Any]] = []
        self.action_history: List[Dict[str, Any]] = []
        self.observations: Dict[str, Dict[str, Any]] = {}
        self.reflections: List[Dict[str, Any]] = []

    def add_thought(self, thought: str, cycle: int) -> None:
        entry = {
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "thought": thought,
        }
        self.thought_process.append(entry)
        logger.info("Thought [cycle %d]: %s", cycle, thought)

    def get_latest_thought(self) -> Optional[str]:
        if self.thought_process:
            return self.thought_process[-1]["thought"]
        return None

    def get_thoughts_by_cycle(self, cycle: int) -> List[Dict[str, Any]]:
        return [t for t in self.thought_process if t["cycle"] == cycle]

    def add_action(self, action: str, params: Dict[str, Any], cycle: int) -> None:
        entry = {
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "params": params,
        }
        self.action_history.append(entry)
        logger.info("Action [cycle %d]: %s %s", cycle, action, params)

    def get_action_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit:
            return self.action_history[-limit:]
        return self.action_history

    def add_observation(self, key: str, value: Any, cycle: int) -> None:
        self.observations[key] = {
            "value": value,
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Observation [cycle %d]: %s = %s", cycle, key, value)

    def get_observation(self, key: str) -> Any:
        obs = self.observations.get(key)
        if obs:
            return obs["value"]
        return None

    def get_observations(self, key: Optional[str] = None) -> Any:
        if key:
            return self.get_observation(key)
        return {k: v["value"] for k, v in self.observations.items()}

    def get_latest_observation(self) -> Tuple[Optional[str], Any]:
        if not self.observations:
            return None, None
        last_key = list(self.observations.keys())[-1]
        return last_key, self.observations[last_key]["value"]

    def add_reflection(self, reflection: str, cycle: int) -> None:
        entry = {
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reflection": reflection,
        }
        self.reflections.append(entry)
        logger.info("Reflection [cycle %d]: %s", cycle, reflection)

    def get_latest_reflection(self) -> Optional[str]:
        if self.reflections:
            return self.reflections[-1]["reflection"]
        return None

    def get_full_log(self) -> Dict[str, Any]:
        return {
            "thoughts": self.thought_process,
            "actions": self.action_history,
            "observations": self.observations,
            "reflections": self.reflections,
        }

    def to_summary(self) -> Dict[str, Any]:
        return {
            "total_thoughts": len(self.thought_process),
            "total_actions": len(self.action_history),
            "total_observations": len(self.observations),
            "total_reflections": len(self.reflections),
            "latest_thought": self.get_latest_thought(),
            "latest_reflection": self.get_latest_reflection(),
        }

    def clear(self) -> None:
        self.thought_process.clear()
        self.action_history.clear()
        self.observations.clear()
        self.reflections.clear()
        logger.info("Agent memory cleared")

    def __repr__(self) -> str:
        return (
            f"AgentMemory(thoughts={len(self.thought_process)}, "
            f"actions={len(self.action_history)}, "
            f"observations={len(self.observations)}, "
            f"reflections={len(self.reflections)})"
        )
