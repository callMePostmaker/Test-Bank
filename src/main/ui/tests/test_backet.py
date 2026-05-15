from openpyxl.worksheet import page
from playwright.sync_api import expect



def test_item_and_check_in_cart(page):
    page.goto('https://www.saucedemo.com')
    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')
    page.locator('#login-button').click()

    page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]').click()

    page.locator('.shopping_cart_link').click()

    item_name = page.locator('[data-test="inventory-item-name"]').inner_text()

    assert item_name == 'Sauce Labs Bike Light'


def test_add_two_items_in_cart(page):
    page.goto('https://www.saucedemo.com')
    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')
    page.locator('#login-button').click()

    page.locator('[data-test="add-to-cart-sauce-labs-fleece-jacket"]').click()
    page.locator('[data-test="add-to-cart-sauce-labs-bolt-t-shirt"]').click()

    page.locator('.shopping_cart_link').click()

    fleece_jacket = page.locator('.inventory_item_name', has_text= 'Sauce Labs Fleece Jacket').inner_text()
    bolt_t_shirt = page.locator('.inventory_item_name', has_text='Sauce Labs Bolt T-Shirt').inner_text()

    assert bolt_t_shirt == 'Sauce Labs Bolt T-Shirt', 'товар с таким названием(Sauce Labs Bolt T-Shirt) не найден'
    assert fleece_jacket == 'Sauce Labs Fleece Jacket', 'товар с таким названием(Sauce Labs Fleece Jacket) не найден'



