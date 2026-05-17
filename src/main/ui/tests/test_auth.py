import pytest

from src.main.ui.pages import login_page
from src.main.ui.pages.catalog_page import CatalogPage
from src.main.ui.pages.login_page import LoginPage
from playwright.sync_api import expect

def test_auth(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login('standard_user', 'secret_sauce')

    expect(page).to_have_url('https://www.saucedemo.com/inventory.html')


def test_auth_locked_out_user(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login('locked_out_user', 'secret_sauce')

    expect(page).to_have_url(LoginPage.URL)

    error_text = login_page.get_error_text()
    assert 'locked out' in error_text, 'была вызвана другая ошибка'


def test_logout(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login('standard_user', 'secret_sauce')

    catalog_page = CatalogPage(page)
    assert catalog_page.get_products_count() > 0

    catalog_page.logout()
    expect(page).to_have_url(LoginPage.URL)


def test_logout_visual_user(page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login('standard_user', 'secret_sauce')

    catalog_page = CatalogPage(page)
    assert catalog_page.get_products_count() > 0

    catalog_page.logout()
    expect(page).to_have_url(LoginPage.URL)

    

