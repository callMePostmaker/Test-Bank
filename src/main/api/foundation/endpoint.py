from enum import Enum

from src.main.api.models.base_model import BaseModel
from typing import Optional, Type
from dataclasses import dataclass

from src.main.api.models.create_account_response import CreateAccountResponse
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.models.create_user_response import CreateUserResponse
from src.main.api.models.login_user_request import LoginUserRequest
from src.main.api.models.login_user_response import LoginUserResponse
from src.main.api.models.user_credit_request import UserCreditRequest
from src.main.api.models.user_deposit_request import UserDepositRequest
from src.main.api.models.user_deposit_response import UserDepositResponse
from src.main.api.models.user_transfer_request import UserTransferRequest
from src.main.api.models.user_transfer_response import UserTransferResponse
from src.main.api.models.user_credit_response import UserCreditResponse
from src.main.api.models.user_credit_repay_request import UserCreditRepayRequest
from src.main.api.models.user_credit_repay_response import UserCreditRepayResponse


@dataclass
class EndpointConfiguration:
    url: str
    request_model: Optional[Type[BaseModel]]
    response_model: Optional[Type[BaseModel]]


class Endpoint(Enum):
    ADMIN_CREATE_USER = EndpointConfiguration(
        request_model=CreateUserRequest,
        url='/admin/create',
        response_model=CreateUserResponse
    )

    ADMIN_DELETE_USER = EndpointConfiguration(
        request_model=None,
        url='/admin/users',
        response_model=None
    )

    LOGIN_USER = EndpointConfiguration(
        request_model=LoginUserRequest,
        url='/auth/token/login',
        response_model=LoginUserResponse
    )

    CREATE_ACCOUNT = EndpointConfiguration(
        request_model=None,
        url='/account/create',
        response_model=CreateAccountResponse
    )

    DEPOSIT_ACCOUNT = EndpointConfiguration(
        request_model=UserDepositRequest,
        url='/account/deposit',
        response_model=UserDepositResponse
    )

    TRANSFER_ACCOUNT = EndpointConfiguration(
        request_model=UserTransferRequest,
        url='/account/transfer',
        response_model=UserTransferResponse
    )

    CREDIT_ACCOUNT = EndpointConfiguration(
        request_model=UserCreditRequest,
        url='/credit/request',
        response_model=UserCreditResponse
    )

    CREDIT_REPAY = EndpointConfiguration(
        request_model=UserCreditRepayRequest,
        url='/credit/repay',
        response_model=UserCreditRepayResponse
    )
