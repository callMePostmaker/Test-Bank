from random import random, randint
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_creditor_request import CreateCreditorRequest
from src.main.api.models.user_credit_repay_request import UserCreditRepayRequest


class TestRepay:
    def test_repay(self, api_manager, create_creditor_request: CreateCreditorRequest, create_creditor_account_user_id, create_credit_id):
        repay_credit_request = UserCreditRepayRequest(creditId=create_credit_id, accountId=create_creditor_account_user_id, amount=5000)
        response = api_manager.user_steps.credit_repay(create_creditor_request, repay_credit_request)

        assert response.amountDeposited == repay_credit_request.amount
