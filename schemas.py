from uuid import UUID
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GoalBase(BaseModel):
    goal_name: str
    goal_type: str  # "short_term" or "long_term"
    target_amount: float
    deadline: datetime
    priority: str  # "low", "medium", "high"
    description: Optional[str] = None


class GoalCreate(GoalBase):
    user_id: str


class GoalSchema(GoalBase):
    goal_id: UUID
    user_id: str
    current_amount: float = 0.0
    status: str = "active"  # "active", "completed", "abandoned"
    created_at: datetime
    updated_at: datetime

    @property
    def progress_percentage(self) -> float:
        if self.target_amount == 0:
            return 0.0
        return round((self.current_amount / self.target_amount) * 100, 2)

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    category: str
    monthly_limit: float


class BudgetCreate(BudgetBase):
    user_id: str
    month: str


class BudgetSchema(BudgetBase):
    budget_id: UUID
    user_id: str
    spent_so_far: float = 0.0
    month: str
    created_at: datetime
    updated_at: datetime

    @property
    def spent_percentage(self) -> float:
        if self.monthly_limit == 0:
            return 0.0
        return round((self.spent_so_far / self.monthly_limit) * 100, 2)

    @property
    def remaining_amount(self) -> float:
        return round(self.monthly_limit - self.spent_so_far, 2)

    @property
    def status(self) -> str:
        pct = self.spent_percentage
        if pct >= 100:
            return "exceeded"
        elif pct >= 80:
            return "warning"
        return "ok"

    class Config:
        from_attributes = True


# ─── Legacy Models (required by existing routes) ──────────────────────────────


class TransactionInput(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    description: str = Field(default="")
    date: str = Field(default="", description="YYYY-MM-DD")


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    amount: float
    category: str
    description: str
    date: str
    created_at: str
    agent_confidence: float
    status: str


class CategorySummary(BaseModel):
    category: str
    count: int
    total: float


class AgentStateResponse(BaseModel):
    thinking_state: str
    current_cycle: int
    task_complete: bool
    error_count: int
    executed_actions: list
    memory_summary: str


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    version: str


class MessageResponse(BaseModel):
    message: str
