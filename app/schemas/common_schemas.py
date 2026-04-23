from pydantic import BaseModel
from typing import Optional

class GenerateRequest(BaseModel):
    user_hint: Optional[str] = None 