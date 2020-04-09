import pytest
from main_app import app

testing_app = app.test_client()


class TestConnectionToWebSite:
    def test_connection(self):
        result = testing_app.get('/')
        assert result.status_code == 200


class TestUserGET:
    def test_get_404(self):
        result = testing_app.get('/api/v0/user/-1')
        assert result.status_code == 404

    def test_get_200(self):
        result = testing_app.get('/api/v0/user/1')
        assert result.status_code == 200
