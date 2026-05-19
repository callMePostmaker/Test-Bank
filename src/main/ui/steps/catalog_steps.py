import allure
from ui.pages.catalog_page import CatalogPage
from playwright.sync_api import Page, expect


class CatalogSteps:
    def __init__(self, page: Page):
        self.page = page
        self.catalog_page = CatalogPage(page)

    @allure.step('Логинимся пользователем {username}')
    def login(self, username: str, password: str):
        self.catalog_page.login(username, password)
        return self

    @allure.step('Добавление товара {product_name} в корзину')
    def add_to_cart(self, product_name: str):
        button = self.catalog_page.add_to_cart(product_name)
        expect(button).to_have_text('Remove')
        return self

    @allure.step('Удаление товара {product_name} из корзины')
    def remove_from_cart(self, product_name: str):
        button = self.catalog_page.remove_from_cart(product_name)
        expect(button).to_have_text('Add to cart')
        return self

    @allure.step('Сортируем товары {option}')
    def sort_items(self, option: str):
        self.catalog_page.sort_items(option)
        return self


    @allure.step('Получаем количество товаров в каталоге')
    def get_products_count(self) -> int:
        return self.catalog_page.get_products_count()

    @allure.step('Получаем список товаров в каталоге')
    def get_products_names(self) -> list[str]:
        return self.catalog_page.get_product_names()

    @allure.step('Получаем список цен на товары в каталоге')
    def get_products_prices(self) -> list[float]:
        return self.catalog_page.get_product_prices()

    @allure.step('Получаем список товаров в корзине')
    def get_products_in_cart_count(self) -> int:
        return self.catalog_page.get_cart_count()

    @allure.step('Открывает детальную страницу товара {product_name}')
    def open_product_details(self, product_name: str):
        return self.catalog_page.open_product_details(product_name)

    @allure.step('Выполняем логаут')
    def logout(self):
        self.catalog_page.logout()
        return self
