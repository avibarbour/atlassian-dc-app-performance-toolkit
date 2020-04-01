from selenium.webdriver.common.keys import Keys

from selenium_ui.base_page import BasePage
from selenium_ui.bitbucket.pages.selectors import LoginPageLocators, GetStartedLocators, \
    DashboardLocators, ProjectsLocators, ProjectLocators, RepoLocators, RepoNavigationPanelLocators, PopupLocators, \
    PullRequestLocator, BranchesLocator, RepositorySettingsLocator, UserSettingsLocator, RepoCommitsLocator, \
    LogoutPageLocators, UrlManager


class LoginPage(BasePage):
    page_url = UrlManager().login_url()

    def fill_username(self, username):
        self.get_element(LoginPageLocators.username_textfield).send_keys(username)

    def fill_password(self, password):
        self.get_element(LoginPageLocators.password_textfield).send_keys(password)

    def submit_login(self, interaction=None):
        self.wait_until_visible(LoginPageLocators.submit_button, interaction).click()

    def set_credentials(self, username, password):
        self.fill_username(username)
        self.fill_password(password)

    def get_app_version(self):
        el = self.get_element(LoginPageLocators.application_version)
        return ''.join([i for i in el.text.split('.')[0] if i.isdigit()])


class LogoutPage(BasePage):

    page_url = LogoutPageLocators.logout_url


class GetStarted(BasePage):
    page_url = GetStartedLocators.get_started_url
    page_loaded_selector = GetStartedLocators.bitbucket_is_ready_widget


class Dashboard(BasePage):
    page_url = DashboardLocators.dashboard_url
    page_loaded_selector = DashboardLocators.dashboard_presence


class Projects(BasePage):
    page_url = ProjectsLocators.project_url
    page_loaded_selector = ProjectsLocators.projects_list


class Project(BasePage):
    page_loaded_selector = [ProjectLocators.repositories_container, ProjectLocators.repository_name]

    def __init__(self, driver, project_key):
        BasePage.__init__(self, driver)
        self.project_key = project_key
        url_manager = UrlManager(project_key=project_key)
        self.page_url = url_manager.project_url()


class RepoNavigationPanel(BasePage):
    page_loaded_selector = RepoNavigationPanelLocators.navigation_panel

    def __clone_repo_button(self):
        return self.get_element(RepoNavigationPanelLocators.clone_repo_button)

    def wait_for_navigation_panel(self, interaction):
        return self.wait_until_present(RepoNavigationPanelLocators.navigation_panel, interaction)

    def clone_repo_click(self):
        self.__clone_repo_button().click()

    def fork_repo(self, interaction):
        return self.wait_until_visible(RepoNavigationPanelLocators.fork_repo_button, interaction)

    def create_pull_request(self, interaction):
        self.wait_until_visible(RepoNavigationPanelLocators.create_pull_request_button, interaction).click()
        self.wait_until_visible(RepoLocators.pull_requests_list, interaction)


class PopupManager(BasePage):

    def dismiss_default_popup(self):
        return self.dismiss_popup(PopupLocators.default_popup, PopupLocators.popup_1, PopupLocators.popup_2)


class Repository(BasePage):

    def __init__(self, driver, project_key, repo_slug):
        BasePage.__init__(self, driver)
        url_manager = UrlManager(project_key=project_key, repo_slug=repo_slug)
        self.page_url = url_manager.repo_url()
        self.repo_slug = repo_slug
        self.project_key = project_key

    def set_enable_fork_sync(self, interaction, value):
        checkbox = self.wait_until_visible(RepoLocators.repo_fork_sync, interaction)
        current_state = checkbox.is_selected()
        if (value and not current_state) or (not value and current_state):
            checkbox.click()

    def submit_fork_repo(self):
        self.wait_until_visible(RepoLocators.fork_repo_submit_button).click()

    def set_fork_repo_name(self):
        fork_name_field = self.get_element(RepoLocators.fork_name_field)
        fork_name_field.clear()
        fork_name = f"{self.repo_slug}-{self.generate_random_string(5)}"
        fork_name_field.send_keys(fork_name)
        return fork_name


