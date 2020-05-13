import json

import requests

from api.errors import (
    UnsupportedObservableTypeError,
    UnexpectedFarsightResponseError
)
from api.utils import join_url


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

        if not response.ok:
            raise UnexpectedFarsightResponseError(response)

        return [json.loads(raw) for raw in response.iter_lines()]

    def lookup(self, observable, limit=None):
        return self._request_farsight(observable, 'lookup', limit)
