import pytest
from main_app import app
from data import db_session


app.config['SQLITE3_SETTINGS'] = {
    'host': 'db/bugtracker_test.sqlite'
}

app.testing = True
testing_app = app.test_client()
db_session.global_init('db/bugtracker_test.sqlite')
CURRENT_API_VER = '/api/v0.5.1'


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
    def test_get_404_due_invalid_id(self):
        """
        Test with passing invalid project id but correct API_KEY, API should return 404 error code
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=DRWLFSSZOHTTF1BFIUDJVPKXD&project_id=-1')
        assert result.status_code == 404

    def test_get_404_due_api_key_equal_none(self):
        """
        Test with passing correct project_id but incorrect API key(None), API should return error code 401
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=None&project_id=1')
        assert result.status_code == 401

    def test_get_404_due_bad_api_key(self):
        """
        Test with passing correct project_id but incorrect API key, API should return error code 401
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=randomkey&project_id=1')
        assert result.status_code == 401

    def test_get_403_due_api_key_that_doesnt_have_access_to_project(self):
        """
        Test with passing API key what's owner doesn't have access to the project, API should return 403
        :return: None
        """

        result = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=a&project_id=1')
        print(result.json)
        assert result.status_code == 403

    def test_get_200(self):
        """
        API key and project_id is correct. User has access to project
        :return: None
        """
        result = testing_app.get(f'{CURRENT_API_VER}/project/?API_KEY=DRWLFSSZOHTTFBFIUDJVPKXD&project_id=1')
        assert result.status_code == 200

