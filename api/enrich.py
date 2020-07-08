from functools import partial

from flask import Blueprint, current_app, g

from api.client import FarsightClient
from api.mappings import Mapping
from api.schemas import ObservableSchema
from api.utils import get_json, jsonify_data, get_key, jsonify_result

enrich_api = Blueprint('enrich', __name__)


get_observables = partial(get_json, schema=ObservableSchema(many=True))


@enrich_api.route('/deliberate/observables', methods=['POST'])
def deliberate_observables():
    return jsonify_data({})


@enrich_api.route('/refer/observables', methods=['POST'])
def refer_observables():
    return jsonify_data([])


@enrich_api.route('/observe/observables', methods=['POST'])
def observe_observables():
    key = get_key()
    observables = get_observables()

    client = FarsightClient(current_app.config['API_URL'],
                            key,
                            current_app.config['USER_AGENT'])

    g.sightings = []

    limit = current_app.config['CTR_ENTITIES_LIMIT']
    aggr = current_app.config['AGGREGATE']
    time_delta = (current_app.config['NUMBER_OF_DAYS_FOR_FARSIGHT_TIME_FILTER']
                  if aggr else None)

    try:
        for x in observables:
            mapping = Mapping.for_(x)

            if mapping:
                lookup_data = client.lookup(x, time_delta)
                if lookup_data:
                    g.sightings.extend(
                        mapping.extract_sightings(lookup_data, limit, aggr)
                    )
    except KeyError:
        g.errors = [{
            'type': 'fatal',
            'code': 'key error',
            'message': 'The data structure of Farsight DNSDB '
                       'has changed. The module is broken.'
        }]

    return jsonify_result()
