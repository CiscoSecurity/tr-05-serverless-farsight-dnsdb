import json


class Config:
    settings = json.load(open('container_settings.json', 'r'))
    VERSION = settings["VERSION"]

    API_URL = 'https://api.dnsdb.info/'

    UI_SEARCH_URL = 'https://scout.dnsdb.info/?seed={query}'
    FARSIGHT_OBSERVABLES = {
        'ip': 'IP',
        'ipv6': 'IPv6',
        'domain': 'domain'
    }

    USER_AGENT = ('SecureX Threat Response Integrations '
                  '<tr-integrations-support@cisco.com>')

    CTR_ENTITIES_LIMIT_MAX = 1000
    CTR_ENTITIES_LIMIT_DEFAULT = 100
    NUMBER_OF_DAYS_FOR_FARSIGHT_TIME_FILTER = 90

    CTR_ENTITIES_LIMIT = CTR_ENTITIES_LIMIT_DEFAULT

    if CTR_ENTITIES_LIMIT > CTR_ENTITIES_LIMIT_MAX:
        CTR_ENTITIES_LIMIT = CTR_ENTITIES_LIMIT_MAX

    AGGREGATE_DEFAULT = True
