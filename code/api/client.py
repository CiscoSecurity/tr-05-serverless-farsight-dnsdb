import json
from datetime import datetime, timedelta
from http import HTTPStatus

import requests
from requests.exceptions import SSLError, InvalidHeader

from api.errors import (
    UnsupportedObservableTypeError,
    CriticalFarsightResponseError,
    FarsightSSLError,
    AuthorizationError
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

    @staticmethod
    def _time_filter(days_delta):
        start = datetime.now() - timedelta(days=days_delta)
        return f'&time_last_after={int(start.timestamp())}'

    def _request_farsight(self, observable, action,
                          number_of_days_to_filter=None, limit=None):

        path = self._path(observable['type'])
        time_filter = self._time_filter(
            number_of_days_to_filter) if number_of_days_to_filter else ''

        url = join_url(
            self.base_url,
            action,
            path,
            observable["value"],
            '?humantime=True&aggr=False',
            f'&limit={limit}' if limit else '',
            time_filter
        )
        try:
            response = requests.get(url, headers=self.headers)
        except SSLError as error:
            raise FarsightSSLError(error)
        except (UnicodeEncodeError, InvalidHeader):
            raise AuthorizationError

        if response.status_code == HTTPStatus.FORBIDDEN:
            raise AuthorizationError(response.text)

        if response.ok:
            return [json.loads(raw) for raw in response.iter_lines()]

        if response.status_code in NOT_CRITICAL_ERRORS:
            return []

        raise CriticalFarsightResponseError(response)

    def lookup(self, observable, number_of_days_to_filter=None, limit=None):
        return self._request_farsight(
            observable, 'lookup', number_of_days_to_filter, limit
        )
