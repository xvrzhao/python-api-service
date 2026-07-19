from typing import Any
from pydantic import BaseModel

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ResumeRequest(BaseModel):
    thread_id: str
    resume_value: Any