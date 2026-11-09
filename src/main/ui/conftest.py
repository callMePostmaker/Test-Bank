import allure
import pytest
from src.main.ui.fixtures.fixtures import *



def pytest_collection_modifyitems(items):
    for item in items:
        if "ui" in item.path.parts:
            item.add_marker(pytest.mark.ui)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f'report_{report.when}', report)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    yield
    report = getattr(request.node, 'report_call', None)
    if report and report.failed:
        allure.attach(
            page.screenshot(full_page=True),
            attachment_type=allure.attachment_type.PNG,
            name="screenshot_on_failure"
        )
