import logging
from typing import Any, Dict, List, Optional, Callable

from memory import AgentMemory
from tools import validate_transaction, categorize_expense, generate_summary

logger = logging.getLogger(__name__)

MAX_CYCLES = 10

TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "validate_transaction": validate_transaction,
    "categorize_expense": categorize_expense,
    "generate_summary": generate_summary,
}


class ReACTAgent:
    def __init__(self) -> None:
        self.memory = AgentMemory()
        self.thinking_state: str = ""
        self.action_queue: List[Dict[str, Any]] = []
        self.current_cycle: int = 0
        self.task_complete: bool = False
        self.task_result: Any = None
        self.error_count: int = 0
        self.executed_actions: List[str] = []

    def add_task(self, task_type: str, params: Dict[str, Any]) -> None:
        action = {"tool": task_type, "params": params}
        self.action_queue.append(action)
        self.task_complete = False
        self.task_result = None
        self.current_cycle = 0
        self.executed_actions.clear()
        logger.info("Task queued: %s %s", task_type, params)

    def add_multiple_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        for task in tasks:
            self.action_queue.append(task)
        self.task_complete = False
        self.task_result = None
        self.current_cycle = 0
        self.executed_actions.clear()
        logger.info("Queued %d tasks", len(tasks))

    def think(self) -> str:
        if not self.action_queue:
            self.thinking_state = "No pending actions. Task complete."
            self.task_complete = True
            return self.thinking_state

        next_action = self.action_queue[0]
        tool_name = next_action["tool"]
        params = next_action["params"]

        if tool_name == "validate_transaction":
            thought = (
                f"Need to validate transaction: amount={params.get('amount')}, "
                f"category={params.get('category')}, date={params.get('date')}. "
                f"Will check amount>0, valid category, and valid date format."
            )
        elif tool_name == "categorize_expense":
            thought = (
                f"Need to categorize: '{params.get('description')}'. "
                f"Will match keywords against known categories."
            )
        elif tool_name == "generate_summary":
            txn_count = len(params.get("transactions", []))
            thought = (
                f"Need to generate summary for {txn_count} transactions. "
                f"Will calculate totals and group by category."
            )
        else:
            thought = f"Unknown tool '{tool_name}' in queue."

        self.thinking_state = thought
        self.memory.add_thought(thought, self.current_cycle)
        return thought

    def act(self) -> Dict[str, Any]:
        if self.task_complete or not self.action_queue:
            return {"status": "idle"}

        action = self.action_queue[0]
        tool_name = action["tool"]
        params = action["params"]

        logger.info("Executing action: %s", tool_name)
        self.memory.add_action(tool_name, params, self.current_cycle)

        if tool_name in TOOL_REGISTRY:
            try:
                tool_fn = TOOL_REGISTRY[tool_name]
                if tool_name == "validate_transaction":
                    result = tool_fn(
                        amount=params.get("amount", 0),
                        category=params.get("category", ""),
                        date=params.get("date", ""),
                    )
                elif tool_name == "categorize_expense":
                    result = tool_fn(
                        description=params.get("description", ""),
                    )
                elif tool_name == "generate_summary":
                    result = tool_fn(
                        transactions_list=params.get("transactions", []),
                    )
                else:
                    result = tool_fn(**params)
            except Exception as e:
                result = {"error": f"{type(e).__name__}: {str(e)}"}
                self.error_count += 1
                logger.error("Tool %s failed: %s", tool_name, result["error"])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        self.action_queue.pop(0)
        self.executed_actions.append(tool_name)

        return {"tool": tool_name, "params": params, "result": result}

    def observe(self, action_result: Dict[str, Any]) -> None:
        if action_result.get("status") == "idle":
            return

        tool_name = action_result.get("tool", "unknown")
        result = action_result.get("result", {})

        self.memory.add_observation(tool_name, result, self.current_cycle)

        if "error" in result:
            logger.warning(
                "Observation: Tool %s returned error: %s",
                tool_name, result["error"],
            )
        elif tool_name == "validate_transaction":
            valid = result.get("valid")
            confidence = result.get("confidence")
            logger.info(
                "Observation: Validation result: valid=%s, confidence=%s",
                valid, confidence,
            )
        elif tool_name == "categorize_expense":
            category = result.get("category")
            confidence = result.get("confidence")
            logger.info(
                "Observation: Categorized as '%s' (confidence: %s)",
                category, confidence,
            )
        elif tool_name == "generate_summary":
            total = result.get("total_transactions", 0)
            amount = result.get("total_amount", 0)
            logger.info(
                "Observation: Summary: %d transactions, total=%.2f",
                total, amount,
            )

    def reflect(self) -> str:
        if self.task_complete:
            reflection = "Task completed successfully. No further action needed."
            self.memory.add_reflection(reflection, self.current_cycle)
            return reflection

        if not self.action_queue:
            self.task_complete = True
            last_key, last_val = self.memory.get_latest_observation()
            if last_val is not None:
                self.task_result = last_val
            reflection = "Queue empty. Task complete."
            self.memory.add_reflection(reflection, self.current_cycle)
            return reflection

        next_action = self.action_queue[0]
        reflection = (
            f"Completed '{self.executed_actions[-1] if self.executed_actions else 'none'}'. "
            f"Moving to next: {next_action['tool']}. "
            f"{len(self.action_queue)} action(s) remaining."
        )
        self.memory.add_reflection(reflection, self.current_cycle)
        return reflection

    def step(self) -> Dict[str, Any]:
        return self.run_cycle()

    def run_cycle(self) -> Dict[str, Any]:
        if self.task_complete:
            cycle_result = {"status": "complete", "result": self.task_result}
            logger.info("Cycle skipped: task already complete")
            return cycle_result

        if self.current_cycle >= MAX_CYCLES:
            logger.warning("Max cycles (%d) reached. Stopping.", MAX_CYCLES)
            self.task_complete = True
            return {"status": "max_cycles_reached", "cycle": self.current_cycle}

        logger.info("%s", "=" * 60)
        logger.info("ReACT Cycle %d", self.current_cycle)
        logger.info("%s", "=" * 60)

        try:
            thought = self.think()
            logger.info("[THINK] %s", thought)

            action_result = self.act()
            tool_name = action_result.get("tool", "idle")
            logger.info("[ACT]   %s", tool_name)

            self.observe(action_result)
            logger.info("[OBSERVE] Stored result of %s", tool_name)

            reflection = self.reflect()
            logger.info("[REFLECT] %s", reflection)

            self.current_cycle += 1

            return {
                "cycle": self.current_cycle - 1,
                "thought": thought,
                "action": tool_name,
                "action_params": action_result.get("params"),
                "action_result": action_result.get("result"),
                "reflection": reflection,
                "task_complete": self.task_complete,
            }
        except Exception as e:
            logger.exception("Cycle %d failed: %s", self.current_cycle, e)
            self.error_count += 1
            self.current_cycle += 1
            return {
                "cycle": self.current_cycle - 1,
                "error": f"{type(e).__name__}: {str(e)}",
                "task_complete": False,
            }

    def run_full_task(self, task_type: str, params: Dict[str, Any]) -> Any:
        self.add_task(task_type, params)
        while not self.task_complete:
            self.run_cycle()
        return self.task_result

    def run_full_pipeline(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        results = []
        for task in tasks:
            result = self.run_full_task(task["tool"], task["params"])
            results.append(result)
            self.reset()
        return results

    def get_state(self) -> Dict[str, Any]:
        return {
            "thinking_state": self.thinking_state,
            "action_queue": self.action_queue,
            "current_cycle": self.current_cycle,
            "task_complete": self.task_complete,
            "task_result": self.task_result,
            "error_count": self.error_count,
            "executed_actions": self.executed_actions,
            "memory_summary": self.memory.to_summary(),
            "memory_log": self.memory.get_full_log(),
        }

    def process_transaction(
        self,
        amount: float,
        category: str,
        description: str,
        date: str,
    ) -> Dict[str, Any]:
        self.add_multiple_tasks([
            {"tool": "validate_transaction", "params": {"amount": amount, "category": category, "date": date}},
            {"tool": "categorize_expense", "params": {"description": description}},
        ])

        while not self.task_complete:
            self.run_cycle()

        validation_result = self.memory.get_observation("validate_transaction")
        categorization_result = self.memory.get_observation("categorize_expense")

        validation_confidence = validation_result.get("confidence", 0.0) if validation_result else 0.0
        categorization_confidence = categorization_result.get("confidence", 0.0) if categorization_result else 0.0
        detected_category = categorization_result.get("category", category) if categorization_result else category

        agent_confidence = round((validation_confidence * 0.4 + categorization_confidence * 0.6), 2)

        is_high_value = amount > 5000
        is_inconsistent = category != detected_category and categorization_confidence > 0.6

        if is_high_value:
            status = "flagged"
            self.memory.add_reflection(
                f"Transaction flagged: high-value amount ${amount:.2f} exceeds $5000 threshold.",
                self.current_cycle - 1,
            )
        elif is_inconsistent:
            status = "flagged"
            self.memory.add_reflection(
                f"Transaction flagged: provided category '{category}' differs from "
                f"detected '{detected_category}' (confidence {categorization_confidence}).",
                self.current_cycle - 1,
            )
        elif agent_confidence < 0.5:
            status = "pending"
        else:
            status = "confirmed"

        if not validation_result or not validation_result.get("valid", False):
            status = "flagged"

        return {
            "amount": amount,
            "category": category if not is_inconsistent else detected_category,
            "description": description,
            "date": date,
            "agent_confidence": agent_confidence,
            "status": status,
            "validation": validation_result,
            "categorization": categorization_result,
        }

    def reset(self) -> None:
        self.memory.clear()
        self.thinking_state = ""
        self.action_queue.clear()
        self.current_cycle = 0
        self.task_complete = False
        self.task_result = None
        self.error_count = 0
        self.executed_actions.clear()
        logger.info("Agent reset to initial state")
