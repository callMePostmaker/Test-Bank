import pytest
from sqlalchemy.orm import Session

from src.main.api.classes.api_manager import ApiManager
from src.main.api.db.crud.account_crud import AccountCrudDb as Account
from src.main.api.models.create_user_request import CreateUserRequest



@pytest.mark.api
class TestCreateAccount:
    def test_create_account(self, db_session: Session, api_manager: ApiManager, create_user_request: CreateUserRequest):
        response = api_manager.user_steps.create_account(create_user_request)

        assert response.balance == 0

        account_from_db = Account.get_account_by_id(db_session, response.account_id)
        assert account_from_db.id == response.id, 'Аккаунт не создан, id аккаунта нет в БД'
        assert account_from_db.balance is not None, 'Поле баланса для созданного аккаунта отсутсвует в БД'
        

