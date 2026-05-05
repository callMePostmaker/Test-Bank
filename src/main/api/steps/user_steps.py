from src.main.api.foundation.endpoint import Endpoint
from src.main.api.foundation.requesters.crud_requester import CrudRequester
from src.main.api.foundation.requesters.validate_crud_requester import ValidateCrudRequester
from src.main.api.steps.base_steps import BaseSteps
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.specs.request_specs import RequestSpecs
from src.main.api.specs.response_specs import ResponseSpecs
from src.main.api.models.user_deposit_request import UserDepositRequest
from src.main.api.models.create_creditor_request import CreateCreditorRequest


class UserSteps(BaseSteps):
    def create_account(self, create_user_request: CreateUserRequest):
        response = ValidateCrudRequester(
            RequestSpecs.auth_headers(username=create_user_request.username, password=create_user_request.password),
            Endpoint.CREATE_ACCOUNT,
            ResponseSpecs.request_created()
        ).post()
        return response

    def deposit_account(self, create_user_request: CreateUserRequest, deposit_account):
        response = ValidateCrudRequester(
            RequestSpecs.auth_headers(username=create_user_request.username, password=create_user_request.password),
            Endpoint.DEPOSIT_ACCOUNT,
            ResponseSpecs.request_ok()
        ).post(deposit_account)
        return response

    def unauthorized_deposit_account(self, create_user_request: CreateUserRequest, deposit_account):
        response = CrudRequester(
            RequestSpecs.unauth_headers(),
            Endpoint.DEPOSIT_ACCOUNT,
            ResponseSpecs.request_unauthorized()
        ).post(deposit_account)
        return response

    def credit_request(self, create_creditor_request: CreateCreditorRequest, credit_account):
        response = ValidateCrudRequester(
            RequestSpecs.auth_headers(username=create_creditor_request.username, password=create_creditor_request.password),
            Endpoint.CREDIT_ACCOUNT,
            ResponseSpecs.request_created()
        ).post(credit_account)
        return response

    def invalid_credit_request(self, create_creditor_request: CreateCreditorRequest, credit_account):
        response = CrudRequester(
            RequestSpecs.auth_headers(username=create_creditor_request.username, password=create_creditor_request.password),
            Endpoint.CREDIT_ACCOUNT,
            ResponseSpecs.request_not_found()
        ).post(credit_account)
        return response

    def credit_repay(self, create_creditor_request: CreateCreditorRequest, credit_repay):
        response = ValidateCrudRequester(
            RequestSpecs.auth_headers(username=create_creditor_request.username, password=create_creditor_request.password),
            Endpoint.CREDIT_REPAY,
            ResponseSpecs.request_ok()
        ).post(credit_repay)
        return response

    def invalid_credit_repay(self, create_creditor_request: CreateCreditorRequest, credit_repay):
        response = CrudRequester(
            RequestSpecs.auth_headers(username=create_creditor_request.username, password=create_creditor_request.password),
            Endpoint.CREDIT_REPAY,
            ResponseSpecs.request_forbidden()
        ).post(credit_repay)
        return response

    def user_transfer(self, create_user_request: CreateUserRequest, transfer_request):
        response = ValidateCrudRequester(
            RequestSpecs.auth_headers(username=create_user_request.username, password=create_user_request.password),
            Endpoint.TRANSFER_ACCOUNT,
            ResponseSpecs.request_ok()
        ).post(transfer_request)
        return response

    def user_invalid_transfer(self, create_user_request: CreateUserRequest, transfer_request):
        response = CrudRequester(
            RequestSpecs.auth_headers(username=create_user_request.username, password=create_user_request.password),
            Endpoint.TRANSFER_ACCOUNT,
            ResponseSpecs.request_unprocessable_entity()
        ).post(transfer_request)
        return response



