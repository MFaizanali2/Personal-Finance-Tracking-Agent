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


class GoalInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_amount: float = Field(..., gt=0)
    current_amount: float = 0
    category: str = "General"
    deadline: str = Field(..., description="YYYY-MM-DD")
    monthly_contribution: float = 0


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    target_amount: Optional[float] = Field(None, gt=0)
    current_amount: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    deadline: Optional[str] = None
    monthly_contribution: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None


class GoalDocument(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = "default"
    name: str
    target_amount: float
    current_amount: float = 0
    category: str = "General"
    deadline: datetime
    monthly_contribution: float = 0
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True


class GoalResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    name: str
    target_amount: float
    current_amount: float
    category: str
    deadline: str
    monthly_contribution: float
    status: str
    progress_pct: float = 0
    created_at: str
    updated_at: str

    class Config:
        populate_by_name = True


Goal = GoalDocument


def goal_doc_to_response(doc: dict) -> dict:
    target = doc.get("target_amount", 1)
    current = doc.get("current_amount", 0)
    progress = round(min(current / target * 100, 100), 1) if target > 0 else 0
    return {
        "_id": str(doc["_id"]),
        "user_id": doc.get("user_id", "default"),
        "name": doc["name"],
        "target_amount": doc["target_amount"],
        "current_amount": doc.get("current_amount", 0),
        "category": doc.get("category", "General"),
        "deadline": doc["deadline"].strftime("%Y-%m-%d") if isinstance(doc["deadline"], datetime) else str(doc["deadline"])[:10],
        "monthly_contribution": doc.get("monthly_contribution", 0),
        "status": doc.get("status", "active"),
        "progress_pct": progress,
        "created_at": doc["created_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get("created_at"), datetime) else "",
        "updated_at": doc["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get("updated_at"), datetime) else "",
    }
