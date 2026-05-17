from playwright.sync_api import expect
from src.main.ui.pages.catalog_page import CatalogPage

def test_count_catalog(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user','secret_sauce')
    assert catalog.get_products_count() == 6


def test_sort_catalog_az(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    catalog.sort_items('az')
    names = sorted(catalog.get_product_names())
    assert names == catalog.get_product_names(), 'Товары не были отсортированы по "az" фильтру'


def test_sort_catalog_za(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    catalog.sort_items('za')
    names = sorted(catalog.get_product_names(), reverse=True)
    assert names == catalog.get_product_names(), 'Товары не были отсортированы по "za" фильтру'


def test_sort_catalog_by_price(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    #сорт от меньшего к большему
    catalog.sort_items('lohi')
    sorted_prices = sorted(catalog.get_product_prices())
    assert sorted_prices == catalog.get_product_prices(), 'товары не были отсортированы по убыванию цены'
    # сорт от большего к меньшему
    catalog.sort_items('hilo')
    reverse_sorted_prices = sorted(catalog.get_product_prices(), reverse=True)
    assert reverse_sorted_prices == catalog.get_product_prices(), 'товары не были отсортированы по возрастанию цены'


def test_add_to_cart(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')

    expect(catalog.add_to_cart('Sauce Labs Bike Light')).to_have_text('Remove')
    assert catalog.get_cart_count() == 1


def test_add_sauce_labs_onesie_to_cart(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    # Добавляем товар Sauce Labs Onesie в корзину
    expect(catalog.add_to_cart('Sauce Labs Onesie')).to_have_text('Remove')
    assert catalog.get_cart_count() == 1
    # Удаляем товар Sauce Labs Onesie из корзины
    expect(catalog.remove_from_cart('Sauce Labs Onesie')).to_have_text('Add to cart')
    assert catalog.get_cart_count() == 0


def test_product_details_onesie(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    name, price, detail_name, detail_price = catalog.open_product_details('Sauce Labs Onesie')

    assert name == detail_name, 'Названия товара не совпадают'
    assert price == detail_price, "Цены товара не совпадают"


def test_product_details_jacket(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    name, price, detail_name, detail_price = catalog.open_product_details('Sauce Labs Fleece Jacket')

    assert name == detail_name, 'Названия товара не совпадают'
    assert price == detail_price, "Цены товара не совпадают"


def test_remove_item_from_catalog(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    # Добавляем товар в корзину
    expect(catalog.add_to_cart('Test.allTheThings() T-Shirt (Red)')).to_have_text('Remove')
    assert catalog.get_cart_count() == 1
    # Удаляем товар из корзины
    expect(catalog.remove_from_cart('Test.allTheThings() T-Shirt (Red)')).to_have_text('Add to cart')
    assert catalog.get_cart_count() == 0



def test_remove_sauce_lab_onesie(page):
    catalog = CatalogPage(page)
    catalog.login('standard_user', 'secret_sauce')
    # Добавляем товар Sauce Labs Onesie в корзину
    expect(catalog.add_to_cart('Sauce Labs Onesie')).to_have_text('Remove')
    assert catalog.get_cart_count() == 1
    # Удаляем товар Sauce Labs Onesie из корзины
    expect(catalog.remove_from_cart('Test.allTheThings() T-Shirt (Red)')).to_have_text('Add to cart')
    assert catalog.get_cart_count() == 0


