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
        """Return an instance of `Mapping` for the specified type."""

        for subcls in all_subclasses(Mapping):
            if subcls.type() == observable['type']:
                return subcls(observable)

        return None

    @classmethod
    @abstractmethod
    def type(cls):
        """Return the observable type that the mapping is able to process."""

    @staticmethod
    @abstractmethod
    def _extract_related(record):
        """
        Extract the list of items an observable is related to
        according to Farsight data record.

        """

    @abstractmethod
    def _resolved_to(self, related):
        """
        Return TR resolved_to relation
        depending on an observable and related types.

        """

    @abstractmethod
    def _description(self, aggr=True):
        """Return description field depending on observable type."""

    def _sighting(self, record, refer_link, description):
        def observed_time():
            start_time = (
                record.get('time_first')
                or record.get('zone_time_first')
                or f'{datetime.now().isoformat(timespec="seconds")}Z'
            )

            end_time = (
                record.get('time_last')
                or record.get('zone_time_last')
                or start_time
            )

            return {'start_time': start_time, 'end_time': end_time}

        def data_source():
            if record.get('time_first'):
                return 'Passive DNS replication'
            elif record.get('zone_time_first'):
                return 'Zone file import'

        result = {
            **CTIM_DEFAULTS,
            'id': f'transient:sighting-{uuid4()}',
            'type': 'sighting',
            'source': 'Farsight DNSDB',
            'title': 'Found in Farsight DNSDB',
            'confidence': 'High',
            'internal': False,
            'count': record['count'],
            'observables': [self.observable],
            'observed_time': observed_time(),
            'description': description,
            'source_uri': refer_link
        }

        sensor = data_source()
        if sensor:
            result['sensor'] = sensor

        return result

    def extract_sightings(
            self, lookup_data, refer_link, limit, aggregate=True
    ):
        # Search result may be missing either time_ or zone_time_ pair
        # but at least one pair of timestamps will always be present.
        if aggregate:
            lookup_data = self.aggregate_data(lookup_data)
        else:
            lookup_data.sort(
                key=lambda r: r.get('time_last') or r.get('zone_time_last'),
                reverse=True
            )
            lookup_data = lookup_data[:limit]

        result = []
        description = self._description(aggregate)
        for record in lookup_data:

            related = (record['related'] if aggregate
                       else self._extract_related(record))

            if related:
                related = sorted(set(related))
                sighting = self._sighting(record, refer_link, description)
                sighting['relations'] = [self._resolved_to(r) for r in related]

                result.append(sighting)

        return result

    def aggregate_data(self, lookup_data):
        """Restructure Farsight response for single sighting mode."""
        count = 0
        related = []

        for record in lookup_data:
            count += record['count']
            related.extend(self._extract_related(record))

        return [{
            'count': count,
            'related': sorted(related)
        }]

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

    RRTYPES = ('A', 'AAAA')

    def _description(self, aggr=True):
        return f'IP addresses that {self.observable["value"]} resolves to'

    def _extract_related(self, record):
        return record['rdata']

    def _resolved_to(self, ip):
        return self.observable_relation(
            RESOLVED_TO,
            source=self.observable,
            related={
                'value': ip,
                'type': 'ipv6' if ':' in ip else 'ip'
            }
        )

    def _sighting(self, record, refer_link, description):
        result = super()._sighting(record, refer_link, description)

        if record.get("bailiwick"):
            # SightingDataTable Object:
            # https://github.com/threatgrid/ctim/blob/master/doc/structures/sighting.md#map3
            result['data'] = {
                'columns': [{'name': 'Bailiwick', 'type': 'string'}],
                'rows': [[record["bailiwick"]]]
            }

        return result

    def extract_sightings(
            self, lookup_data, refer_link, limit, aggregate=True
    ):
        lookup_data = [r for r in lookup_data if r['rrtype'] in self.RRTYPES]
        return super().extract_sightings(
            lookup_data, refer_link, limit, aggregate
        )


class IP(Mapping):
    @classmethod
    def type(cls):
        return 'ip'

    def _description(self, aggr=True):
        return (f'{"Hostnames that have" if aggr else "Hostname that has"}'
                f' resolved to {self.observable["value"]}')

    def _extract_related(self, record):
        return [record['rrname']]

    def _resolved_to(self, domain):
        # Remove trailing dot for compatibility with TR
        domain = domain.rstrip('.')
        return self.observable_relation(
            RESOLVED_TO,
            source={'value': domain, 'type': 'domain'},
            related=self.observable
        )


class IPV6(IP):
    @classmethod
    def type(cls):
        return 'ipv6'
