import json
from http import HTTPStatus

import requests

from api.errors import (
    UnsupportedObservableTypeError,
    UnexpectedFarsightResponseError
)
from api.utils import join_url

NOT_CRITICAL_ERRORS = (HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND)


class FarsightClient:
    def __init__(self, base_url, api_key, user_agent):
        self.base_url = base_url
        self.headers = {
            'Accept': 'application/json',
            'X-API-Key': api_key,
            'User-Agent': user_agent
        }

    @staticmethod
    def _path(type_):
        path = {
            'domain': 'rrset/name/',
            'ip': 'rdata/ip/',
            'ipv6': 'rdata/ip/',
        }.get(type_)

        if not path:
            raise UnsupportedObservableTypeError(type_)

        return path

    def _request_farsight(self, observable, action, limit=None):

        path = self._path(observable['type'])

        url = join_url(
            self.base_url,
            action,
            path,
            observable["value"],
            '?humantime=True&aggr=False',
            f'&limit={limit}' if limit else ''
        )
        response = requests.get(url, headers=self.headers)

        if response.ok:
            return [json.loads(raw) for raw in response.iter_lines()]

        if response.status_code in NOT_CRITICAL_ERRORS:
            return []

        raise UnexpectedFarsightResponseError(response)

    def lookup(self, observable, limit=None):
        return self._request_farsight(observable, 'lookup', limit)
