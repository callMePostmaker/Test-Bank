from src.main.api.configs.config import Config
from src.main.api.foundation.http_requester import HttpRequester
from src.main.api.models.base_model import BaseModel
from requests import Response
from typing import Optional
import requests
import allure



class CrudRequester(HttpRequester):
    def post(self, model: Optional[BaseModel]) -> BaseModel | Response:
        body = model.model_dump() if model is not None else ''

        with allure.step(f'post {Config.fetch('backendUrl')}{self.endpoint.value.url}'):
            allure.attach(str(body), "Request body", allure.attachment_type.JSON)

        response = requests.post(
            url=f'{Config.fetch('backendUrl')}{self.endpoint.value.url}',
            headers=self.request_spec,
            json=body
        )

        allure.attach(
            response.text,
            'Response body',
            allure.attachment_type.JSON
        )
        self.response_spec(response)
        return response

    def delete(self, user_id: int) -> BaseModel | Response:
        response = requests.delete(
            url=f'{Config.fetch('backendUrl')}{self.endpoint.value.url}/{user_id}',
            headers=self.request_spec
        )
        self.response_spec(response)
        return response























