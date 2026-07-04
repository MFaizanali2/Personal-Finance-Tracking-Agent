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


class TransactionMetadata(BaseModel):
    agent_reasoning: str = ""
    original_category_suggestion: str = ""


class TransactionInput(BaseModel):
    user_id: str = "default"
    amount: float = Field(..., gt=0)
    category: str
    description: str
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    tags: list[str] = []
    recurring: bool = False
    recurring_frequency: str = ""


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    recurring: Optional[bool] = None
    recurring_frequency: Optional[str] = None
    agent_notes: Optional[str] = None
    agent_confidence: Optional[float] = None
    metadata: Optional[TransactionMetadata] = None


class TransactionDocument(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = "default"
    amount: float
    category: str
    description: str
    date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_confidence: float = 0.0
    status: str = "pending"
    agent_notes: str = ""
    tags: list[str] = []
    recurring: bool = False
    recurring_frequency: str = ""
    metadata: TransactionMetadata = Field(default_factory=TransactionMetadata)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True


class TransactionResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    amount: float
    category: str
    description: str
    date: str
    created_at: str
    updated_at: str
    agent_confidence: float
    status: str
    agent_notes: str
    tags: list[str]
    recurring: bool
    recurring_frequency: str
    metadata: TransactionMetadata

    class Config:
        populate_by_name = True


def doc_to_response(doc: dict) -> dict:
    return {
        "_id": str(doc["_id"]),
        "user_id": doc.get("user_id", "default"),
        "amount": doc["amount"],
        "category": doc["category"],
        "description": doc["description"],
        "date": doc["date"].strftime("%Y-%m-%d") if isinstance(doc["date"], datetime) else doc["date"],
        "created_at": doc["created_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get("created_at"), datetime) else "",
        "updated_at": doc["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(doc.get("updated_at"), datetime) else "",
        "agent_confidence": doc.get("agent_confidence", 0.0),
        "status": doc.get("status", "pending"),
        "agent_notes": doc.get("agent_notes", ""),
        "tags": doc.get("tags", []),
        "recurring": doc.get("recurring", False),
        "recurring_frequency": doc.get("recurring_frequency", ""),
        "metadata": doc.get("metadata", {"agent_reasoning": "", "original_category_suggestion": ""}),
    }


Transaction = TransactionDocument
