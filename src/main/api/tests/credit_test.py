from random import random, randint

from src.main.api.models.create_creditor_request import CreateCreditorRequest
from src.main.api.models.user_credit_request import UserCreditRequest




class TestCredit:
    def test_credit(self, api_manager, create_creditor_request: CreateCreditorRequest, create_creditor_account_user_id):
        credit_account_request = UserCreditRequest(accountId=create_creditor_account_user_id, amount=randint(500000, 1500000)/100, termMonths=randint(6,24))
        response = api_manager.user_steps.credit_request(create_creditor_request, credit_account_request)

        assert response.balance == credit_account_request.amount
