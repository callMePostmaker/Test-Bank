from src.main.ui.fixtures.fixtures import *

@pytest.fixture
def auth_page(page):
    page.goto('https://www.saucedemo.com')
    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')
    page.locator('#login-button').click()
    return page