class RepoPullRequests(BasePage):
    page_loaded_selector = RepoLocators.pull_requests_list

    def __init__(self, driver, project_key, repo_slug):
        BasePage.__init__(self, driver)
        self.url_manager = UrlManager(project_key=project_key, repo_slug=repo_slug)
        self.page_url = self.url_manager.repo_pull_requests()

    def create_new_pull_request(self, from_branch, to_branch, interaction):
        self.go_to_url(url=self.url_manager.create_pull_request_url(from_branch=from_branch,
                                                                    to_branch=to_branch))
        self.submit_pull_request(interaction)

    def set_pull_request_source_branch(self, interaction, source_branch):
        self.wait_until_visible(RepoLocators.pr_source_branch_field, interaction).click()
        self.wait_until_visible(RepoLocators.pr_branches_dropdown, interaction)
        source_branch_name_field = self.get_element(RepoLocators.pr_source_branch_name)
        source_branch_name_field.send_keys(source_branch)
        self.wait_until_invisible(RepoLocators.pr_source_branch_spinner, interaction)
        source_branch_name_field.send_keys(Keys.ENTER)
        self.wait_until_invisible(RepoLocators.pr_branches_dropdown, interaction)

    def set_pull_request_destination_repo(self, interaction):
        self.wait_until_visible(RepoLocators.pr_destination_repo_field, interaction).click()
        self.wait_until_visible(RepoLocators.pr_destination_first_repo_dropdown, interaction).click()

    def set_pull_request_destination_branch(self, interaction, destination_branch):
        self.wait_until_visible(RepoLocators.pr_destination_branch_field, interaction)
        self.execute_js("document.querySelector('#targetBranch').click()")
        self.wait_until_visible(RepoLocators.pr_destination_branch_dropdown, interaction)
        destination_branch_name_field = self.get_element(RepoLocators.pr_destination_branch_name)
        destination_branch_name_field.send_keys(destination_branch)
        self.wait_until_invisible(RepoLocators.pr_destination_branch_spinner, interaction)
        destination_branch_name_field.send_keys(Keys.ENTER)
        self.wait_until_invisible(RepoLocators.pr_branches_dropdown, interaction)
        self.wait_until_clickable(RepoLocators.pr_continue_button, interaction)
        self.wait_until_visible(RepoLocators.pr_continue_button, interaction).click()

    def submit_pull_request(self, interaction):
        self.wait_until_visible(RepoLocators.pr_description_field, interaction)
        title = self.get_element(RepoLocators.pr_title_field)
        title.clear()
        title.send_keys('Selenium test pull request')
        self.wait_until_visible(RepoLocators.pr_submit_button, interaction).click()
        self.wait_until_visible(PullRequestLocator.pull_request_activity_content, interaction)
        self.wait_until_clickable(PullRequestLocator.pull_request_page_merge_button, interaction)


class PullRequest(BasePage):

    def __init__(self, driver, project_key=None, repo_slug=None, pull_request_key=None):
        BasePage.__init__(self, driver)
        url_manager = UrlManager(project_key=project_key, repo_slug=repo_slug,
                                 pull_request_key=pull_request_key)
        self.page_url = url_manager.pull_request_overview()
        self.diff_url = url_manager.pull_request_diff()
        self.commits_url = url_manager.pull_request_commits()

    def wait_for_overview_tab(self, interaction):
        return self.wait_until_visible(PullRequestLocator.pull_request_activity_content, interaction)

    def go_to_overview(self):
        return self.go_to()

    def go_to_diff(self):
        self.go_to_url(url=self.diff_url)

    def go_to_commits(self):
        self.go_to_url(self.commits_url)

    def wait_for_diff_tab(self, interaction):
        return self.wait_until_any_element_visible(PullRequestLocator.commit_files, interaction)

    def wait_for_code_diff(self, interaction):
        return self.wait_until_visible(PullRequestLocator.diff_code_lines, interaction)

    def wait_for_commits_tab(self, interaction):
        self.wait_until_any_element_visible(PullRequestLocator.commit_message_label, interaction)

    def click_inline_comment_button_js(self):
        selector = self.get_selector(PullRequestLocator.inline_comment_button)
        self.execute_js(f"elems=document.querySelectorAll('{selector[1]}'); "
                        "item=elems[Math.floor(Math.random() * elems.length)];"
                        "item.scrollIntoView();"
                        "item.click();")

    def wait_for_comment_text_area(self, interaction):
        return self.wait_until_visible(PullRequestLocator.comment_text_area, interaction)

    def add_code_comment_v6(self, interaction):
        self.wait_for_comment_text_area(interaction)
        selector = self.get_selector(PullRequestLocator.comment_text_area)
        self.execute_js(f"document.querySelector('{selector[1]}').value = 'Comment from Selenium script';")
        self.click_save_comment_button(interaction)

    def add_code_comment_v7(self, interaction):
        self.wait_until_visible(PullRequestLocator.text_area, interaction).send_keys('Comment from Selenium script')
        self.click_save_comment_button(interaction)

    def add_code_comment(self, interaction):
        if self.app_version == '6':
            self.add_code_comment_v6(interaction)
        elif self.app_version == '7':
            self.add_code_comment_v7(interaction)

    def click_save_comment_button(self, interaction):
        return self.wait_until_visible(PullRequestLocator.comment_button, interaction).click()

    def add_overview_comment(self, interaction):
        self.wait_for_comment_text_area(interaction).click()
        self.wait_until_clickable(PullRequestLocator.text_area, interaction).send_keys(self.generate_random_string(50))

    def wait_merge_button_clickable(self, interaction):
        self.wait_until_clickable(PullRequestLocator.pull_request_page_merge_button, interaction)

    def merge_pull_request(self, interaction):
        if self.driver.app_version == '6':
            if self.get_elements(PullRequestLocator.merge_spinner):
                self.wait_until_invisible(PullRequestLocator.merge_spinner, interaction)
        self.wait_until_present(PullRequestLocator.pull_request_page_merge_button).click()
        PopupManager(self.driver).dismiss_default_popup()
        self.wait_until_visible(PullRequestLocator.diagram_selector)
        self.get_element(PullRequestLocator.delete_branch_per_merge_checkbox).click()
        self.wait_until_clickable(PullRequestLocator.pull_request_modal_merge_button, interaction).click()
        self.wait_until_invisible(PullRequestLocator.del_branch_checkbox_selector, interaction)


