from flask import Blueprint, current_app

from api.client import FarsightClient
from api.utils import jsonify_data, get_key

health_api = Blueprint('health', __name__)


@health_api.route('/health', methods=['POST'])
def health():
    key = get_key()

    client = FarsightClient(current_app.config['API_URL'],
                            key,
                            current_app.config['USER_AGENT'])

    _ = client.summarize({'value': 'www.farsightsecurity.com',
                          'type': 'domain'})

    return jsonify_data({'status': 'ok'})
