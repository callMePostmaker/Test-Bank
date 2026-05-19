import pytest

from ui.steps.catalog_steps import CatalogSteps
from ui.steps.basket_steps import BasketSteps
from ui.steps.checkout_steps import CheckoutSteps


def test_item_and_check_in_cart(page):
    catalog_steps = CatalogSteps(page)
    basket_steps = BasketSteps(page)

    catalog_steps.login('standard_user', 'secret_sauce')
    catalog_steps.add_to_cart('Sauce Labs Bike Light')

    basket_steps.open_cart()
    basket_steps.check_product_in_basket('Sauce Labs Bike Light')


def test_add_two_items_in_cart(page):
    catalog_steps = CatalogSteps(page)
    basket_steps = BasketSteps(page)

    catalog_steps.login('standard_user', 'secret_sauce')
    catalog_steps.add_to_cart('Sauce Labs Fleece Jacket')
    catalog_steps.add_to_cart('Sauce Labs Bolt T-Shirt')

    basket_steps.open_cart()
    items = basket_steps.get_items_names()
    assert 'Sauce Labs Fleece Jacket' in items, "Товара Sauce Labs Fleece Jacket нет в корзине"
    assert 'Sauce Labs Bolt T-Shirt' in items, "Товара Sauce Labs Bolt T-Shirt нет в корзине"


def test_remove_item_from_cart(page):
    catalog_steps = CatalogSteps(page)
    basket_steps = BasketSteps(page)

    catalog_steps.login('standard_user', 'secret_sauce')
    catalog_steps.add_to_cart('Sauce Labs Bike Light')

    basket_steps.open_cart()
    assert 'Sauce Labs Bike Light' in basket_steps.get_items_names()

    basket_steps.remove_item('Sauce Labs Bike Light')
    assert 'Sauce Labs Bike Light' not in basket_steps.get_items_names()


def test_remove_two_items_from_cart(page):
    catalog_steps = CatalogSteps(page)
    basket_steps = BasketSteps(page)

    catalog_steps.login('standard_user', 'secret_sauce')
    catalog_steps.add_to_cart('Sauce Labs Backpack')
    catalog_steps.add_to_cart('Test.allTheThings() T-Shirt (Red)')

    basket_steps.open_cart()

    items_list = basket_steps.get_items_names()
    assert 'Sauce Labs Backpack' in items_list
    assert 'Test.allTheThings() T-Shirt (Red)' in items_list

    basket_steps.remove_item('Sauce Labs Backpack')
    basket_steps.remove_item('Test.allTheThings() T-Shirt (Red)')

    items_list = basket_steps.get_items_names()
    assert 'Sauce Labs Backpack' not in items_list
    assert 'Test.allTheThings() T-Shirt (Red)' not in items_list


def test_e2e(page):
    catalog_steps = CatalogSteps(page)
    basket_steps = BasketSteps(page)
    checkout_steps = CheckoutSteps(page)

    catalog_steps.login('standard_user', 'secret_sauce')
    catalog_steps.add_to_cart('Sauce Labs Bike Light')
    catalog_steps.add_to_cart('Sauce Labs Fleece Jacket')

    basket_steps.open_cart()
    items_names = basket_steps.get_items_names()
    basket_total = basket_steps.get_items_prices()

    assert 'Sauce Labs Bike Light' in items_names, 'товар с названием Sauce Labs Bike Light не найден'
    assert 'Sauce Labs Fleece Jacket' in items_names, 'товар с названием Sauce Labs Fleece Jacket не найден'

    basket_steps.open_checkout()

    checkout_steps.start_checkout(first_name='Test', last_name='Test', postal_code= '000')
    assert checkout_steps.get_item_total_after_continue() == pytest.approx(basket_total, 0.01)

    checkout_steps.finish_checkout()
    assert checkout_steps.get_success_message() == 'Thank you for your order!'


def test_checkout_without_field(page):
    catalog_steps = CatalogSteps(page)
    basket_steps = BasketSteps(page)
    checkout_steps = CheckoutSteps(page)

    catalog_steps.login('standard_user', 'secret_sauce')
    catalog_steps.add_to_cart('Sauce Labs Bike Light')

    basket_steps.open_cart()
    assert 'Sauce Labs Bike Light' in basket_steps.get_items_names()

    basket_steps.open_checkout()

    checkout_steps.start_checkout(first_name='Test', last_name='Test',postal_code= '')
    assert checkout_steps.get_error_message() == 'Error: Postal Code is required'

