from pydantic import Field
from src.main.api.models.base_model import BaseModel



class UserDepositRequest(BaseModel):
    accountId: int = Field(allias='id')
    amount: float