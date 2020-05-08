import os

from version import VERSION


class Config:
    VERSION = VERSION

    SECRET_KEY = os.environ.get('SECRET_KEY', '')

    API_URL = 'https://api.dnsdb.info/'

    USER_AGENT = ('Cisco Threat Response Integrations '
                  '<tr-integrations-support@cisco.com>')
