from typing import Annotated

from src.main.api.models.base_model import BaseModel
from src.main.api.generators.creation_rule import CreationRule


class CreateCreditorRequest(BaseModel):
    username: Annotated[str, CreationRule(regex=r'^[A-Za-z0-9]{3,15}$')]
    password: Annotated[str, CreationRule(regex=r'^[A-Z]{3}[a-z]{1}[0-9]{2}[!$_]{4}$')]
    role: Annotated[str, CreationRule(regex=r'^ROLE_CREDIT_SECRET')]

