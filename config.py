import os

from version import VERSION


class Config:
    VERSION = VERSION

    SECRET_KEY = os.environ.get('SECRET_KEY', None)

    API_URL = 'https://api.dnsdb.info/'

    UI_SEARCH_URL = 'https://scout.dnsdb.info/?seed={query}'
    FARSIGHT_OBSERVABLES = {
        'ip': 'IP',
        'ipv6': 'IPv6',
        'domain': 'domain'
    }

    USER_AGENT = ('Cisco Threat Response Integrations '
                  '<tr-integrations-support@cisco.com>')

    NUMBER_OF_DAYS_FOR_FARSIGHT_TIME_FILTER = 90

    CTR_ENTITIES_LIMIT_DEFAULT = 100
    CTR_ENTITIES_LIMIT_MAX = 1000

    try:
        CTR_ENTITIES_LIMIT = int(os.environ['CTR_ENTITIES_LIMIT'])
        assert CTR_ENTITIES_LIMIT > 0
    except (KeyError, ValueError, AssertionError):
        CTR_ENTITIES_LIMIT = CTR_ENTITIES_LIMIT_DEFAULT

    if CTR_ENTITIES_LIMIT > CTR_ENTITIES_LIMIT_MAX:
        CTR_ENTITIES_LIMIT = CTR_ENTITIES_LIMIT_MAX

    # True by default
    AGGREGATE = str(os.environ.get('AGGREGATE')).lower() != 'false'
