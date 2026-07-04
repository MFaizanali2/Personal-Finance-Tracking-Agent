from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES: List[str] = [
    "Food", "Rent", "Transport", "Entertainment",
    "Medical", "Shopping", "Utilities", "Other",
]


class TransactionInput(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount (must be > 0)")
    category: str = Field(..., min_length=1, description="Expense category")
    description: str = Field(..., min_length=1, max_length=500, description="Transaction description")
    date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        description="Transaction date (YYYY-MM-DD), defaults to today",
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Must be one of: {', '.join(VALID_CATEGORIES)}")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{v}'. Use YYYY-MM-DD.")
        return v


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0, description="Transaction amount (must be > 0)")
    category: Optional[str] = Field(default=None, min_length=1, description="Expense category")
    description: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Transaction description")
    date: Optional[str] = Field(default=None, description="Transaction date (YYYY-MM-DD)")
    status: Optional[str] = Field(default=None, description="Transaction status: pending, confirmed, or flagged")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Must be one of: {', '.join(VALID_CATEGORIES)}")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{v}'. Use YYYY-MM-DD.")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("pending", "confirmed", "flagged"):
            raise ValueError("Status must be: pending, confirmed, or flagged")
        return v


class TransactionResponse(BaseModel):
    id: str = Field(..., description="Unique transaction ID")
    amount: float = Field(..., description="Transaction amount")
    category: str = Field(..., description="Expense category")
    description: str = Field(..., description="Transaction description")
    date: str = Field(..., description="Transaction date (YYYY-MM-DD)")
    created_at: str = Field(..., description="ISO timestamp of creation")
    agent_confidence: float = Field(..., ge=0, le=1, description="Agent confidence score (0-1)")
    status: str = Field(..., description="Transaction status: pending, confirmed, or flagged")


class CategorySummary(BaseModel):
    category: str = Field(..., description="Expense category")
    count: int = Field(..., ge=0, description="Number of transactions in category")
    total: float = Field(..., ge=0, description="Total amount spent in category")


class AgentStateResponse(BaseModel):
    thinking_state: str = Field(..., description="Current agent reasoning")
    current_cycle: int = Field(..., description="Current ReACT cycle number")
    task_complete: bool = Field(..., description="Whether current task is done")
    error_count: int = Field(..., description="Number of errors encountered")
    executed_actions: List[str] = Field(default_factory=list, description="Actions executed in current task")
    memory_summary: Dict[str, Any] = Field(..., description="Summary of agent memory")
    memory_log: Dict[str, Any] = Field(default_factory=dict, description="Full agent memory log")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")


class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


GOAL_TYPES = ["short_term", "long_term"]
GOAL_PRIORITIES = ["low", "medium", "high"]
GOAL_STATUSES = ["active", "completed", "abandoned"]


class GoalSchema(BaseModel):
    goal_id: str = Field(default="", description="Unique goal identifier (UUID)", examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"])
    user_id: str = Field(..., min_length=1, description="User identifier", examples=["user123"])
    goal_name: str = Field(..., min_length=1, max_length=200, description="Name of the savings goal", examples=["Emergency Fund", "Vacation"])
    goal_type: str = Field(..., description="Type of goal: short_term or long_term", examples=["short_term", "long_term"])
    target_amount: float = Field(..., gt=0, description="Target amount to save (must be > 0)", examples=[10000.00, 5000.00])
    current_amount: float = Field(default=0, ge=0, description="Amount saved so far", examples=[2500.00])
    deadline: datetime = Field(..., description="Target deadline for the goal", examples=["2026-12-31T00:00:00"])
    priority: str = Field(default="medium", description="Priority level: low, medium, or high", examples=["high", "medium", "low"])
    status: str = Field(default="active", description="Goal status: active, completed, or abandoned", examples=["active", "completed", "abandoned"])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the goal was created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the goal was last updated")
    description: Optional[str] = Field(default=None, max_length=1000, description="Optional description or notes for the goal", examples=["Save $10,000 for a down payment on a house"])

    @field_validator("goal_type")
    @classmethod
    def validate_goal_type(cls, v: str) -> str:
        if v not in GOAL_TYPES:
            raise ValueError(f"Invalid goal_type '{v}'. Must be one of: {', '.join(GOAL_TYPES)}")
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_target_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("target_amount must be greater than 0")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in GOAL_PRIORITIES:
            raise ValueError(f"Invalid priority '{v}'. Must be one of: {', '.join(GOAL_PRIORITIES)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in GOAL_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Must be one of: {', '.join(GOAL_STATUSES)}")
        return v


ALERT_THRESHOLDS = [80, 100]


class BudgetSchema(BaseModel):
    budget_id: str = Field(default="", description="Unique budget identifier (UUID)", examples=["b1c2d3e4-f5a6-7890-abcd-ef1234567890"])
    user_id: str = Field(..., min_length=1, description="User identifier", examples=["user123"])
    category: str = Field(..., min_length=1, description="Expense category for the budget", examples=["Food", "Transport", "Entertainment"])
    monthly_limit: float = Field(..., gt=0, description="Monthly spending limit for this category (must be > 0)", examples=[500.00, 200.00, 300.00])
    spent_so_far: float = Field(default=0, ge=0, description="Amount spent so far this month", examples=[320.50])
    threshold_alerts: list[bool] = Field(default_factory=lambda: [True, True], description="Alert flags for threshold percentages [80%, 100%]", examples=[[True, True], [True, False]])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the budget was created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the budget was last updated")
    month: str = Field(..., description="Budget month in YYYY-MM format", examples=["2026-07", "2026-08"])

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Must be one of: {', '.join(VALID_CATEGORIES)}")
        return v

    @field_validator("monthly_limit")
    @classmethod
    def validate_monthly_limit(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("monthly_limit must be greater than 0")
        return v

    @field_validator("threshold_alerts")
    @classmethod
    def validate_threshold_alerts(cls, v: list[bool]) -> list[bool]:
        if len(v) != 2:
            raise ValueError("threshold_alerts must have exactly 2 booleans (for 80% and 100%)")
        return v

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        from datetime import datetime as dt
        try:
            dt.strptime(v, "%Y-%m")
        except ValueError:
            raise ValueError(f"Invalid month format '{v}'. Use YYYY-MM (e.g. 2026-07).")
        return v
