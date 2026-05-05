from random import randint

from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.user_transfer_request import UserTransferRequest


class TestTransfer:
    def test_transfer(self, api_manager, create_user_request: CreateUserRequest, user_deposited_account, create_receiver_account_id):
        user_transfer_request = UserTransferRequest(fromAccountId=user_deposited_account, toAccountId=create_receiver_account_id, amount=randint(100000, 500000)/100)
        response = api_manager.user_steps.user_transfer(create_user_request, user_transfer_request)

        assert response.fromAccountIdBalance >= 0


    def test_invalid_transfer(self, api_manager, create_user_request: CreateUserRequest, user_deposited_account, create_receiver_account_id):
        user_transfer_request = UserTransferRequest(fromAccountId=user_deposited_account, toAccountId=create_receiver_account_id, amount=randint(700000, 900000)/100)
        response = api_manager.user_steps.user_invalid_transfer(create_user_request, user_transfer_request)


