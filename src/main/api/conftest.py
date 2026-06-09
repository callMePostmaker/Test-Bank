import pytest
from src.main.api.fixtures.api_fixture import *
from src.main.api.fixtures.object_fixture import *
from src.main.api.fixtures.user_fixture import *
from src.main.api.fixtures.db_fixture import *

def pytest_collection_modify_items(items):
    """Автоматически вешаем маркер api на ВСЕ тесты в этой директории и ниже."""
    for item in items:
        item.add_marker(pytest.mark.api)

