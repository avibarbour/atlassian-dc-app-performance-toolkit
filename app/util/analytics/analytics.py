import sys
import os
import re
import requests
from datetime import datetime, timezone
import platform
import uuid
import getpass
import socket
import hashlib

from util.analytics.application_info import ApplicationSelector
from util.analytics.log_reader import BztLogReader
from util.conf import TOOLKIT_VERSION


JIRA = 'jira'
CONFLUENCE = 'confluence'
BITBUCKET = 'bitbucket'

MIN_DEFAULTS = {JIRA: {'test_duration': 2700, 'concurrency': 200},
                CONFLUENCE: {'test_duration': 2700, 'concurrency': 200},
                BITBUCKET: {'test_duration': 3000, 'concurrency': 20, 'git_operations_per_hour': 14400}
                }

# List in value in case of specific output appears for some OS for command platform.system()
OS = {'macOS': ['Darwin'], 'Windows': ['Windows'], 'Linux': ['Linux']}
DT_REGEX = r'(\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2})'
SUCCESS_TEST_RATE_REGX = r'(\d{1,3}.\d{1,2}%)'
JMETER_TEST_REGX = r'jmeter_\S*'
SELENIUM_TEST_REGX = r'selenium_\S*'
BASE_URL = 'https://s7hdm2mnj1.execute-api.us-east-2.amazonaws.com/default/analytics_collector'
SUCCESS_TEST_RATE = 95.00
RESULTS_CSV = 'results.csv'
BZT_LOG = 'bzt.log'
LABEL_HEADER = 'Label'
LABEL_HEADER_INDEX = 0
SAMPLES_HEADER = '# Samples'
SAMPLES_HEADER_INDEX = 1
GIT_OPERATIONS = ['jmeter_clone_repo_via_http', 'jmeter_clone_repo_via_ssh',
                  'jmeter_git_push_via_http', 'jmeter_git_fetch_via_http',
                  'jmeter_git_push_via_ssh', 'jmeter_git_fetch_via_ssh']


