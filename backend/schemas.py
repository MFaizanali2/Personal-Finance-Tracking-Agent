from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
