import allure
from ui.pages.basket_page import BasketPage
from playwright.sync_api import Page, expect


class BasketSteps:
    def __init__(self, page: Page):
        self.page = page
        self.basket = BasketPage(page)

    @allure.step('Открывем корзину')
    def open_cart(self):
        self.basket.open_cart()
        return self

    @allure.step('Проверяем что товар {product_name} добавлен в коризину')
    def check_product_in_basket(self, product_name: str):
        self.basket.expect_item_in_cart(product_name)
        return self

    @allure.step('Проверяем что товар {product_name} не в коризине')
    def check_product_not_in_basket(self, product_name: str):
        self.basket.expect_item_not_in_cart(product_name)
        return self

    @allure.step('Удаляем товар из корзины')
    def remove_item(self, product_name: str):
        self.basket.remove_item(product_name)
        return self

    @allure.step('переходим в чекаут')
    def open_checkout(self):
        self.basket.checkout()
        return self

    @allure.step('Получаем список товаров добавленных в корзину')
    def get_items_names(self) -> list[str]:
        return self.basket.get_items_names()

    @allure.step('Получаем сумму цен товаров в корзине')
    def get_items_prices(self) -> float:
        return self.basket.get_items_total_price()




