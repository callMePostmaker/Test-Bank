import allure
from ui.pages.checkout_page import CheckoutPage
from playwright.sync_api import Page, expect


class CheckoutSteps:
    def __init__(self, page: Page):
        self.page = page
        self.checkout = CheckoutPage(page)

    @allure.step('Выполняем checkout: {first_name} {last_name} {postal_code}')
    def start_checkout(self, first_name: str, last_name: str, postal_code: str):
        self.checkout.start_checkout(first_name, last_name, postal_code)
        return self

    @allure.step('Завершаем первый шаг чекаута')
    def finish_checkout(self):
        self.checkout.finish_checkout()
        return self

    @allure.step('Получаем текст ошибки при чекауте')
    def get_error_message(self) -> str:
        return self.checkout.get_error_text()

    @allure.step('Получаем текст при успешном чекауте')
    def get_success_message(self) -> str:
        return self.checkout.get_success_text()

    @allure.step('Получаем сумму цен товаров после continue')
    def get_item_total_after_continue(self) -> float:
        return self.checkout.get_item_total_after_continue()
