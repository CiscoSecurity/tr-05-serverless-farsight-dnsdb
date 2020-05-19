import json
from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock

from authlib.jose import jwt
from pytest import fixture

from api.errors import PERMISSION_DENIED, INVALID_ARGUMENT
from app import app


@fixture(scope='session')
def secret_key():
    # Generate some string based on the current datetime.
    return datetime.utcnow().isoformat()


@fixture(scope='session')
def client(secret_key):
    app.secret_key = secret_key

    app.testing = True

    with app.test_client() as client:
        yield client


def farsight_api_response_mock(status_code, payload=None):
    def iter_lines():
        for r in payload:
            yield r

    mock_response = MagicMock()

    mock_response.status = status_code
    mock_response.ok = status_code == HTTPStatus.OK

    payload = payload or []
    payload = (json.dumps(r) for r in payload)

    mock_response.iter_lines = iter_lines

    return mock_response


def farsight_api_error_mock(status_code, text=None):
    mock_response = MagicMock()

    mock_response.status_code = status_code
    mock_response.ok = status_code == HTTPStatus.OK

    mock_response.text = text

    return mock_response


@fixture(scope='session')
def farsight_response_ok(secret_key):
    return farsight_api_response_mock(
            HTTPStatus.OK, payload=[
                {
                    "count": 4,
                    "time_first": "2013-01-18T05:38:08Z",
                    "time_last": "2013-01-22T23:17:10Z",
                    "rrname": "google.com.",
                    "rrtype": "A",
                    "bailiwick": ".",
                    "rdata": ["74.125.128.100", "74.125.128.101"]
                }
            ]
        )


@fixture(scope='session')
def farsight_response_unauthorized_creds(secret_key):
    return farsight_api_error_mock(
        HTTPStatus.FORBIDDEN,
        'Error: Bad API key'
    )


@fixture(scope='module')
def unauthorized_creds_expected_payload(route):
    if route in ('/observe/observables', '/health'):
        return {
            'errors': [
                {'code': PERMISSION_DENIED,
                 'message': ("Unexpected response from Farsight DNSDB: "
                             "Error: Bad API key"),
                 'type': 'fatal'}
            ]
        }

    if route.endswith('/deliberate/observables'):
        return {'data': {}}

    if route.endswith('/refer/observables'):
        return {'data': []}


@fixture(scope='session')
def valid_jwt(client):
    header = {'alg': 'HS256'}

    payload = {'username': 'gdavoian', 'superuser': False}

    secret_key = client.application.secret_key

    return jwt.encode(header, payload, secret_key).decode('ascii')


@fixture(scope='session')
def invalid_jwt(valid_jwt):
    header, payload, signature = valid_jwt.split('.')

    def jwt_decode(s: str) -> dict:
        from authlib.common.encoding import urlsafe_b64decode, json_loads
        return json_loads(urlsafe_b64decode(s.encode('ascii')))

    def jwt_encode(d: dict) -> str:
        from authlib.common.encoding import json_dumps, urlsafe_b64encode
        return urlsafe_b64encode(json_dumps(d).encode('ascii')).decode('ascii')

    payload = jwt_decode(payload)

    # Corrupt the valid JWT by tampering with its payload.
    payload['superuser'] = True

    payload = jwt_encode(payload)

    return '.'.join([header, payload, signature])


@fixture(scope='module')
def invalid_jwt_expected_payload(route):
    if route in ('/observe/observables', '/health'):
        return {
            'errors': [
                {'code': PERMISSION_DENIED,
                 'message': 'Invalid Authorization Bearer JWT.',
                 'type': 'fatal'}
            ]
        }

    if route.endswith('/deliberate/observables'):
        return {'data': {}}

    if route.endswith('/refer/observables'):
        return {'data': []}


@fixture(scope='module')
def invalid_json_expected_payload(route, client):
    if route.endswith('/observe/observables'):
        return {'errors': [
            {'code': INVALID_ARGUMENT,
             'message': "{0: {'value': ['Missing data for required field.']}}",
             'type': 'fatal'}
        ]}

    if route.endswith('/deliberate/observables'):
        return {'data': {}}

    return {'data': []}
