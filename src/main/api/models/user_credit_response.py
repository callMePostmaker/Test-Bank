from pydantic import Field

from src.main.api.models.base_model import BaseModel



class UserCreditResponse(BaseModel):
    accountId: int = Field(alias='id')
    amount: float
    termMonths: int
    balance: float
    creditId: int
