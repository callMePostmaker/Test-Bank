from src.main.api.models.base_model import BaseModel



class UserCreditRepayRequest(BaseModel):
    creditId: int
    accountId: int
    amount: float