class AnalyticsCollector:

    def __init__(self, application):
        self.application = application
        self.bzt_log = BztLogReader
        self.run_id = str(uuid.uuid1())
        self.tool_version = ""
        self.os = ""
        self.duration = 0
        self.concurrency = 0
        self.actual_duration = self.bzt_log.actual_run_time
        self.selenium_test_rates = self.bzt_log.selenium_test_rates
        self.jmeter_test_rates = self.bzt_log.jmeter_test_rates
        self.time_stamp = ""
        self.date = ""
        self.application_version = self.application.version
        self.summary = []
        self.nodes_count = self.application.nodes_count
        self.dataset_information = self.application.dataset_information

    @staticmethod
    def get_os():
        os_type = platform.system()
        for key, value in OS.items():
            os_type = key if os_type in value else os_type
        return os_type

    def is_analytics_enabled(self):
        return str(self.application.config.analytics_collector).lower() in ['yes', 'true', 'y']

    @staticmethod
    def __convert_to_sec(duration):
        seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        duration = str(duration)
        numbers = ''.join(filter(str.isdigit, duration))
        units = ''.join(filter(str.isalpha, duration))
        return int(numbers) * seconds_per_unit[units] if units in seconds_per_unit else int(numbers)

    def set_date_timestamp(self):
        utc_now = datetime.utcnow()
        self.time_stamp = int(round(utc_now.timestamp() * 1000))
        self.date = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat('T', 'seconds')

    @property
    def uniq_user_id(self):
        user_info = str(platform.node()) + str(getpass.getuser()) + str(socket.gethostname())
        uid = hashlib.pbkdf2_hmac('sha256', user_info.encode('utf-8'),
                                  b"DCAPT Centaurus",
                                  100000).hex()
        return uid

    def generate_analytics(self):
        self.concurrency = self.application.config.concurrency
        self.duration = self.__convert_to_sec(self.application.config.duration)
        self.os = self.get_os()
        self.tool_version = TOOLKIT_VERSION
        self.set_date_timestamp()

    @property
    def actual_git_operations_count(self):
        count = 0

        if self.application.type != BITBUCKET:
            raise Exception(f'ERROR: {self.application.type} is not {BITBUCKET}')
        results_csv_file_path = f'{self._log_dir}/results.csv'
        if not os.path.exists(results_csv_file_path):
            raise SystemExit(f'ERROR: {results_csv_file_path} was not found.')
        with open(results_csv_file_path) as res_file:
            header = res_file.readline()
            results = res_file.readlines()

        headers_list = header.split(',')
        if headers_list[LABEL_HEADER_INDEX] != LABEL_HEADER:
            raise SystemExit(f'ERROR: {results_csv_file_path} has unexpected header. '
                             f'Actual: {headers_list[LABEL_HEADER_INDEX]}, Expected: {LABEL_HEADER}')
        if headers_list[SAMPLES_HEADER_INDEX] != SAMPLES_HEADER:
            raise SystemExit(f'ERROR: {results_csv_file_path} has unexpected header. '
                             f'Actual: {headers_list[SAMPLES_HEADER_INDEX]}, Expected: {SAMPLES_HEADER}')

        for line in results:
            if any(s in line for s in GIT_OPERATIONS):
                count = count + int(line.split(',')[SAMPLES_HEADER_INDEX])

        return count

    @staticmethod
    def is_all_tests_successful(tests):
        for success_rate in tests.values():
            if success_rate < SUCCESS_TEST_RATE:
                return False
        return True

    def __is_success(self):
        message = 'OK'
        if not self.jmeter_test_rates:
            return False, f"JMeter test results was not found."
        if not self.selenium_test_rates:
            return False, f"Selenium test results was not found."

        success = (self.is_all_tests_successful(self.jmeter_test_rates) and
                   self.is_all_tests_successful(self.selenium_test_rates))

        if not success:
            message = f"One or more actions have success rate < {SUCCESS_TEST_RATE} %."
        return success, message

    def __is_finished(self):
        message = 'OK'
        finished = self.actual_duration >= self.duration
        if not finished:
            message = (f"Actual test duration {self.actual_duration} sec "
                       f"< than expected test_duration {self.duration} sec.")
        return finished, message

    def __is_compliant(self):
        message = 'OK'
        compliant = (self.actual_duration >= MIN_DEFAULTS[self.application.type]['test_duration'] and
                     self.concurrency >= MIN_DEFAULTS[self.application.type]['concurrency'])
        if not compliant:
            err_msg = []
            if self.actual_duration < MIN_DEFAULTS[self.application.type]['test_duration']:
                err_msg.append(f"Test run duration {self.actual_duration} sec < than minimum test "
                               f"duration {MIN_DEFAULTS[self.application.type]['test_duration']} sec.")
            if self.concurrency < MIN_DEFAULTS[self.application.type]['concurrency']:
                err_msg.append(f"Test run concurrency {self.concurrency} < than minimum test "
                               f"concurrency {MIN_DEFAULTS[self.application.type]['concurrency']}.")
            message = ' '.join(err_msg)
        return compliant, message

    def __is_git_operations_compliant(self):
        # calculate expected git operations for a particular test duration
        message = 'OK'
        expected_get_operations_count = int(MIN_DEFAULTS[BITBUCKET]['git_operations_per_hour'] / 3600 * self.duration)
        git_operations_compliant = self.actual_git_operations_count >= expected_get_operations_count
        if not git_operations_compliant:
            message = (f"Total git operations {self.actual_git_operations_count} < than "
                       f"{expected_get_operations_count} - minimum for expected duration {self.duration} sec.")
        return git_operations_compliant, message

    def generate_report_summary(self):
        summary_report = []
        summary_report_file = f'{self.bzt_log.log_dir}/results_summary.log'

        finished = self.__is_finished()
        compliant = self.__is_compliant()
        success = self.__is_success()

        overall_status = 'OK' if finished[0] and success[0] and compliant[0] else 'FAIL'

        if self.application.type == BITBUCKET:
            git_compliant = self.__is_git_operations_compliant()
            overall_status = 'OK' if finished[0] and success[0] and compliant[0] and git_compliant[0] else 'FAIL'

        summary_report.append(f'Summary run status|{overall_status}\n')
        summary_report.append(f'Artifacts dir|{os.path.basename(self.bzt_log.log_dir)}')
        summary_report.append(f'OS|{self.os}')
        summary_report.append(f'DC Apps Performance Toolkit version|{self.tool_version}')
        summary_report.append(f'Application|{self.application.type} {self.application_version}')
        summary_report.append(f'Dataset info|{self.dataset_information}')
        summary_report.append(f'Application nodes count|{self.nodes_count}')
        summary_report.append(f'Concurrency|{self.concurrency}')
        summary_report.append(f'Expected test run duration from yml file|{self.duration} sec')
        summary_report.append(f'Actual test run duration|{self.actual_duration} sec')

        if self.application.type == BITBUCKET:
            summary_report.append(f'Total Git operations count|{self.actual_git_operations_count}')
            summary_report.append(f'Total Git operations compliant|{git_compliant}')

        summary_report.append(f'Finished|{finished}')
        summary_report.append(f'Compliant|{compliant}')
        summary_report.append(f'Success|{success}\n')

        summary_report.append(f'Action|Success Rate|Status')

        for key, value in {**self.jmeter_test_rates, **self.selenium_test_rates}.items():
            status = 'OK' if value >= SUCCESS_TEST_RATE else 'Fail'
            summary_report.append(f'{key}|{value}|{status}')

        pretty_report = map(self.format_string, summary_report)

        self.__write_to_file(pretty_report, summary_report_file)

    @staticmethod
    def __write_to_file(content, file):
        with open(file, 'w') as f:
            f.writelines(content)

    @staticmethod
    def format_string(string_to_format, offset=50):
        # format string with delimiter "|"
        return ''.join([f'{item}{" " * (offset - len(str(item)))}' for item in string_to_format.split("|")]) + "\n"


class AnalyticsSender:

    def __init__(self, analytics_instance):
        self.analytics = analytics_instance

    def send_request(self):
        headers = {"Content-Type": "application/json"}
        payload = {"run_id": self.analytics.run_id,
                   "user_id": self.analytics.uniq_user_id,
                   "app_version": self.analytics.application_version,
                   "date": self.analytics.date,
                   "time_stamp": self.analytics.time_stamp,
                   "app_type": self.analytics.application_type,
                   "os": self.analytics.os,
                   "tool_ver": self.analytics.tool_version,
                   "exp_dur": self.analytics.duration,
                   "act_dur": self.analytics.actual_duration,
                   "selenium_test_rates": self.analytics.selenium_test_rates,
                   "jmeter_test_rates": self.analytics.jmeter_test_rates,
                   "concurrency": self.analytics.concurrency
                   }
        r = requests.post(url=f'{BASE_URL}', json=payload, headers=headers)
        print(r.json())
        if r.status_code != 200:
            print(f'Analytics data was send unsuccessfully, status code {r.status_code}')


def main():
    application = ApplicationSelector(sys.argv).application
    collector = AnalyticsCollector(application)
    collector.generate_analytics()
    collector.generate_report_summary()
    if collector.is_analytics_enabled():
        sender = AnalyticsSender(collector)
        sender.send_request()


if __name__ == '__main__':
    main()
