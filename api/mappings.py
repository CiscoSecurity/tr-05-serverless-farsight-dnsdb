from abc import ABCMeta, abstractmethod
from datetime import datetime
from uuid import uuid4

from api.utils import all_subclasses

CTIM_DEFAULTS = {
    'schema_version': '1.0.17',
}

RESOLVED_TO = 'Resolved_To'


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
        def observed_time():
            start = {
                'start_time':
                    record.get('time_first') or record['zone_time_first']
            }

            end = record.get('time_last') or record.get('zone_time_last')
            end = {'end_time': end} if end else {}

            return {**start, **end}

        return {
            **CTIM_DEFAULTS,
            'id': f'transient:{uuid4()}',
            'type': 'sighting',
            'source': 'Farsight DNSDB',
            'title': 'Found in Farsight DNSDB',
            'confidence': 'High',
            'internal': False,
            'count': record['count'],
            'observables': [self.observable],
            'observed_time': observed_time(),
        }

    @abstractmethod
    def extract_related(self, record):
        pass

    def aggregate_data(self, lookup_data):
        count = 0
        related = set()

        for record in lookup_data:
            count += record['count']
            related.update(set(self.extract_related(record)))

        return [{
            'count': count,
            'related': related,
            'time_first': f'{datetime.now().isoformat(timespec="seconds")}Z'
        }]

    def extract_sightings(self, lookup_data, limit, aggregate=True):
        # Search result may be missing either time_ or zone_time_ pair
        # but at least one pair of timestamps will always be present.
        lookup_data.sort(
            key=lambda r: r.get('time_last') or r.get('zone_time_last'),
            reverse=True
        )

        lookup_data = lookup_data[:limit]

        if aggregate:
            lookup_data = self.aggregate_data(lookup_data)

        result = []
        for r in lookup_data:
            sighting = self._sighting(r)

            sighting['relations'] = [
                self.resolved_to(related)
                for related in
                (r['related'] if aggregate else self.extract_related(r))
            ]
            result.append(sighting)

        return result

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

    RRTYPES = {
        'A': 'ip',
        'AAAA': 'ipv6',
    }

    def resolved_to(self, ip):
        return self.observable_relation(
            RESOLVED_TO,
            source=self.observable,
            related={
                'value': ip,
                'type': 'ipv6' if ':' in ip else 'ip'
            }
        )

    def _sighting(self, record):
        result = super()._sighting(record)

        if record.get("bailiwick"):
            # SightingDataTable Object:
            # https://github.com/threatgrid/ctim/blob/master/doc/structures/sighting.md#map3
            result['data'] = {
                'columns': [{'name': 'Bailiwick', 'type': 'string'}],
                'rows': [[record["bailiwick"]]]
            }

        return result

    def extract_related(self, record):
        return record['rdata']

    def extract_sightings(self, lookup_data, limit, aggregate=True):
        lookup_data = [r for r in lookup_data if r['rrtype'] in self.RRTYPES]
        return super().extract_sightings(lookup_data, limit, aggregate)


class IP(Mapping):
    @classmethod
    def type(cls):
        return 'ip'

    def resolved_to(self, domain):
        # Remove trailing dot for compatibility with TR
        domain = domain.rstrip('.')
        return self.observable_relation(
            RESOLVED_TO,
            source={'value': domain, 'type': 'domain'},
            related=self.observable
        )

    def extract_related(self, record):
        return [record['rrname']]


class IPV6(IP):
    @classmethod
    def type(cls):
        return 'ipv6'
