from http import HTTPStatus
from unittest.mock import patch

from pytest import fixture

from .utils import headers


def routes():
    yield '/deliberate/observables'
    yield '/observe/observables'
    yield '/refer/observables'


@fixture(scope='module', params=routes(), ids=lambda route: f'POST {route}')
def route(request):
    return request.param


def test_enrich_call_with_invalid_jwt_failure(
        route, client, invalid_jwt, invalid_jwt_expected_payload
):
    response = client.post(route, headers=headers(invalid_jwt))

    assert response.status_code == HTTPStatus.OK
    assert response.json == invalid_jwt_expected_payload


@fixture(scope='module')
def invalid_json():
    return [{'type': 'domain'}]


def test_enrich_call_with_valid_jwt_but_invalid_json_failure(
        route, client, valid_jwt, invalid_json, invalid_json_expected_payload,
):
    response = client.post(
        route, headers=headers(valid_jwt), json=invalid_json
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == invalid_json_expected_payload


@fixture(scope='module')
def valid_json():
    return [{'type': 'domain', 'value': 'google.com'}]


def test_enrich_call_with_unauthorized_creds_failure(
        route, client, valid_jwt, valid_json,
        farsight_response_unauthorized_creds,
        unauthorized_creds_expected_payload,
):
    with patch('requests.get') as get_mock:
        get_mock.return_value = farsight_response_unauthorized_creds
        response = client.post(
            route, headers=headers(valid_jwt), json=valid_json
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json == unauthorized_creds_expected_payload


def test_enrich_call_success(
        route, client, valid_jwt, valid_json,
        farsight_response_ok, success_enrich_expected_payload
):
    with patch('requests.get') as get_mock:
        get_mock.return_value = farsight_response_ok

        response = client.post(
            route, headers=headers(valid_jwt), json=valid_json
        )

        assert response.status_code == HTTPStatus.OK

        response = response.get_json()
        assert response.get('errors') is None

        if response.get('data') and response['data'].get('sightings'):
            assert response['data']['sightings']['docs'][0].pop('id')
            assert response['data']['sightings']['docs'][0].pop(
                'observed_time')

        assert response == success_enrich_expected_payload


def test_enrich_success_with_not_found(
        client, valid_jwt, valid_json,
        farsight_response_not_found
):
    with patch('requests.get') as get_mock:
        get_mock.return_value = farsight_response_not_found

        response = client.post(
            '/observe/observables', headers=headers(valid_jwt), json=valid_json
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json == {'data': {}}


@fixture(scope='module')
def valid_json_multiple():
    return [{'type': 'domain', 'value': 'google.com'},
            {'type': 'domain', 'value': '1'},
            {'type': 'domain', 'value': 'farsight.com'}]


def test_enrich_call_success_with_extended_error_handling(
        client, valid_jwt, valid_json_multiple, farsight_response_ok,
        farsight_response_unauthorized_creds, farsight_response_not_found,
        success_enrich_body, unauthorized_creds_body
):
    with patch('requests.get') as get_mock:
        get_mock.side_effect = [farsight_response_ok,
                                farsight_response_not_found,
                                farsight_response_unauthorized_creds]
        response = client.post(
            '/observe/observables', headers=headers(valid_jwt),
            json=valid_json_multiple
        )

        assert response.status_code == HTTPStatus.OK

        response = response.get_json()

        assert response['data']['sightings']['docs'][0].pop('id')
        assert response['data']['sightings']['docs'][0].pop('observed_time')

        assert response['data'] == success_enrich_body['data']
        assert response['errors'] == unauthorized_creds_body['errors']
