from src.main.api.models.base_model import BaseModel



class UserCreditRepayResponse(BaseModel):
    creditId: int
    amountDeposited: float
