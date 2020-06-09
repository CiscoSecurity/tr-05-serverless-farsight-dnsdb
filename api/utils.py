import json
from typing import Optional

from authlib.jose import jwt
from authlib.jose.errors import JoseError
from flask import request, current_app, jsonify, g

from api.errors import InvalidJWTError, InvalidArgumentError


def get_jwt():
    """
    Parse the incoming request's Authorization Bearer JWT for some credentials.
    Validate its signature against the application's secret key.

    """

    try:
        scheme, token = request.headers['Authorization'].split()
        assert scheme.lower() == 'bearer'
        return jwt.decode(token, current_app.config['SECRET_KEY'])
    except (KeyError, ValueError, AssertionError, JoseError):
        raise InvalidJWTError


def get_key() -> Optional[str]:
    return get_jwt().get('key')


def get_json(schema):
    """
    Parse the incoming request's data as JSON.
    Validate it against the specified schema.

    """

    data = request.get_json(force=True, silent=True, cache=False)

    message = schema.validate(data)

    if message:
        raise InvalidArgumentError(
            f'Invalid JSON payload received. {json.dumps(message)}'
        )

    return data


def jsonify_data(data):
    return jsonify({'data': data})


def jsonify_errors(error):
    return jsonify({'errors': [error]})


def jsonify_result():
    result = {'data': {}}

    if g.get('sightings'):
        result['data']['sightings'] = format_docs(g.sightings)

    if g.get('errors'):
        result['errors'] = g.errors

    return jsonify(result)


def format_docs(docs):
    return {'count': len(docs), 'docs': docs}


def join_url(base, *parts):
    return '/'.join(
        [base.rstrip('/')] +
        [part.strip('/') for part in parts]
    )


def all_subclasses(cls):
    """
    Retrieve set of class subclasses recursively.

    """
    subclasses = set(cls.__subclasses__())
    return subclasses.union(s for c in subclasses for s in all_subclasses(c))