class RepositoryBranches(BasePage):
    page_loaded_selector = BranchesLocator.branches_name

    def __init__(self, driver, project_key, repo_slug):
        BasePage.__init__(self, driver)
        self.url_manager = UrlManager(project_key=project_key, repo_slug=repo_slug)
        self.page_url = self.url_manager.repo_branches()

    def open_base_branch(self, base_branch_name, interaction):
        self.go_to_url(f"{self.url_manager.base_branch_url()}{base_branch_name}")
        self.wait_until_visible(BranchesLocator.branches_name, interaction)

    def create_branch_fork_rnd_name(self, base_branch_name, interaction):
        self.wait_until_visible(BranchesLocator.branches_action, interaction).click()
        self.get_element(BranchesLocator.branches_action_create_branch).click()
        self.wait_until_visible(BranchesLocator.new_branch_name_textfield, interaction)
        branch_name = f"{base_branch_name}-{self.generate_random_string(5)}".replace(' ', '-')
        self.get_element(BranchesLocator.new_branch_name_textfield).send_keys(branch_name)
        self.wait_until_clickable(BranchesLocator.new_branch_submit_button, interaction).click()
        return branch_name

    def delete_branch(self, interaction, branch_name):
        self.wait_until_visible(BranchesLocator.search_branch_textfield, interaction).send_keys(branch_name)
        self.wait_until_visible(BranchesLocator.branches_name, interaction)
        self.wait_until_visible(BranchesLocator.search_branch_action, interaction).click()
        self.execute_js("document.querySelector('li>a.delete-branch').click()")
        self.wait_until_clickable(BranchesLocator.delete_branch_diaglog_submit, interaction).click()


class RepositorySettings(BasePage):

    def wait_repository_settings(self, interaction):
        self.wait_until_visible(RepositorySettingsLocator.repository_settings_menu, interaction)

    def delete_repository(self, interaction, repo_slug):
        self.wait_repository_settings(interaction)
        self.wait_until_visible(RepositorySettingsLocator.delete_repository_button, interaction).click()
        self.wait_until_visible(RepositorySettingsLocator.delete_repository_modal_text_field,
                                interaction).send_keys(repo_slug)
        self.wait_until_clickable(RepositorySettingsLocator.delete_repository_modal_submit_button, interaction)
        self.wait_until_visible(RepositorySettingsLocator.delete_repository_modal_submit_button, interaction).click()


class ForkRepositorySettings(RepositorySettings):
    def __init__(self, driver, user, repo_slug):
        BasePage.__init__(self, driver)
        url_manager = UrlManager(user=user, repo_slug=repo_slug)
        self.page_url = url_manager.fork_repo_url()


class UserSettings(BasePage):

    def __init__(self, driver, user):
        BasePage.__init__(self, driver)
        url_manager = UrlManager(user=user)
        self.page_url = url_manager.user_settings_url()

    def user_role_visible(self, interaction):
        return self.wait_until_visible(UserSettingsLocator.user_role_label, interaction)


class RepositoryCommits(BasePage):
    page_loaded_selector = RepoCommitsLocator.repo_commits_graph

    def __init__(self, driver, project_key, repo_slug):
        BasePage.__init__(self, driver)
        url_manager = UrlManager(project_key=project_key, repo_slug=repo_slug)
        self.page_url = url_manager.commits_url()
