import pytest
from main_app import app, API_VER
from data import db_session
import random

app.config['SQLITE3_SETTINGS'] = {
    'host': 'db/bugtracker_test.sqlite'
}

app.testing = True
testing_app = app.test_client()
db_session.global_init('db/bugtracker_test.sqlite')
CURRENT_API_VER = f'/api/v{API_VER}'
# TEST API_KEYS
FIRST_TEST_ACCOUNT_API_KEY = "OWJEAOOVSRRBVXTFLVNQVKJG"
SECOND_TEST_ACCOUNT_API_KEY = "OQUJGOOLQJPDMJOMRAUEKSQW"

# THIS IS LIST OF DICT THAT CONTAIN TEST DATA
TEST_DATA = [
    {
        'API_KEY': FIRST_TEST_ACCOUNT_API_KEY,
        'ISSUE_ID_404': 1,
        'ISSUE_ID_403': 'API2-1',
        'ISSUE_ID_200': 'API1-1',
        'PROJECT_ID_404': -1,
        'PROJECT_ID_403': 3,
        'PROJECT_ID_200': 2
    },
    {
        'API_KEY': SECOND_TEST_ACCOUNT_API_KEY,
        'ISSUE_ID_404': 1,
        'ISSUE_ID_403': 'API1-1',
        'ISSUE_ID_200': 'API2-1',
        'PROJECT_ID_404': 12342341,
        'PROJECT_ID_403': 2,
        'PROJECT_ID_200': 3
    }
]


class TestConnectionToWebSite:
    def test_connection(self):
        result = testing_app.get('/')
        assert result.status_code == 200


class TestUserGET:
    """
    This class implements GET requests to API for User entity
    """

    def test_get_404_due_invalid_id(self):
        """
        Test with passing incorrect user id, API should return error code 404
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/user/?user_id=-1')
        print(result.json)
        assert result.status_code == 404
        assert result.json['message'] == "Instance of <class 'data.models.User'> with id = -1 not found"

    def test_get_401_with_key_equal_none(self):
        """
        Test with passing correct user_id but incorrect API key(None), API should return error code 401
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/user/?API_KEY=None&user_id=1')
        assert result.status_code == 401

    def test_get_401_with_bad_key(self):
        """
        Test with passing correct user_id bu incorrect API key, API should return error code 401
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/user/?API_KEY=dgdhfkj&user_id=1')
        assert result.status_code == 401

    def test_get_200(self):
        """
        Test with passing correct API key and correct user ID, API should return code 200
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/user/?API_KEY=DRWLFSSZOHTTFBFIUDJVPKXD&user_id=1')
        print(result.json)
        assert result.status_code == 200


