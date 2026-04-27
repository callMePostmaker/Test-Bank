from random import random, randint
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.user_deposit_request import UserDepositRequest


class TestDeposit:
    def test_deposit(self, api_manager, create_user_request: CreateUserRequest, create_account_user_id):
        deposit_account_request = UserDepositRequest(accountId=create_account_user_id, amount=randint(100000, 900000)/100)
        response = api_manager.user_steps.deposit_account(create_user_request, deposit_account_request)

        assert response.balance == deposit_account_request.amount
