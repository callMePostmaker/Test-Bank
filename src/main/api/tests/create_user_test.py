import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.generators.model_generator import RandomModelGenerator
from src.main.api.models.create_user_request import CreateUserRequest
from sqlalchemy.orm import Session
from src.main.api.db.crud.user_crud import UserCrudDb as User


@pytest.mark.api
class TestCreateUser:
    @pytest.mark.parametrize(
        'create_user_request',
        [RandomModelGenerator.generate(CreateUserRequest)]
    )
    def test_create_user_valid(self, api_manager: ApiManager, create_user_request: CreateUserRequest, db_session: Session):
        response = api_manager.admin_steps.create_user(create_user_request)


        assert create_user_request.username == response.username
        assert create_user_request.role == response.role

        # user_from_db = User.get_user_by_username(db_session, create_user_request.username)
        # assert user_from_db.username == create_user_request.username


    @pytest.mark.parametrize(
        'username, password',
        [
            ('абв', 'Pas!sw0rd'),
            ('ab', 'Pas!sw0rd'),
            ('abc!', 'Pas!sw0rd'),
            ('Max1123', 'Pas!sв0rd'),
            ('Max1124', 'Pas!sw0'),
            ('Max1125', 'pas!sw0rd'),
            ('Max1126', 'PAS!SW0RD'),
            ('Max1127', 'Pas!sword'),
            ('Max1128', 'Passw0rdd')
        ]
    )
    def test_create_user_invalid(self, username, password, api_manager):
        create_user_request = CreateUserRequest(username=username, password=password, role="ROLE_USER")
        api_manager.admin_steps.create_invalid_user(create_user_request)




        