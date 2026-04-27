from src.main.api.models.base_model import BaseModel
from pydantic import Field

class UserDepositResponse(BaseModel):
    accountId: int = Field(alias="id")
    balance: float