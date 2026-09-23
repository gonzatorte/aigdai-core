from rdflib import URIRef, Literal
from rdflib.namespace import OWL, XSD
import settings
import typing
import re
import calendar
import datetime

from onto.populator.ontology import onto_elements


def owl_all_different(g, instances):
    for (idx, instance1) in enumerate(instances):
        for instance2 in instances[idx+1:]:
            g.add((instance1, OWL.differentFrom, instance2))


def reason_on_memory():
    # g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones = refine_and_insert_on_rdf()
    # g_orgs = insert_on_rdf()
    import owlready2 as ow

    ow.JAVA_EXE = settings.JAVA_EXE_PATH
    ow.onto_path.append('../owl/')

    # from io import BytesIO
    # my_str_as_bytes = str.encode(my_str)  # convert to binary
    # fobj = BytesIO(my_str_as_bytes)
    # abox = ow.get_ontology("some-random-path").load(fileobj=fobj)

    tbox = ow.get_ontology('file://../owl/aigdai-tbox.owl').load(only_local=True)

    for data_file_path in [
        'repositorios.xml',
        'criterios.xml',
        'disciplinas.xml',
        'commons.xml',
        'localizaciones.xml',
        'organizaciones.xml',
    ]:
        # ow.get_ontology('file://%s' % (data_file_path,)).load(only_local=True)
        # tbox.imported_ontologies.append(ow.get_ontology('file://../owl/%s' % (data_file_path,)))
        tbox.imported_ontologies.append(ow.get_ontology('file:///home/gonzalo/workspace/propio/AIGDAI/aigdai-core/onto/owl/%s' % (data_file_path,)))
        # tbox.imported_ontologies.append('file://%s' % (data_file_path,))

    ow.sync_reasoner([tbox], ignore_unsupported_datatypes=True, infer_property_values=True)
    # ow.sync_reasoner_pellet([tbox], infer_data_property_values=True, infer_property_values=True, debug=2)
    # with tbox:
    #     ow.sync_reasoner()

    if len(list(ow.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')

    print(list(tbox.individuals()))
    # print(list(tbox.graph.triples((None, None, None))))


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
    # Cotas (_desde, _hasta) en xsd:dateTime de una fecha de granularidad variable (YYYY, YYYY-MM, YYYY-MM-DD)
    # o de un instante. Las fechas sin zona horaria se interpretan en UTC; un datetime sin zona, en hora local.
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


if __name__ == '__main__':
    reason_on_memory()
