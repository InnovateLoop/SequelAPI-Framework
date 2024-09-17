from pydantic import BaseModel
from typing import Literal

class Activity(BaseModel):
    time: Literal["morning", "afternoon", "evening", "night"]
    activity: str

class Day(BaseModel):
    activities: list[Activity]

class Plan(BaseModel):
    summary: str
    days: list[Day]