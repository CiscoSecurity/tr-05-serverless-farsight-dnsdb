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

    def _sighting(self, lookup_data):
        return {
            **CTIM_DEFAULTS,
            'id': f'transient:{uuid4()}',
            'type': 'sighting',
            'source': 'Farsight DNSDB',
            'title': 'Found in Farsight DNSDB',
            'confidence': 'High',
            'internal': False,
            'count': sum(r['count'] for r in lookup_data),
            'observables': [self.observable],
            'observed_time': {
                'start_time':
                    f'{datetime.now().isoformat(timespec="seconds")}Z'
            },
        }

    def extract_sightings(self, lookup_data, limit):
        # Search result may be missing either time_ or zone_time_ pair
        # but at least one pair of timestamps will always be present.
        lookup_data.sort(
            key=lambda r: r.get('time_last') or r.get('zone_time_last'),
            reverse=True
        )

        lookup_data = lookup_data[:limit]
        return [self._sighting(lookup_data)]

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

    def resolved_to(self, ip, rrtype):
        return self.observable_relation(
            RESOLVED_TO,
            source=self.observable,
            related={
                'value': ip,
                'type': self.RRTYPES[rrtype]
            }
        )

    def _sighting(self, lookup_data):
        result = super()._sighting(lookup_data)

        added_ips = set()
        relations = []

        for record in lookup_data:
            for ip in record['rdata']:
                if ip not in added_ips:
                    added_ips.add(ip)
                    relations.append(self.resolved_to(ip, record['rrtype']))

        if relations:
            result['relations'] = relations

        return result

    def extract_sightings(self, lookup_data, limit):
        lookup_data = [r for r in lookup_data if r['rrtype'] in self.RRTYPES]
        return super().extract_sightings(lookup_data, limit)


class IP(Mapping):
    @classmethod
    def type(cls):
        return 'ip'

    def resolved_to(self, domain):
        return self.observable_relation(
            RESOLVED_TO,
            source={'value': domain, 'type': 'domain'},
            related=self.observable
        )

    def _sighting(self, lookup_data):
        result = super()._sighting(lookup_data)

        added_domains = set()
        relations = []

        for record in lookup_data:
            # Remove trailing dot for compatibility with TR
            domain = record['rrname'].rstrip('.')

            if domain not in added_domains:
                added_domains.add(domain)
                relations.append(self.resolved_to(domain))

        if relations:
            result['relations'] = relations

        return result


class IPV6(IP):
    @classmethod
    def type(cls):
        return 'ipv6'