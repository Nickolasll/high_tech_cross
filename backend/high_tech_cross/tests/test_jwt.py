import json
import uuid
import jwt

from http import HTTPStatus
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from ..config import JWT_SECRET_KEY


class TestJWT(TestCase):

    def get(self, token: str):
        return self.client.get(
            path='/api/competition',
            HTTP_Authorization=token
        )

    def test_not_bearer_token(self):
        token = 'NotBearer 12345'
        response = self.get(token)
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Invalid token'

    def test_no_token(self):
        response = self.client.get(
            path='/api/competition',
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Token not found'

    def test_wrong_app_token(self):
        current_time = timezone.now()
        exp = current_time + timedelta(hours=5)
        payload = {
            'exp': exp,
            'iat': current_time,
            'bla bla bla': str(uuid.uuid4())
        }
        token = jwt.encode(
            payload,
            'My own secret',
            algorithm='HS256'
        )
        token = token.decode()
        token = f'Bearer {token}'
        response = self.get(token)
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Invalid token'

    def test_no_bearer(self):
        token = "12345"
        response = self.get(token)
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Invalid token'

    def test_expired_token(self):
        current_time = timezone.now() - timedelta(hours=6)
        exp = current_time + timedelta(hours=5)
        payload = {
            'exp': exp,
            'iat': current_time,
            'team_id': str(uuid.uuid4()),
            'competition_id': str(uuid.uuid4())
        }
        token = jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm='HS256'
        )
        token = token.decode()
        token = f'Bearer {token}'
        response = self.get(token)
        assert response.status_code == HTTPStatus.FORBIDDEN
        data = json.loads(response.content)
        assert data['detail'] == 'Token expired'
