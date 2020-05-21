from functools import partial

from flask import Blueprint, current_app

from api.client import FarsightClient
from api.mappings import Mapping
from api.mappings_aggr import Mapping as MappingAggr
from api.schemas import ObservableSchema
from api.utils import get_json, jsonify_data, get_key, format_docs

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
    data = {}
    sightings = []

    limit = current_app.config['CTR_ENTITIES_LIMIT']
    aggr = current_app.config['AGGREGATE']

    for x in observables:
        mapping = (MappingAggr if aggr else Mapping).for_(x)

        if mapping:
            lookup_data = client.lookup(x)
            sightings.extend(mapping.extract_sightings(lookup_data, limit))

    if sightings:
        data['sightings'] = format_docs(sightings)

    return jsonify_data(data)
