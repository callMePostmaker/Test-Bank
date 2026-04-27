from src.main.api.models.base_model import BaseModel



class UserTransferResponse(BaseModel):
    fromAccountId: int
    toAccountId: int
    fromAccountIdBalance: float
