from http import HTTPStatus
from pytest import fixture
from .utils import headers
from requests.exceptions import SSLError
from unittest.mock import patch, MagicMock


def routes():
    yield '/health'


@fixture(scope='module', params=routes(), ids=lambda route: f'POST {route}')
def route(request):
    return request.param


def test_health_call_with_ssl_error_failure(
        route, client, valid_jwt,
        sslerror_expected_payload,
        get_public_key,
):
    with patch('requests.get') as get_mock:
        mock_exception = MagicMock()
        mock_exception.reason.args.__getitem__().verify_message \
            = 'self signed certificate'
        get_mock.side_effect = (
            get_public_key,
            SSLError(mock_exception)
        )

        response = client.post(
            route, headers=headers(valid_jwt())
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json == sslerror_expected_payload


def test_health_call_success(route, client, valid_jwt, farsight_response_ok,
                             get_public_key):
    with patch('requests.get') as get_mock:
        get_mock.side_effect = [
            get_public_key,
            farsight_response_ok
        ]
        response = client.post(route, headers=headers(valid_jwt()))

        assert response.status_code == HTTPStatus.OK
        assert response.json == {'data': {'status': 'ok'}}
