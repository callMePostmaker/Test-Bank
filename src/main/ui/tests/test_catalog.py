from playwright.sync_api import expect
from ui.pages.catalog_page import CatalogPage
from ui.steps.catalog_steps import CatalogSteps


def test_count_catalog(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')
    assert steps.get_products_count() > 0


def test_sort_catalog_by_name(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')

    assert (steps.sort_items('az').get_products_names() ==
    sorted(steps.sort_items('az').get_products_names()))\
    , 'Товары не были отсортированы по "az" фильтру'

    assert (steps.sort_items('za').get_products_names() ==
    sorted(steps.sort_items('za').get_products_names(), reverse=True))\
    , 'Товары не были отсортированы по "za" фильтру'


def test_sort_catalog_by_price(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')
    #сорт от меньшего к большему
    assert (steps.sort_items('lohi').get_products_prices() ==
    sorted(steps.sort_items('lohi').get_products_prices())) \
    , 'Товары не были отсортированы по "lohi" фильтру'
    # сорт от большего к меньшему
    assert (steps.sort_items('hilo').get_products_prices() ==
    sorted(steps.sort_items('hilo').get_products_prices(), reverse=True)) \
    , 'Товары не были отсортированы по "hilo" фильтру'


def test_add_to_cart(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')

    steps.add_to_cart('Sauce Labs Onesie')
    assert steps.get_products_in_cart_count() == 1


def test_add_sauce_labs_onesie_to_cart(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')
    # Добавляем товар Sauce Labs Onesie в корзину
    steps.add_to_cart('Sauce Labs Onesie')
    assert steps.get_products_in_cart_count() == 1
    # Удаляем товар Sauce Labs Onesie из корзины
    steps.remove_from_cart('Sauce Labs Onesie')
    assert steps.get_products_in_cart_count() == 0


def test_product_details_onesie(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')
    name, price, detail_name, detail_price = steps.open_product_details('Sauce Labs Onesie')

    assert name == detail_name, 'Названия товара не совпадают'
    assert price == detail_price, "Цены товара не совпадают"


def test_product_details_jacket(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')
    name, price, detail_name, detail_price = steps.open_product_details('Sauce Labs Fleece Jacket')

    assert name == detail_name, 'Названия товара не совпадают'
    assert price == detail_price, "Цены товара не совпадают"


def test_remove_item_from_catalog(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')
    # Добавляем товар в корзину
    steps.add_to_cart('Test.allTheThings() T-Shirt (Red)')
    assert steps.get_products_in_cart_count() == 1
    # Удаляем товар из корзины
    steps.remove_from_cart('Test.allTheThings() T-Shirt (Red)')
    assert steps.get_products_in_cart_count() == 0



def test_remove_sauce_lab_onesie(page):
    steps = CatalogSteps(page)
    steps.login('standard_user', 'secret_sauce')
    # Добавляем товар в корзину
    steps.add_to_cart('Sauce Labs Onesie')
    assert steps.get_products_in_cart_count() == 1
    # Удаляем товар из корзины
    steps.remove_from_cart('Sauce Labs Onesie')
    assert steps.get_products_in_cart_count() == 0


