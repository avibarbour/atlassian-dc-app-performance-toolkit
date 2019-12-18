from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from selenium_ui.conftest import print_timing
from selenium_ui.jira.modules import _wait_until
from util.conf import JIRA_SETTINGS

APPLICATION_URL = JIRA_SETTINGS.server_url
timeout = 20


def custom_action(webdriver, datasets):
    @print_timing
    def measure(webdriver, interaction):
        @print_timing
        def measure(webdriver, interaction):
            webdriver.get(f'{APPLICATION_URL}/plugins/servlet/some-app/reporter')
            _wait_until(webdriver, ec.visibility_of_element_located((By.ID, "plugin-element")), interaction)

        measure(webdriver, 'selenium_app_custom_action:view_report')

        @print_timing
        def measure(webdriver, interaction):
            webdriver.get(f'{APPLICATION_URL}/plugins/servlet/some-app/administration')
            _wait_until(webdriver, ec.visibility_of_element_located((By.ID, "plugin-dashboard")), interaction)

        measure(webdriver, 'selenium_app_custom_action:view_dashboard')

    measure(webdriver, 'selenium_app_custom_action')
