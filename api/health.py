import requests
from flask import Blueprint, current_app

from api.errors import UnexpectedFarsightResponseError
from api.utils import jsonify_data, get_key

health_api = Blueprint('health', __name__)


@health_api.route('/health', methods=['POST'])
def health():
    key = get_key()

    headers = {'Accept': 'application/json',
               'User-Agent': current_app.config['USER_AGENT'],
               'X-API-Key': key}

    url = f"{current_app.config['API_URL']}/summarize/rrset/name/www.farsightsecurity.com?limit=1"
    response = requests.get(url, headers=headers)

    if not response.ok:
        raise UnexpectedFarsightResponseError(response)

    return jsonify_data({'status': 'ok'})
