from abc import ABCMeta, abstractmethod
from uuid import uuid4

from api.utils import all_subclasses

NONE = 'None'
INFO = 'Info'
LOW = 'Low'
MEDIUM = 'Medium'
HIGH = 'High'
UNKNOWN = 'Unknown'
CTIM_DEFAULTS = {
    'schema_version': '1.0.16',
}


class Mapping(metaclass=ABCMeta):

    def __init__(self, observable):
        self.observable = observable

    @classmethod
    def for_(cls, observable):
        """Returns an instance of `Mapping` for the specified type."""

        for subcls in all_subclasses(Mapping):
            if subcls.type() == observable['type']:
                return subcls(observable)

        return None

    @classmethod
    @abstractmethod
    def type(cls):
        """Returns the observable type that the mapping is able to process."""

    def _sighting(self, record):
        return {
            **CTIM_DEFAULTS,
            'id': f'transient:{uuid4()}',
            'type': 'sighting',
            # ToDo: confirm
            'source': 'Farsight DNSDB',
            'title': 'Found in Farsight DNSDB',
            'confidence': HIGH,
            'internal': True,
            # ___________________
            'source_uri': '',  # ToDO: find out

            'count': record['count'],
            'observables': [self.observable],
            'observed_time': {
                'start_time': record.get('time_first') or record.get('zone_time_first'),  # ToDo: confirm
                'end_time':  record.get('time_last') or record.get('zone_time_last'),  # ToDo: confirm
            },
        }


    def extract_sightings(self, lookup_data, limit):
        lookup_data.sort(key=lambda r: r.get('time_first') or r.get('zone_time_first'), reverse=True) # ToDo: confirm
        lookup_data = lookup_data[:limit]

        return [self._sighting(r) for r in lookup_data]

    @staticmethod
    def observable_relation(relation_type, source, related):
        return {
            "origin": "Farsight DNSDB Enrichment Module",
            "relation": relation_type,
            "source": source,
            "related": related
        }


class Domain(Mapping):
    @classmethod
    def type(cls):
        return 'domain'

    def resolved_to(self, ip):
        return self.observable_relation(
            'Resolved_To',
            source=self.observable,
            related={'value': ip,
                     'type': 'ipv6' if ':' in ip else 'ip'}
        )

    def _sighting(self, record):
        result = super()._sighting(record)
        result['details'] = f'Bailiwick: {record["bailiwick"]}'

        if record['rdata']:
            result['relations'] = [
                self.resolved_to(ip) for ip in record['rdata']
            ]

        return result

    def extract_sightings(self, lookup_data, limit):
        lookup_data = [r for r in lookup_data if r['rrtype'] in ('A', 'AAAA')]
        return super().extract_sightings(lookup_data, limit)


class IP(Mapping):
    @classmethod
    def type(cls):
        return 'ip'

    def resolved_to(self, domain):
        return self.observable_relation(
            'Resolved_To',
            source=domain,
            related=self.observable
        )

    def _sighting(self, record):
        result = super()._sighting(record)
        result['relations'] = [self.resolved_to(record['rrname'])]
        return result


class IPV6(IP):
    @classmethod
    def type(cls):
        return 'ipv6'
