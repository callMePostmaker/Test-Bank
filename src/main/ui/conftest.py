from src.main.ui.fixtures.fixtures import *



def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.ui)