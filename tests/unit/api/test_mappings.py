import json
from collections import namedtuple

from pytest import fixture

from api.mappings import (
    Domain, Mapping,
    IP, IPV6
)


def input_sets():
    TestData = namedtuple('TestData', 'file mapping')
    yield TestData('domain.json',
                   Domain({'type': 'domain', 'value': 'google.com'}))
    yield TestData('ip.json', IP({'type': 'ip', 'value': '127.0.0.1'}))
    yield TestData('ipv6.json',
                   IPV6({'type': 'ipv6',
                         'value': '2001:0db8:85a3:0000:0000:8a2e:0370:7334'}))


@fixture(scope='module', params=input_sets(), ids=lambda d: d.file)
def input_data(request):
    return request.param


def test_map(input_data):
    with open('tests/unit/data/' + input_data.file) as file:
        data = json.load(file)

        results = getattr(input_data.mapping, 'extract_sightings')(
            data['input'], 100, aggregate=False)

        for record in results:
            assert record.pop('id').startswith('transient:')

        for i, r in enumerate(results):
            for k, v in r['relations'][0].items():
                if v != data['output'][i]['relations'][0][k]:
                    print(v)
                    print(data['output'][i]['relations'][0][k])
                else:
                    print('*')

        assert results == data['output']


def test_limit(input_data):
    with open('tests/unit/data/' + input_data.file) as file:
        data = json.load(file)

        for limit in (0, 1, 2, 25, 100):
            results = getattr(input_data.mapping, 'extract_sightings')(
                data['input'], limit, aggregate=False)

            assert len(results) <= limit


def test_mapping_for_():
    assert isinstance(Mapping.for_({'type': 'domain'}), Domain)
    assert isinstance(Mapping.for_({'type': 'ip'}), IP)
    assert isinstance(Mapping.for_({'type': 'ipv6'}), IPV6)
    assert Mapping.for_({'type': 'whatever'}) is None
