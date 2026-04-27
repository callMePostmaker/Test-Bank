from src.main.api.models.base_model import BaseModel



class UserTransferRequest(BaseModel):
    fromAccountId: int
    toAccountId: int
    amount: float
