import pytest
from playwright.sync_api import expect
from ui.pages.catalog_page import CatalogPage
from ui.pages.login_page import LoginPage
from ui.steps.login_steps import LoginSteps
from ui.steps.catalog_steps import CatalogSteps

def test_auth(page):
    steps = LoginSteps(page)
    steps.open_login_page().login('standard_user', 'secret_sauce')

    # Проверяем, что находимся на странице каталога после успешного логина
    catalog_page = CatalogPage(page)
    assert catalog_page.get_products_count() > 0


def test_auth_locked_out_user(page):
    steps = LoginSteps(page)
    steps.open_login_page().login('locked_out_user', 'secret_sauce')

    error_text = steps.get_error_message()
    assert 'locked out' in error_text, 'Ожидаем сообщение о заблокированном пользователе'


def test_logout(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')

    assert steps.get_products_count() > 0
    assert steps.get_products_in_cart_count() == 0

    steps.logout()
    expect(page).to_have_url(CatalogPage.URL)


def test_logout_visual_user(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')

    assert steps.get_products_count() > 0
    assert steps.get_products_in_cart_count() == 0

    steps.logout()
    expect(page).to_have_url(CatalogPage.URL)

    

