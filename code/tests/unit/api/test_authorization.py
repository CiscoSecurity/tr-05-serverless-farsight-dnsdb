from .utils import headers
from pytest import fixture
from http import HTTPStatus
from requests.exceptions import InvalidURL, ConnectionError
from api.utils import (
    NO_AUTH_HEADER,
    WRONG_AUTH_TYPE,
    WRONG_JWKS_HOST,
    WRONG_PAYLOAD_STRUCTURE,
    JWKS_HOST_MISSING,
    WRONG_KEY,
    WRONG_JWT_STRUCTURE,
    WRONG_AUDIENCE,
    KID_NOT_FOUND
)


def routes():
    yield '/health'
    yield '/observe/observables'


@fixture(scope='module', params=routes(), ids=lambda route: f'POST {route}')
def route(request):
    return request.param


def test_call_with_authorization_header_failure(
        route, client, valid_json,
        authorization_errors_expected_payload
):
    response = client.post(route, json=valid_json)

    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        NO_AUTH_HEADER
    )


def test_call_with_wrong_auth_type(
        route, client, valid_json, valid_jwt,
        authorization_errors_expected_payload
):
    response = client.post(
        route, json=valid_json,
        headers=headers(valid_jwt(), auth_type='not')
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        WRONG_AUTH_TYPE
    )


def test_call_with_wrong_jwks_host(
        route, client, valid_json, valid_jwt, mock_request,
        authorization_errors_expected_payload
):
    for error in (ConnectionError, InvalidURL):
        mock_request.side_effect = error()

        response = client.post(
            route, json=valid_json, headers=headers(valid_jwt())
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json == authorization_errors_expected_payload(
            WRONG_JWKS_HOST
        )


def test_call_with_wrong_jwt_payload_structure(
        route, client, valid_json, valid_jwt, mock_request,
        authorization_errors_expected_payload, get_public_key
):
    mock_request.return_value = get_public_key

    response = client.post(
        route, json=valid_json,
        headers=headers(valid_jwt(wrong_structure=True))
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        WRONG_PAYLOAD_STRUCTURE
    )


def test_call_with_missing_jwks_host(
        route, client, valid_json, valid_jwt, mock_request,
        authorization_errors_expected_payload, get_public_key
):
    mock_request.return_value = get_public_key

    response = client.post(
        route, json=valid_json,
        headers=headers(valid_jwt(jwks_host=''))
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        JWKS_HOST_MISSING
    )


def test_call_with_wrong_key(
        route, client, valid_json, valid_jwt, mock_request,
        authorization_errors_expected_payload, get_wrong_public_key
):
    mock_request.return_value = get_wrong_public_key

    response = client.post(
        route, json=valid_json,
        headers=headers(valid_jwt())
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        WRONG_KEY
    )


def test_call_with_wrong_jwt_structure(
        route, client, valid_json, mock_request,
        authorization_errors_expected_payload, get_public_key
):
    mock_request.return_value = get_public_key

    response = client.post(
        route, json=valid_json,
        headers=headers('valid_jwt()')
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        WRONG_JWT_STRUCTURE
    )


def test_call_with_wrong_audience(
        route, client, valid_json, valid_jwt, mock_request,
        authorization_errors_expected_payload, get_public_key
):
    mock_request.return_value = get_public_key

    response = client.post(
        route, json=valid_json,
        headers=headers(valid_jwt(aud='wrong_aud'))
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        WRONG_AUDIENCE
    )


def test_call_with_wrong_kid(
        route, client, valid_json, valid_jwt, mock_request,
        authorization_errors_expected_payload, get_public_key
):
    mock_request.return_value = get_public_key

    response = client.post(
        route, json=valid_json,
        headers=headers(valid_jwt(kid='wrong_kid'))
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == authorization_errors_expected_payload(
        KID_NOT_FOUND
    )