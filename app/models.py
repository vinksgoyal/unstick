from typing import Any

from pydantic import BaseModel, Field


class UnstickRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=2000)
    minutes: int = Field(ge=1, le=60)
    energy: int = Field(ge=1, le=5)
    location: str = Field(min_length=1, max_length=100)
    time: str = Field(min_length=1, max_length=20)


class CompleteRequest(BaseModel):
    goal_id: str = Field(min_length=1, max_length=200)
    action_id: str = Field(min_length=1, max_length=200)
    completed: bool


class Action(BaseModel):
    text: str
    constraints: dict[str, Any]
    estimated_minutes: int = Field(default=5, ge=1, le=5)


class UnstickResponse(BaseModel):
    start_here: Action
    if_you_have_15: Action
    not_today: dict[str, str]
    model_used: str
    privacy_note: str
