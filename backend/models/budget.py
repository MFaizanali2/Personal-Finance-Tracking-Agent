from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid ObjectId")


DEFAULT_BUDGET_CATEGORIES = {
    "Food": 500,
    "Transport": 200,
    "Entertainment": 300,
    "Shopping": 400,
    "Utilities": 150,
    "Medical": 200,
    "Rent": 2000,
    "Other": 100,
}


class BudgetInput(BaseModel):
    month: str
    budgets: dict[str, float]


class BudgetDocument(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = "default"
    month: str
    budgets: dict[str, float]
    total_budget: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True


class BudgetResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    month: str
    budgets: dict[str, float]
    total_budget: float
    created_at: str
    updated_at: str

    class Config:
        populate_by_name = True


Budget = BudgetDocument


def budget_doc_to_response(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "user_id": doc.get("user_id", "default"),
        "month": doc["month"],
        "budgets": doc["budgets"],
        "total_budget": doc.get("total_budget", sum(doc["budgets"].values())),
        "created_at": doc["created_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get("created_at"), datetime) else "",
        "updated_at": doc["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get("updated_at"), datetime) else "",
    }
