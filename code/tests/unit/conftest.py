import jwt
import json

from app import app
from pytest import fixture
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from api.errors import INVALID_ARGUMENT, UNKNOWN, AUTH_ERROR
from tests.unit.mock_for_tests import (
    PRIVATE_KEY,
    EXPECTED_RESPONSE_OF_JWKS_ENDPOINT,
    RESPONSE_OF_JWKS_ENDPOINT_WITH_WRONG_KEY
)


@fixture(scope='session')
def client():
    app.rsa_private_key = PRIVATE_KEY

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
def get_public_key():
    mock_response = MagicMock()
    payload = EXPECTED_RESPONSE_OF_JWKS_ENDPOINT

    mock_response.json = lambda: payload
    return mock_response


@fixture(scope='session')
def get_wrong_public_key():
    mock_response = MagicMock()
    payload = RESPONSE_OF_JWKS_ENDPOINT_WITH_WRONG_KEY
    mock_response.json = lambda: payload
    return mock_response


@fixture(scope='session')
def valid_jwt(client):
    def _make_jwt(
            key='some_key',
            jwks_host='visibility.amp.cisco.com',
            aud='http://localhost',
            kid='02B1174234C29F8EFB69911438F597FF3FFEE6B7',
            aggregate=True,
            ctr_entities_limit=0,
            wrong_structure=False,
            wrong_jwks_host=False,
    ):
        payload = {
            'key': key,
            'jwks_host': jwks_host,
            'aud': aud,
            'AGGREGATE': aggregate,
            'CTR_ENTITIES_LIMIT': ctr_entities_limit
        }

        if wrong_jwks_host:
            payload.pop('jwks_host')

        if wrong_structure:
            payload.pop('key')

        return jwt.encode(
            payload, client.application.rsa_private_key, algorithm='RS256',
            headers={
                'kid': kid
            }
        )

    return _make_jwt


@fixture(scope='function')
def mock_request():
    with patch('requests.get') as mock_request:
        yield mock_request


@fixture(scope='module')
def valid_json():
    return [{'type': 'domain', 'value': 'google.com'}]


@fixture(scope='module')
def invalid_json():
    return [{'type': 'domain'}]


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
def farsight_response_not_found():
    return farsight_api_error_mock(
        HTTPStatus.NOT_FOUND,
        'Error: Not Found'
    )


@fixture(scope='session')
def farsight_response_unauthorized_creds():
    return farsight_api_error_mock(
        HTTPStatus.FORBIDDEN,
        'Error: Bad API key'
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
            {'code': AUTH_ERROR,
             'message': ("Authorization failed: "
                         "Error: Bad API key"),
             'type': 'fatal'}
        ]
    }


@fixture(scope='module')
def sslerror_expected_payload():
    return {
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
def invalid_json_expected_payload(route):
    return expected_payload(
        route,
        {
            'errors': [
                {
                    'code': INVALID_ARGUMENT,
                    'message':
                    'Invalid JSON payload received. '
                    '{"0": {"value": ["Missing data for required field."]}}',
                    'type': 'fatal'
                }
            ]
        }
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
        ]
    }


@fixture(scope='module')
def success_enrich_expected_payload(
        route, success_enrich_body, success_enrich_refer_body
):
    return expected_payload(
        route, success_enrich_body, success_enrich_refer_body
    )


@fixture(scope='module')
def authorization_errors_expected_payload(route):
    def _make_payload_message(message):
        payload = {
            'errors':
                [
                    {
                        'code': AUTH_ERROR,
                        'message': f'Authorization failed: {message}',
                        'type': 'fatal'
                    }
                ]

        }
        return payload

    return _make_payload_message
