import logging
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from backend.agent.memory import AgentMemory
from backend.agent.tools import validate_transaction, categorize_expense, generate_summary

logger = logging.getLogger(__name__)

MAX_CYCLES = 10

_has_gemini = False
genai = None
try:
    import google.generativeai as genai_mod
    genai = genai_mod
    _has_gemini = True
except ImportError:
    pass


class BaseAgent(ABC):
    def __init__(self, name: str = "BaseAgent", gemini_api_key: Optional[str] = None):
        self.name = name
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.memory: List[Dict[str, Any]] = []
        self.thinking_history: List[Dict[str, Any]] = []
        self._model = None

        if gemini_api_key and _has_gemini:
            genai.configure(api_key=gemini_api_key)
            self._model = genai.GenerativeModel("gemini-2.5-flash")
        elif _has_gemini:
            try:
                genai.configure()
                self._model = genai.GenerativeModel("gemini-2.5-flash")
            except Exception:
                pass

    def register_tool(self, name: str, func: Callable, description: str) -> None:
        self.tools[name] = {"function": func, "description": description}
        logger.info("Tool registered: %s", name)

    def think(self, prompt: str) -> str:
        system_prompt = f"""
You are {self.name}, an AI agent.

Available tools:
{json.dumps({n: t['description'] for n, t in self.tools.items()}, indent=2)}

Analyze the user's request and decide:
1. What's the goal?
2. Which tools do I need?
3. In what order?
4. What's my approach?

Be concise and direct.
"""
        if self._model:
            response = self._model.generate_content(f"{system_prompt}\n\nUser request: {prompt}")
            thinking = response.text
        else:
            thinking = f"[{self.name} thinking about: {prompt[:100]}...]"

        self.thinking_history.append({"timestamp": __import__("datetime").datetime.now().isoformat(), "thinking": thinking})
        logger.info("[THINK] %s", thinking[:200])
        return thinking

    def act(self, tool_name: str, *args, **kwargs) -> Any:
        if tool_name not in self.tools:
            logger.warning("Tool '%s' not found", tool_name)
            return {"error": f"Tool '{tool_name}' not found"}
        try:
            result = self.tools[tool_name]["function"](*args, **kwargs)
            logger.info("[ACT] %s executed", tool_name)
            return result
        except Exception as e:
            logger.error("Tool %s error: %s", tool_name, e)
            return {"error": str(e)}

    def observe(self, thinking: str, action_result: Any) -> str:
        if self._model:
            obs_prompt = f"""
My thinking was: {thinking}

Tool result: {json.dumps(action_result, default=str)}

Based on this result:
1. Is the task complete?
2. Do I need more tools?
3. What's the final answer?
"""
            response = self._model.generate_content(obs_prompt)
            observation = response.text
        else:
            observation = f"[Observed result of previous action]"

        logger.info("[OBSERVE] %s", observation[:200])
        return observation

    def react_loop(self, prompt: str, max_iterations: int = 3) -> str:
        logger.info("Starting ReACT loop: %s", prompt[:100])
        for iteration in range(max_iterations):
            thinking = self.think(prompt)
            if self._model:
                final_response = self._model.generate_content(f"Based on your analysis, provide the final answer: {prompt}")
                answer = final_response.text
            else:
                answer = f"[{self.name} processed: {prompt[:100]}]"

            self.memory.append({
                "iteration": iteration + 1,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
                "prompt": prompt,
                "thinking": thinking,
                "answer": answer,
            })
            return answer
        return "Max iterations reached"

    @abstractmethod
    def process(self, prompt: str) -> str:
        raise NotImplementedError

    def get_memory(self) -> List[Dict[str, Any]]:
        return self.memory

    def clear_memory(self) -> None:
        self.memory.clear()
        self.thinking_history.clear()

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tools": list(self.tools.keys()),
            "memory_size": len(self.memory),
            "thinking_history": len(self.thinking_history),
        }


