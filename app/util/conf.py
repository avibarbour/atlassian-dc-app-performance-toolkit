import yaml
from util.project_paths import JIRA_YML, CONFLUENCE_YML


def read_yml_file(file):
    with file.open(mode='r') as file:
        return yaml.load(file, Loader=yaml.FullLoader)


class JiraSettings:

    def __init__(self):
        obj = read_yml_file(JIRA_YML)
        self.hostname = obj['settings']['env']['application_hostname']
        self.protocol = obj['settings']['env']['application_protocol']
        self.port = obj['settings']['env']['application_port']
        self.postfix = obj['settings']['env']['application_postfix'] or ""
        self.admin_login = obj['settings']['env']['admin_login']
        self.admin_password = obj['settings']['env']['admin_password']
        self.concurrency = obj['settings']['env']['concurrency']

    def __repr__(self):
        return f'hostname = {self.hostname!r}\n' \
               f'protocol = {self.protocol!r}\n' \
               f'port = {self.port!r}\n' \
               f'postfix = {self.postfix!r}\n' \
               f'admin_login = {self.admin_login!r}\n' \
               f'admin_password = {self.admin_password!r}\n' \
               f'concurrency = {self.concurrency!r}\n'

    @property
    def server_url(self):
        return f'{self.protocol}://{self.hostname}:{self.port}{self.postfix}'


class ConfluenceSettings(JiraSettings):

    def __init__(self):
        super().__init__()
        obj = read_yml_file(CONFLUENCE_YML)
        self.hostname = obj['settings']['env']['application_hostname']
        self.protocol = obj['settings']['env']['application_protocol']
        self.port = obj['settings']['env']['application_port']
        self.postfix = obj['settings']['env']['application_postfix'] or ""
        self.admin_login = obj['settings']['env']['admin_login']
        self.admin_password = obj['settings']['env']['admin_password']
        self.concurrency = obj['settings']['env']['concurrency']


JIRA_SETTINGS = JiraSettings()
CONFLUENCE_SETTINGS = ConfluenceSettings()
