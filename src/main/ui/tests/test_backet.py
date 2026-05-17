import pytest

from src.main.ui.pages import catalog_page
from src.main.ui.pages.catalog_page import CatalogPage
from src.main.ui.pages.basket_page import BasketPage
from src.main.ui.pages.checkout_page import CheckoutPage


def test_item_and_check_in_cart(page):
    catalog_page = CatalogPage(page)
    basket_page = BasketPage(page)

    catalog_page.login('standard_user', 'secret_sauce')
    catalog_page.add_to_cart('Sauce Labs Bike Light')

    basket_page.open_cart()
    basket_page.expect_item_in_cart('Sauce Labs Bike Light')


def test_add_two_items_in_cart(page):
    catalog_page = CatalogPage(page)
    basket_page = BasketPage(page)

    catalog_page.login('standard_user', 'secret_sauce')
    catalog_page.add_to_cart('Sauce Labs Fleece Jacket')
    catalog_page.add_to_cart('Sauce Labs Bolt T-Shirt')

    basket_page.open_cart()
    items = basket_page.get_items_names()
    assert 'Sauce Labs Fleece Jacket' in items, "Товара Sauce Labs Fleece Jacket нет в корзине"
    assert 'Sauce Labs Bolt T-Shirt' in items, "Товара Sauce Labs Bolt T-Shirt нет в корзине"


def test_remove_item_from_cart(page):
    catalog_page = CatalogPage(page)
    basket_page = BasketPage(page)

    catalog_page.login('standard_user', 'secret_sauce')
    catalog_page.add_to_cart('Sauce Labs Bike Light')

    basket_page.open_cart()
    assert 'Sauce Labs Bike Light' in basket_page.get_items_names()

    basket_page.remove_item('Sauce Labs Bike Light')
    assert 'Sauce Labs Bike Light' not in basket_page.get_items_names()


def test_remove_two_items_from_cart(page):
    catalog_page = CatalogPage(page)
    basket_page = BasketPage(page)

    catalog_page.login('standard_user', 'secret_sauce')
    catalog_page.add_to_cart('Sauce Labs Backpack')
    catalog_page.add_to_cart('Test.allTheThings() T-Shirt (Red)')

    basket_page.open_cart()

    items_list = basket_page.get_items_names()
    assert 'Sauce Labs Backpack' in items_list
    assert 'Test.allTheThings() T-Shirt (Red)' in items_list

    basket_page.remove_item('Sauce Labs Backpack')
    basket_page.remove_item('Test.allTheThings() T-Shirt (Red)')

    items_list = basket_page.get_items_names()
    assert 'Sauce Labs Backpack' not in items_list
    assert 'Test.allTheThings() T-Shirt (Red)' not in items_list


def test_e2e(page):
    catalog = CatalogPage(page)
    basket = BasketPage(page)
    checkout = CheckoutPage(page)

    catalog.login('standard_user', 'secret_sauce')
    catalog.add_to_cart('Sauce Labs Bike Light')
    catalog.add_to_cart('Sauce Labs Fleece Jacket')

    basket.open_cart()
    items_names = basket.get_items_names()
    basket_total = basket.get_items_total_price()

    assert 'Sauce Labs Bike Light' in items_names, 'товар с названием Sauce Labs Bike Light не найден'
    assert 'Sauce Labs Fleece Jacket' in items_names, 'товар с названием Sauce Labs Fleece Jacket не найден'

    basket.checkout()

    checkout.start_checkout(first_name='Test', last_name='Test', postal_code= '000')
    assert checkout.get_item_total_after_continue() == pytest.approx(basket_total, 0.01)

    checkout.finish_checkout()
    assert checkout.get_success_text() == 'Thank you for your order!'


def test_checkout_without_field(auth_page):
    catalog = CatalogPage(auth_page)
    basket = BasketPage(auth_page)
    checkout = CheckoutPage(auth_page)

    catalog.login('standard_user', 'secret_sauce')
    catalog.add_to_cart('Sauce Labs Bike Light')

    basket.open_cart()
    assert 'Sauce Labs Bike Light' in basket.get_items_names()

    basket.checkout()

    checkout.start_checkout(first_name='Test', last_name='Test',postal_code= '')
    assert checkout.get_error_text() == 'Error: Postal Code is required'

