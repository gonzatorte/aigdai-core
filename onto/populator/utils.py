from rdflib import BNode, URIRef, Literal
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, XSD
import typing
import re
import calendar
import datetime

from onto.populator.ontology import onto_elements


def owl_all_different(g, instances):
    # A single owl:AllDifferent per group instead of an owl:differentFrom per pair, which grows with the square of
    # the group. It uses owl:distinctMembers (OWL 1) and not owl:members (OWL 2): the Jena rules (distinct2) only
    # recognize the former, and the OWL API and owlready2 read both. HermiT and Jena expand it to pairs internally.
    if len(instances) < 2:
        return
    all_different = BNode()
    members = BNode()
    Collection(g, members, list(instances))
    g.add((all_different, RDF.type, OWL.AllDifferent))
    g.add((all_different, OWL.distinctMembers, members))


T = typing.TypeVar('T')
def find_or_fail(ll: typing.List[T], searcher: typing.Callable[[T], bool]):
    try:
        return next(filter(searcher, ll))
    except StopIteration:
        raise KeyError()


def buckets(n: int, ll: typing.Iterator[typing.Any]):
    bulk = []
    for xx in ll:
        bulk.append(xx)


class ParentURIRef(URIRef):
    local_uri = ""
    # def __init__(self, onto):
    #     self.onto = onto

    def child_uri_ref(self, idd: str):
        pass
        # return URIRef("%s/%s" % (self.toPython(), idd), self.onto.base_iri)

    def get_local_uri(self):
        pass

AUTO_ID_COUNTER = 0

def get_ref_from_ontology(name: str) -> ParentURIRef:
    (node, onto) = onto_elements[name]
    uri_ref = URIRef(name, onto.base_iri)
    def child_uri_ref(idd: typing.Optional[str | int]):
        if idd is None:
            global AUTO_ID_COUNTER
            AUTO_ID_COUNTER += 1
            idd = AUTO_ID_COUNTER
        if isinstance(idd, int):
            idd = str(idd)
        idd_n = re.sub('[ |@:]', '_', idd).lower()
        uu = URIRef("%s/%s" % (uri_ref.toPython(), idd_n), onto.base_iri)
        uu.local_uri = idd_n
        return uu
    uri_ref.child_uri_ref = child_uri_ref
    return typing.cast(ParentURIRef, uri_ref)


def get_datatype_from_ontology(name: str) -> ParentURIRef:
    return URIRef(name, 'http://aigdai.tbox.owl/')


def gross_date_bounds(value: str | datetime.datetime) -> typing.Tuple[Literal, Literal]:
    # Bounds (_desde, _hasta) in xsd:dateTime of a date with variable granularity (YYYY, YYYY-MM, YYYY-MM-DD)
    # or of an instant. Dates without a time zone are interpreted as UTC; a datetime without one, as local time.
    if isinstance(value, datetime.datetime):
        instant = value.astimezone(datetime.timezone.utc)
        return (Literal(instant, datatype=XSD.dateTime), Literal(instant, datatype=XSD.dateTime))
    if 'T' in value:
        instant = datetime.datetime.fromisoformat(value)
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=datetime.timezone.utc)
        return (Literal(instant, datatype=XSD.dateTime), Literal(instant, datatype=XSD.dateTime))
    parts = [int(x) for x in value.split('-')]
    year = parts[0]
    (month_desde, month_hasta) = (parts[1], parts[1]) if len(parts) > 1 else (1, 12)
    day_desde = parts[2] if len(parts) > 2 else 1
    day_hasta = parts[2] if len(parts) > 2 else calendar.monthrange(year, month_hasta)[1]
    desde = datetime.datetime(year, month_desde, day_desde, tzinfo=datetime.timezone.utc)
    hasta = datetime.datetime(year, month_hasta, day_hasta, 23, 59, 59, tzinfo=datetime.timezone.utc)
    return (Literal(desde, datatype=XSD.dateTime), Literal(hasta, datatype=XSD.dateTime))

