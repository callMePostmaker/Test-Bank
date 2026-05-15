from playwright.sync_api import expect



def test_item_and_check_in_cart(auth_page):
    auth_page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]').click()

    auth_page.locator('.shopping_cart_link').click()

    item_name = auth_page.locator('[data-test="inventory-item-name"]').inner_text()

    assert item_name == 'Sauce Labs Bike Light'


def test_add_two_items_in_cart(auth_page):
    auth_page.locator('[data-test="add-to-cart-sauce-labs-fleece-jacket"]').click()
    auth_page.locator('[data-test="add-to-cart-sauce-labs-bolt-t-shirt"]').click()

    auth_page.locator('.shopping_cart_link').click()

    fleece_jacket = auth_page.locator('.inventory_item_name', has_text= 'Sauce Labs Fleece Jacket').inner_text()
    bolt_t_shirt = auth_page.locator('.inventory_item_name', has_text='Sauce Labs Bolt T-Shirt').inner_text()

    assert bolt_t_shirt == 'Sauce Labs Bolt T-Shirt', 'товар с таким названием(Sauce Labs Bolt T-Shirt) не найден'
    assert fleece_jacket == 'Sauce Labs Fleece Jacket', 'товар с таким названием(Sauce Labs Fleece Jacket) не найден'


def test_remove_item_from_cart(auth_page):
    auth_page.locator('[data-test="add-to-cart-sauce-labs-fleece-jacket"]').click()

    auth_page.locator('.shopping_cart_link').click()

    jacket = auth_page.locator('.inventory_item_name', has_text= 'Sauce Labs Fleece Jacket')
    expect(jacket).to_be_visible()

    auth_page.locator('[data-test="remove-sauce-labs-fleece-jacket"]').click()

    expect(jacket).not_to_be_visible()


def test_remove_two_items_from_cart(auth_page):
    auth_page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    auth_page.locator('[data-test="add-to-cart-test.allthethings()-t-shirt-(red)"]').click()

    auth_page.locator('.shopping_cart_link').click()

    backpack = auth_page.locator('.inventory_item_name', has_text= 'Sauce Labs Backpack')
    t_shirt = auth_page.locator('.inventory_item_name', has_text= 'Test.allTheThings() T-Shirt (Red)')

    expect(backpack).to_be_visible()
    expect(t_shirt).to_be_visible()

    auth_page.locator('[data-test="remove-sauce-labs-backpack"]').click()
    auth_page.locator('[data-test="remove-test.allthethings()-t-shirt-(red)"]').click()


    expect(backpack).not_to_be_visible()
    expect(t_shirt).not_to_be_visible()


def test_e2e(auth_page):
    auth_page.locator('[data-test="add-to-cart-sauce-labs-fleece-jacket"]').click()
    auth_page.locator('[data-test="add-to-cart-test.allthethings()-t-shirt-(red)"]').click()

    auth_page.locator('.shopping_cart_link').click()

    fleece_jacket = auth_page.locator('.inventory_item_name', has_text='Sauce Labs Fleece Jacket')
    bolt_t_shirt = auth_page.locator('.inventory_item_name', has_text='Test.allTheThings() T-Shirt (Red)')

    expect(fleece_jacket).to_be_visible()
    expect(bolt_t_shirt).to_be_visible()
    assert bolt_t_shirt == 'Sauce Labs Bolt T-Shirt', 'товар с таким названием(Sauce Labs Bolt T-Shirt) не найден'
    assert fleece_jacket == 'Sauce Labs Fleece Jacket', 'товар с таким названием(Sauce Labs Fleece Jacket) не найден'

    prices_text = auth_page.locator('.inventory_item_price').all_text_contents()
    price = [float(p.replace('$', '')) for p in prices_text]
    expected_total = sum(price)

    auth_page.locator('[data-test="checkout"]').click()

    expect(auth_page).to_have_url('https://www.saucedemo.com/checkout-step-one.html')

    auth_page.locator('[data-test="firstName"]').fill('tester')
    auth_page.locator('[data-test="lastName"]').fill('auto')
    auth_page.locator('[data-test="postalCode"]').fill('000')
    auth_page.locator('[data-test="continue"]').click()

    item_total_text = auth_page.locator('[data-test="subtotal-label"]').inner_text()
    item_subtotal_value = float(item_total_text.split('$')[1])
    assert item_subtotal_value == expected_total, f'{item_subtotal_value}, не совпадает с ожидаемой ценой -> {expected_total}'

    tax_text = auth_page.locator('.summary_tax_label').inner_text()
    tax = float(tax_text.split('$')[1])

    total_text = auth_page.locator('.summary_total_label').inner_text()
    total_value = float(total_text.split('$')[1])

    assert total_value == round(item_subtotal_value + tax, 2), 'total не совпадает с tax + item_total'

    auth_page.locator('[data-test="finish"]').click()

    expect(auth_page).to_have_url('https://www.saucedemo.com/checkout-complete.html')

    success_text = auth_page.locator('[data-test="complete-text"]').inner_text()

    assert 'Your order has been dispatched' in success_text

    back_home_button = auth_page.locator('[data-test="back-to-products"]')

    expect(back_home_button).to_be_visible()


def test_checkout_without_field(auth_page):
    auth_page.locator('[data-test="add-to-cart-sauce-labs-fleece-jacket"]').click()

    auth_page.locator('.shopping_cart_link').click()

    auth_page.locator('[data-test="checkout"]').click()

    auth_page.locator('[data-test="firstName"]').fill('tester')
    auth_page.locator('[data-test="lastName"]').fill('auto')

    auth_page.locator('[data-test="continue"]').click()

    error_message = auth_page.locator('[data-test="error"]')
    expect(error_message).to_have_text('Error: Postal Code is required')
