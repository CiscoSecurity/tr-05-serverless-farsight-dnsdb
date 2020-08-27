import json
from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock

from authlib.jose import jwt
from pytest import fixture

from api.errors import PERMISSION_DENIED, INVALID_ARGUMENT, UNKNOWN
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


@fixture(scope='function')
def farsight_response_ok():
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


@fixture(scope='session')
def farsight_response_not_found(secret_key):
    return farsight_api_error_mock(
        HTTPStatus.NOT_FOUND,
        'Error: Not Found'
    )


def expected_payload(r, observe_body, refer_body=None):
    if r.endswith('/deliberate/observables'):
        return {'data': {}}

    if r.endswith('/refer/observables') and refer_body is not None:
        return refer_body

    return observe_body


@fixture(scope='module')
def unauthorized_creds_body():
    return {
        'errors': [
            {'code': PERMISSION_DENIED,
             'message': ("Unexpected response from Farsight DNSDB: "
                         "Error: Bad API key"),
             'type': 'fatal'}
        ],
        'data': {}
    }


@fixture(scope='module')
def unauthorized_creds_expected_payload(
        route, unauthorized_creds_body, success_enrich_refer_body
):
    return expected_payload(
        route, unauthorized_creds_body, success_enrich_refer_body
    )


@fixture(scope='module')
def sslerror_expected_payload():
    return {
        'data': {},
        'errors': [
            {
                'code': UNKNOWN,
                'message': 'Unable to verify SSL certificate:'
                           ' Self signed certificate',
                'type': 'fatal'
            }
        ]
    }

@fixture(scope='module')
def invalid_jwt_expected_payload(route, success_enrich_refer_body):
    return expected_payload(
        route, {
            'errors': [
                {'code': PERMISSION_DENIED,
                 'message': 'Invalid Authorization Bearer JWT.',
                 'type': 'fatal'}
            ],
            'data': {}
        },
        success_enrich_refer_body
    )


@fixture(scope='module')
def invalid_json_expected_payload(route):
    return expected_payload(
        route,
        {'errors': [
            {'code': INVALID_ARGUMENT,
             'message':
                 'Invalid JSON payload received. '
                 '{"0": {"value": ["Missing data for required field."]}}',
             'type': 'fatal'}],
            'data': {}}
    )


@fixture(scope='module')
def success_enrich_body():
    return {
        'data':
            {'sightings': {'count': 1, 'docs': [
                {'confidence': 'High', 'count': 4,
                 'description': 'IP addresses that google.com resolves to',
                 'source_uri': 'https://scout.dnsdb.info/?seed=google.com',
                 'internal': False, 'observables': [
                    {'type': 'domain', 'value': 'google.com'}],
                 'relations': [
                     {'origin': 'Farsight DNSDB Enrichment Module',
                      'related': {'type': 'ip', 'value': '74.125.128.100'},
                      'relation': 'Resolved_To',
                      'source': {'type': 'domain', 'value': 'google.com'}},
                     {'origin': 'Farsight DNSDB Enrichment Module',
                      'related': {'type': 'ip', 'value': '74.125.128.101'},
                      'relation': 'Resolved_To',
                      'source': {'type': 'domain',
                                 'value': 'google.com'}}],
                 'schema_version': '1.0.17', 'source': 'Farsight DNSDB',
                 'title': 'Found in Farsight DNSDB',
                 'type': 'sighting'}]}}}


@fixture(scope='module')
def success_enrich_refer_body():
    return {
        'data': [
            {
                'categories': ['Search', 'Farsight DNSDB'],
                'description': 'Lookup this domain on Farsight DNSDB',
                'id': 'ref-farsight-dnsdb-search-domain-google.com',
                'title': 'Search for this domain',
                'url': 'https://scout.dnsdb.info/?seed=google.com',
            }
        ]
    }


@fixture(scope='module')
def key_error_body():
    return {
        'errors': [
            {
                'type': 'fatal',
                'code': 'key error',
                'message': 'The data structure of Farsight DNSDB '
                           'has changed. The module is broken.'
            }
        ],
        'data': {}
    }


@fixture(scope='module')
def success_enrich_expected_payload(
        route, success_enrich_body, success_enrich_refer_body
):
    return expected_payload(
        route, success_enrich_body, success_enrich_refer_body
    )
