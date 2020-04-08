import pytest
from main_app import app


class TestProjectGET:
    app = app.test_client()

    def test_get_404(self):
        result = self.app.get('/api/v0/user/-1')
        assert result.status_code == 404

    def test_get_200(self):
        result = self.app.get('/api/v0/user/1')
        assert result.status_code == 200
