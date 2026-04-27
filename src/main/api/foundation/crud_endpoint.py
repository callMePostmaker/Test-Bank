from typing import Protocol, Optional
from src.main.api.models.base_model import BaseModel
from requests import Response



class CrudEndpoint(Protocol):
    def post(self, model: Optional[BaseModel]) -> BaseModel | Response: ...
    def get(self, user_id: int) -> BaseModel | Response: ...
    def delete(self, user_id: int) -> BaseModel | Response: ...