class FinanceTrackerAgent(BaseAgent):
    def __init__(self, gemini_api_key: Optional[str] = None):
        super().__init__(name="FinanceTrackerAgent", gemini_api_key=gemini_api_key)
        self.memory = AgentMemory()
        self.thinking_state: str = ""
        self.action_queue: List[Dict[str, Any]] = []
        self.current_cycle: int = 0
        self.task_complete: bool = False
        self.task_result: Any = None
        self.error_count: int = 0
        self.executed_actions: List[str] = []

        self.register_tool("validate_transaction", validate_transaction, "Validates a transaction's amount, category, and date format")
        self.register_tool("categorize_expense", categorize_expense, "Categorizes an expense based on description keywords")
        self.register_tool("generate_summary", generate_summary, "Generates spending summary from a list of transactions")

    def add_task(self, task_type: str, params: Dict[str, Any]) -> None:
        self.action_queue.append({"tool": task_type, "params": params})
        self.task_complete = False
        self.task_result = None
        self.current_cycle = 0
        self.executed_actions.clear()

    def add_multiple_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        for task in tasks:
            self.action_queue.append(task)
        self.task_complete = False
        self.task_result = None
        self.current_cycle = 0
        self.executed_actions.clear()

    def think(self) -> str:
        if not self.action_queue:
            self.thinking_state = "No pending actions. Task complete."
            self.task_complete = True
            return self.thinking_state
        next_action = self.action_queue[0]
        tool_name = next_action["tool"]
        params = next_action["params"]
        if tool_name == "validate_transaction":
            thought = f"Need to validate transaction: amount={params.get('amount')}, category={params.get('category')}, date={params.get('date')}. Will check amount>0, valid category, and valid date format."
        elif tool_name == "categorize_expense":
            thought = f"Need to categorize: '{params.get('description')}'. Will match keywords against known categories."
        elif tool_name == "generate_summary":
            thought = f"Need to generate summary for {len(params.get('transactions', []))} transactions. Will calculate totals and group by category."
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
        self.memory.add_action(tool_name, params, self.current_cycle)
        tool_fn_map = {
            "validate_transaction": lambda: validate_transaction(amount=params.get("amount", 0), category=params.get("category", ""), date=params.get("date", "")),
            "categorize_expense": lambda: categorize_expense(description=params.get("description", "")),
            "generate_summary": lambda: generate_summary(transactions_list=params.get("transactions", [])),
        }
        if tool_name in tool_fn_map:
            try:
                result = tool_fn_map[tool_name]()
            except Exception as e:
                result = {"error": f"{type(e).__name__}: {str(e)}"}
                self.error_count += 1
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
            logger.warning("Observation: Tool %s returned error: %s", tool_name, result["error"])

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
        reflection = f"Completed '{self.executed_actions[-1] if self.executed_actions else 'none'}'. Moving to next: {next_action['tool']}. {len(self.action_queue)} action(s) remaining."
        self.memory.add_reflection(reflection, self.current_cycle)
        return reflection

    def run_cycle(self) -> Dict[str, Any]:
        if self.task_complete:
            return {"status": "complete", "result": self.task_result}
        if self.current_cycle >= MAX_CYCLES:
            logger.warning("Max cycles (%d) reached. Stopping.", MAX_CYCLES)
            self.task_complete = True
            return {"status": "max_cycles_reached", "cycle": self.current_cycle}
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
            return {"cycle": self.current_cycle - 1, "thought": thought, "action": tool_name, "action_params": action_result.get("params"), "action_result": action_result.get("result"), "reflection": reflection, "task_complete": self.task_complete}
        except Exception as e:
            logger.exception("Cycle %d failed: %s", self.current_cycle, e)
            self.error_count += 1
            self.current_cycle += 1
            return {"cycle": self.current_cycle - 1, "error": f"{type(e).__name__}: {str(e)}", "task_complete": False}

    def process_transaction(self, amount: float, category: str, description: str, date: str) -> Dict[str, Any]:
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
        elif is_inconsistent:
            status = "flagged"
        elif agent_confidence < 0.5:
            status = "pending"
        else:
            status = "confirmed"
        if not validation_result or not validation_result.get("valid", False):
            status = "flagged"
        return {
            "amount": amount, "category": category if not is_inconsistent else detected_category,
            "description": description, "date": date, "agent_confidence": agent_confidence,
            "status": status, "validation": validation_result, "categorization": categorization_result,
        }

    def process(self, prompt: str) -> str:
        return str(self.process_transaction(0, "Other", prompt, ""))

    def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tools": list(self.tools.keys()),
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

    def reset(self) -> None:
        self.memory.clear()
        self.thinking_state = ""
        self.action_queue.clear()
        self.current_cycle = 0
        self.task_complete = False
        self.task_result = None
        self.error_count = 0
        self.executed_actions.clear()
