import random
import string

import urllib3

from util.conf import BAMBOO_SETTINGS
from util.api.bamboo_clients import BambooClient
from util.project_paths import BAMBOO_BUILD_PLANS, BAMBOO_USERS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BUILD_PLANS = 'plans'
USERS = 'users'
PROJECTS = 'projects'
DEFAULT_PASSWORD = 'password'
AGENTS_BUILD_PLANS_PERCENT = 10


def generate_random_string(length=20):
    return "".join([random.choice(string.ascii_lowercase) for _ in range(length)])


def get_users(client, users_count):
    existing_users = client.get_users(users_count)
    users_to_generate = 0
    users = []
    if len(existing_users) < users_count:
        users_to_generate = users_count - len(existing_users)
    users.extend(existing_users)
    if users_to_generate:
        for i in range(0, users_to_generate):
            username = f'performance_user_{generate_random_string(5)}'
            password = DEFAULT_PASSWORD
            generated_user = client.create_user(name=username, password=password)
            users.append(generated_user)
    return users


def generate_project_name_keys_dict(client):
    projects_name_key_dict = {}
    projects = client.get_projects()
    for project in projects:
        projects_name_key_dict[project['name']] = project['key']
    return projects_name_key_dict


def assert_number_of_agents(client):
    number_of_online_agents = len(client.get_online_agents())
    if number_of_online_agents < BAMBOO_SETTINGS.number_of_agents:
        raise Exception(f'There are {number_of_online_agents} of desired {BAMBOO_SETTINGS.number_of_agents}. '
                        f'Please, review the number of online agents.')
    print(f'There are {number_of_online_agents} online agents.')


def verify_agents_plans_setup():
    parallel_plans_count = BAMBOO_SETTINGS.parallel_plans_count
    number_of_agents = BAMBOO_SETTINGS.number_of_agents
    agents_plans_diff_in_perc = 100 * float(number_of_agents) / float(parallel_plans_count) - 100

    if agents_plans_diff_in_perc < AGENTS_BUILD_PLANS_PERCENT:
        raise Exception(f'The number of online agents should be more thant the number of parallel '
                        f'runs by {AGENTS_BUILD_PLANS_PERCENT}%. '
                        f'There {number_of_agents} agents and {parallel_plans_count} parallel plans to '
                        f'build are configured, which is {agents_plans_diff_in_perc}%. ')


def __create_dataset(client):
    dataset = dict()
    dataset[BUILD_PLANS] = client.get_build_plans(max_result=2000)
    dataset[PROJECTS] = generate_project_name_keys_dict(client)
    dataset[USERS] = get_users(client, BAMBOO_SETTINGS.concurrency)

    return dataset


def __write_to_file(file_path, items):
    with open(file_path, 'w') as f:
        for item in items:
            f.write(f"{item}\n")


def write_test_data_to_files(dataset):
    build_plans = [f"{dataset[PROJECTS][build_plan['searchEntity']['projectName']]},{build_plan['id']}" for
                   build_plan in dataset[BUILD_PLANS]]
    __write_to_file(BAMBOO_BUILD_PLANS, build_plans)
    users = [f"{user['name']},{DEFAULT_PASSWORD}" for user in dataset[USERS] if user['name'] != 'admin']
    __write_to_file(BAMBOO_USERS, users)


def main():
    print("Started preparing data")
    verify_agents_plans_setup()

    url = BAMBOO_SETTINGS.server_url
    print("Server url: ", url)

    client = BambooClient(url, BAMBOO_SETTINGS.admin_login, BAMBOO_SETTINGS.admin_password,
                          verify=BAMBOO_SETTINGS.secure)

    dataset = __create_dataset(client)
    write_test_data_to_files(dataset)
    assert_number_of_agents(client)

    print("Finished preparing data")


if __name__ == "__main__":
    main()