class TestProjectGET:
    """
    This class implements GET requests to API for Project entity
    """

    def test_get_404_due_invalid_id_negative_int(self):
        """
        Test with passing invalid project id(Negative integer) but correct API_KEY, API should return 404 error code
        :return: None
        """
        negative_int_test = testing_app.get(
            f'{CURRENT_API_VER}/project/?API_KEY=DRWLFSSZOHTTF1BFIUDJVPKXD&project_id=-1')
        assert negative_int_test.status_code == 404

    def test_get_404_due_invalid_id_floating_point(self):
        """
        Test with passing invalid project id(float) but correct API_KEY, API should return 404 error code
        :return: None
        """
        floating_point_test = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY={TEST_DATA[1]["API_KEY"]}&'
                                              f'project_id=1.3')
        assert floating_point_test.status_code == 404

    def test_get_404_due_invalid_id_string(self):
        """
        Test with passing invalid project id(string) but correct API_KEY, API should return 404 error code
        :return: None
        """
        string_test_request = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY={TEST_DATA[0]["API_KEY"]}&'
                                              f'project_id=randomstring')
        assert string_test_request.status_code == 404

    def test_get_404_due_invalid_id_random_int(self):
        """
        Test with passing invalid project id(random_int) but correct API_KEY, API should return 404 error code
        :return: None
        """
        negative_int_test = testing_app.get(
            f'{CURRENT_API_VER}/project/?API_KEY=DRWLFSSZOHTTF1BFIUDJVPKXD&project_id={random.randint(10000, 99999)}')
        assert negative_int_test.status_code == 404

    def test_get_401_due_api_key_equal_none(self):
        """
        Test with passing correct project_id but incorrect API key(None), API should return error code 401
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=None&project_id=1')
        assert result.status_code == 401

    def test_get_401_due_bad_api_key(self):
        """
        Test with passing correct project_id but incorrect API key(random string), API should return error code 401
        :return: None
        """

        request = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=randomkey&project_id=1')
        assert request.status_code == 401

    def test_get_403_due_api_key_that_doesnt_have_access_to_project(self):
        """
        Test with passing API key what's owner doesn't have access to the project, API should return 403
        :return: None
        """

        request = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=a&project_id=1')

        second_request = testing_app.get(
            f'{CURRENT_API_VER}/project/?API_KEY={TEST_DATA[0]["API_KEY"]}&project_id={TEST_DATA[0]["PROJECT_ID_403"]}')

        third_request = testing_app.get(
            f'{CURRENT_API_VER}/project/?API_KEY={TEST_DATA[1]["API_KEY"]}&project_id={TEST_DATA[1]["PROJECT_ID_403"]}')

        assert request.status_code == 403
        assert second_request.status_code == 403
        assert third_request.status_code == 403

    def test_get_200(self):
        """
        API key and project_id is correct. User has access to project
        :return: None
        """
        result = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=DRWLFSSZOHTTFBFIUDJVPKXD&project_id=1')
        second_request = testing_app.get(
            f'{CURRENT_API_VER}/project/?API_KEY={TEST_DATA[0]["API_KEY"]}&project_id={TEST_DATA[0]["PROJECT_ID_200"]}')

        third_request = testing_app.get(
            f'{CURRENT_API_VER}/project/?API_KEY={TEST_DATA[1]["API_KEY"]}&project_id={TEST_DATA[1]["PROJECT_ID_200"]}')

        assert result.status_code == 200
        assert second_request.status_code == 403
        assert third_request.status_code == 403


class TestIssueGET:
    """
    This class implements GET requests to API for Issue entity
    """

    def test_get_404_by_invalid_id(self):
        single_int_test = testing_app.get(f'{CURRENT_API_VER}/issue/?API_KEY=DRWLFSSZOHTTFBFIUDJVPKXD&tag=1')
        assert single_int_test.status_code == 404

    def test_get_404_by_invalid_id_lot_of_data(self):
        lot_of_data_test = testing_app.get(
            f'{CURRENT_API_VER}/issue/?API_KEY=DRWLFSSZOHTTFBFIUDJVPKXD&tag=MORE_THAN_5_SYMB')
        assert lot_of_data_test.status_code == 404

    def test_get_404_by_invalid_id_floating_point(self):
        floating_point_testrequest = testing_app.get(
            f'{CURRENT_API_VER}/issue/?API_KEY=DRWLFSSZOHTTFBFIUDJVPKXD&tag=1.5')
        assert floating_point_testrequest.status_code == 404

    def test_get_404_by_invalid_id_random_int(self):
        random_int_test = testing_app.get(f'{CURRENT_API_VER}/issue/?API_KEY=DRWLFSSZOHTTFBFIUDJVPKXD&tag='
                                          f'{random.randint(1, 10000)}')
        assert random_int_test.status_code == 404

    def test_get_403_due_api_key_that_doesnt_have_access_to_project(self):
        first_account_test = testing_app.get(f'{CURRENT_API_VER}/issue/?API_KEY={TEST_DATA[0]["API_KEY"]}'
                                             f'&tag={TEST_DATA[0]["ISSUE_ID_403"]}')
        second_account_test = testing_app.get(f'{CURRENT_API_VER}/issue/?API_KEY={TEST_DATA[1]["API_KEY"]}'
                                              f'&tag={TEST_DATA[1]["ISSUE_ID_403"]}')
        assert first_account_test.status_code == 403
        assert second_account_test.status_code == 403

    def test_get_403_on_request_issues_list_due_bad_api_key(self):
        first_account_test = testing_app.get(f'{CURRENT_API_VER}/issues/?API_KEY={TEST_DATA[0]["API_KEY"]}'
                                             f'&tag={TEST_DATA[1]["ISSUE_ID_403"]}')
        second_account_test = testing_app.get(f'{CURRENT_API_VER}/issues/?API_KEY={TEST_DATA[1]["API_KEY"]}'
                                              f'&tag={TEST_DATA[1]["ISSUE_ID_403"]}')
        assert first_account_test.status_code == 403
        assert second_account_test.status_code == 403

    def test_get_403_on_request_issues_list_due_api_key_owner_not_an_admin(self):
        test_case = testing_app.get(f'{CURRENT_API_VER}/issues/?API_KEY={TEST_DATA[0]["API_KEY"]}')
        assert test_case.status_code == 403
        assert test_case.json['message'] == 'Only admin can access to list of all Issues'
