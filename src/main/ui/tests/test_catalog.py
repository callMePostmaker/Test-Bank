from asyncio import timeout
from itertools import product

from playwright.sync_api import expect

def test_count_catalog(page):
    page.goto('https://www.saucedemo.com')

    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')

    page.locator('#login-button').click()

    products = page.locator('.inventory_item')

    assert products.count() == 6


def test_sort_catalog_az(page):
    page.goto('https://www.saucedemo.com')

    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')

    page.locator('#login-button').click()

    sort_selector = page.locator('.product_sort_container')
    expect(sort_selector).to_be_visible(timeout=5000)

    sort_selector.select_option('az')

    names = page.locator('.inventory_item').all_text_contents()

    assert names == sorted(names), 'Товары не были отсортированы по "az" фильтру'


def test_sort_catalog_za(page):
    page.goto('https://www.saucedemo.com')

    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')

    page.locator('#login-button').click()

    sort_selector = page.locator('.product_sort_container')
    expect(sort_selector).to_be_visible(timeout=5000)

    sort_selector.select_option('za')

    names = page.locator('.inventory_item').all_text_contents()

    assert names == sorted(names, reverse=True), 'Товары не были отсортированы по "za" фильтру'


def test_sort_catalog_by_price(page):
    page.goto('https://www.saucedemo.com')

    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')

    page.locator('#login-button').click()

    sort_selector = page.locator('.product_sort_container')
    expect(sort_selector).to_be_visible(timeout=5000)

    sort_selector.select_option('lohi')

    prices_text = page.locator('.inventory_item_price').all_text_contents()

    prices = [float(p.replace('$', "")) for p in prices_text]

    assert prices ==sorted(prices), 'товары не были отсортированы по убыванию цены'

    sort_selector.select_option('hilo')

    prices_text = page.locator('.inventory_item_price').all_text_contents()

    prices = [float(p.replace('$', "")) for p in prices_text]

    assert prices == sorted(prices, reverse=True), 'товары не были отсортированы по возрастанию цены'


def test_add_to_cart(page):
    page.goto('https://www.saucedemo.com')

    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')

    page.locator('#login-button').click()

    product_card = page.locator('.inventory_item', has_text='Sauce Labs Bike Light')
    add_button = product_card.locator('button')

    add_button.click()

    expect(add_button).to_have_text('Remove')

    expect(page.locator('.shopping_cart_badge')).to_have_text('1')


def test_add_sause_labs_onesie_to_cart(page):
    page.goto('https://www.saucedemo.com')

    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')

    page.locator('#login-button').click()

    product_card = page.locator('.inventory_item', has_text='Sauce Labs Onesie')
    add_button = product_card.locator('button')

    add_button.click()

    expect(add_button).to_have_text('Remove')
    cart_bage = page.locator('.shopping_cart_badge')
    expect(cart_bage).to_have_text('1')

    add_button.click()

    expect(add_button).to_have_text('Add to cart')
    expect(cart_bage).not_to_be_visible()


def test_product_details_onesie(page):
    page.goto('https://www.saucedemo.com')
    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')
    page.locator('#login-button').click()

    product_card = page.locator('.inventory_item', has_text='Sauce Labs Onesie')

    product_name = product_card.locator('[data-test="inventory-item-name"]').inner_text()
    product_price = product_card.locator('[data-test="inventory-item-price"]').inner_text()

    product_card.locator('[data-test="inventory-item-name"]').click()

    detail_name = page.locator('[data-test="inventory-item-name"]').inner_text()
    detail_price = page.locator('[data-test="inventory-item-price"]').inner_text()

    assert product_name == detail_name, 'Названия товара не совпадают'
    assert product_price == detail_price, "Цены товара не совпадают"


def test_product_details_jacket(page):
    page.goto('https://www.saucedemo.com')
    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')
    page.locator('#login-button').click()

    product_card = page.locator('.inventory_item', has_text='Sauce Labs Fleece Jacket')

    product_name = product_card.locator('[data-test="inventory-item-name"]').inner_text()
    product_price = product_card.locator('[data-test="inventory-item-price"]').inner_text()

    product_card.locator('[data-test="inventory-item-name"]').click()

    detail_name = page.locator('[data-test="inventory-item-name"]').inner_text()
    detail_price = page.locator('[data-test="inventory-item-price"]').inner_text()

    assert product_name == detail_name, 'Названия товара не совпадают'
    assert product_price == detail_price, "Цены товара не совпадают"


def test_remove_item_from_catalog(page):
    page.goto('https://www.saucedemo.com')
    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')
    page.locator('#login-button').click()

    product_card = page.locator('.inventory_item', has_text='Test.allTheThings() T-Shirt (Red)')
    product_button = product_card.locator('[data-test="add-to-cart-test.allthethings()-t-shirt-(red)"]')
    product_button.click()

    remove_button = product_card.locator('[data-test="remove-test.allthethings()-t-shirt-(red)"]')
    assert remove_button.is_visible(), "кнопка удаления товара из корзины не появилась"

    remove_button.click()
    assert product_button.is_visible(), 'Кнопка добавить в корзиру не появилась после удаления товара из корзины'


def test_remove_sauce_lab_onesie(page):
    page.goto('https://www.saucedemo.com')
    page.get_by_placeholder('Username').fill('standard_user')
    page.get_by_placeholder('Password').fill('secret_sauce')
    page.locator('#login-button').click()

    product_card = page.locator('.inventory_item', has_text='Sauce Labs Onesie')
    product_button = product_card.locator('[data-test="add-to-cart-sauce-labs-onesie"]')
    product_button.click()

    remove_button = product_card.locator('[data-test="remove-sauce-labs-onesie"]')
    assert remove_button.is_visible(), "кнопка удаления товара из корзины не появилась"

    remove_button.click()
    assert product_button.is_visible(), 'Кнопка добавить в корзиру не появилась после удаления товара из корзины'



