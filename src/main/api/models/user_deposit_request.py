from pydantic import Field, ConfigDict
from src.main.api.models.base_model import BaseModel


class UserDepositRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    accountId: int = Field(alias='id')
    amount: float