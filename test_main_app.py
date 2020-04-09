import pytest
from main_app import app
from data import db_session

app.config['SQLITE3_SETTINGS'] = {
    'host': 'db/bugtracker_test.sqlite'
}

app.testing = True
testing_app = app.test_client()
db_session.global_init('db/bugtracker_test.sqlite')
API_VER_V0 = '/api/v0'


class TestConnectionToWebSite:
    def test_connection(self):
        result = testing_app.get('/')
        assert result.status_code == 200


class TestUserGET:
    def test_get_404(self):
        result = testing_app.get(f'{API_VER_V0}/user/-1')
        print(result.json)
        assert result.status_code == 404

    def test_get_200(self):
        result = testing_app.get(f'{API_VER_V0}/user/1')
        print(result.json)
        assert result.status_code == 200


class TestProjectGET:
    def test_get_404_due_invalid_id(self):
        """
        404 because of invalid project id
        :return:
        """
        result = testing_app.get(f'{API_VER_V0}/project/-1')
        print(result.json)
        assert result.status_code == 404

    def test_get_404_due_bad_api_key(self):
        """
        404 because of bad api key
        :return:
        """
        result = testing_app.get(f'{API_VER_V0}/project/1?API_KEY=Z')
        print(result.json)
        assert result.status_code == 404

    def test_get_403_due_api_key_that_doesnt_have_access_to_project(self):
        """
        403 due api key that doesnt have access to the project
        :return:
        """
        result = testing_app.get(f'{API_VER_V0}/project/1?API_KEY=a')
        print(result.json)
        assert result.status_code == 403
