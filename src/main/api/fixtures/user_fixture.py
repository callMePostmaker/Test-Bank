from random import randint
import pytest

from src.main.api.models.create_creditor_request import CreateCreditorRequest
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.model_generator import RandomModelGenerator
from src.main.api.models.user_credit_request import UserCreditRequest
from src.main.api.models.user_deposit_request import UserDepositRequest


@pytest.fixture
def create_user_request(api_manager):
    user_request = RandomModelGenerator.generate(CreateUserRequest)
    api_manager.admin_steps.create_user(user_request)
    return user_request

@pytest.fixture
def create_receiver_request(api_manager):
    user_request = RandomModelGenerator.generate(CreateUserRequest)
    api_manager.admin_steps.create_user(user_request)
    return user_request


@pytest.fixture
def create_creditor_request(api_manager):
    creditor_request = RandomModelGenerator.generate(CreateCreditorRequest)
    api_manager.admin_steps.create_user(creditor_request)
    return creditor_request


@pytest.fixture
def create_account_user_id(api_manager, create_user_request):
    create_account_response = api_manager.user_steps.create_account(create_user_request)
    return create_account_response.id

@pytest.fixture
def create_receiver_account_id(api_manager, create_receiver_request):
    create_account_response = api_manager.user_steps.create_account(create_receiver_request)
    return create_account_response.id

@pytest.fixture
def create_creditor_account_user_id(api_manager, create_creditor_request):
    create_account_response = api_manager.user_steps.create_account(create_creditor_request)
    return create_account_response.id

@pytest.fixture
def user_deposited_account(api_manager, create_user_request, create_account_user_id):
    deposit_account_request = UserDepositRequest(accountId=create_account_user_id, amount=randint(500000, 700000)/100)
    user_deposited_account = api_manager.user_steps.deposit_account(create_user_request, deposit_account_request)
    return user_deposited_account.accountId

@pytest.fixture
def credit_account_request(create_creditor_account_user_id):
    credit_account_request = UserCreditRequest(accountId=create_creditor_account_user_id, amount=5000, termMonths=randint(6,24))
    return credit_account_request

@pytest.fixture
def create_credit_id(api_manager, create_creditor_request, credit_account_request):
    create_credit_response = api_manager.user_steps.credit_request(create_creditor_request, credit_account_request)

    return create_credit_response.creditId





