from lib import chunks
import asyncio
from onto.populator.common import seed_commons, seed_locaciones
from onto.populator.jena_client import JenaClient
from onto.populator.ontology import ontology_graph
from onto.populator.sources.datacite import DataCiteSource
from onto.populator.sources.dummy import DummySource
from onto.populator.sources.fairsharing import FairSharingSource
from onto.populator.sources.re3data import seed_disciplinas, Re3DataSource
import onto.cts as cts
import onto.populator.rdf_types as rdf_types
from lib.no_relational_database import get_database_client
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF
from rdflib.plugins.sparql import prepareQuery
from ror.extractor import insert_on_rdf as ror_insert_on_rdf

def walk_dummy(gg: Graph):
    source = DummySource(gg)
    source.process()

def walk_datacite(gg: Graph):
    database = get_database_client()

    source = DataCiteSource(gg)

    col_datacite = database['datacite']
    skip_count = 0
    limit_count = 0
    instances = col_datacite.find({}).sort({'_id': -1}).skip(skip_count).limit(limit_count)
    total = col_datacite.count_documents({})
    for idx, r_info in enumerate(instances):
        source.process(r_info)
        if idx % 20 == 0:
            print("ready %s out of %s" % (idx, total))


def walk_fairsharing(gg: Graph):
    database = get_database_client()

    source = FairSharingSource(gg)

    col_subjects = database['fs_subjects']
    subjects = col_subjects.find({}).sort({'_id': -1})
    source.process_subjects(list(subjects))

    col_orgs = database['fs_orgs']
    orgs = col_orgs.find({}).sort({'_id': -1})
    source.process_orgs(list(orgs))

    col_licence = database['fs_licence']
    licences = col_licence.find({}).sort({'_id': -1})
    source.process_licencia(list(licences))

    col_keyword = database['fs_keyword']
    keywords = col_keyword.find({}).sort({'_id': -1})
    source.process_keywords(list(keywords))

    col_registry = database['fs_registry']
    skip_count = 0
    limit_count = 10
    instances = col_registry.find({}).sort({'_id': -1}).skip(skip_count).limit(limit_count)
    total = col_registry.count_documents({})
    for idx, r_info in enumerate(instances):
        source.process_registry(r_info)
        if idx % 20 == 0:
            print("ready %s out of %s" % (idx, total))


def walk_re3data(g_repos: Graph):
    database = get_database_client()
    raw_drepo_collection = database['raw_drepo_2']
    skip_count = 0
    limit_count = 0
    instances = raw_drepo_collection.find({}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    # instances_count = raw_drepo_collection.count_documents({})

    source = Re3DataSource(g_repos)
    repository_infos = source.refine_iterator(instances)
    total = len(repository_infos)
    counter = 0
    for r_info in repository_infos:
        source.process(r_info)
        counter += 1
        if counter % 20 == 0:
            print("ready %s out of %s" % (counter, total))


def refine_and_insert_on_rdf():
    # g = Graph(store="BerkeleyDB")
    # g.open("/some/folder/location")
    # g.close()
    # g.parse("....")
    # (g_criterios, ) = seed_criterios()
    # (g_disciplinas, ) = seed_disciplinas()
    # g_commons = Graph()
    # g_commons.bind('', rdf_types.my_ns)
    # seed_commons(g_commons)
    # g_locaciones = Graph()
    # g_locaciones.bind('', rdf_types.my_ns)
    # seed_locaciones(g_locaciones)

    g_repos = Graph()
    g_repos.bind('', rdf_types.my_ns)
    walk_dummy(g_repos)
    # walk_re3data(g_repos)
    # walk_fairsharing(g_repos)
    # walk_datacite(g_repos)

    return (g_repos,
            # g_commons, g_criterios, g_disciplinas, g_locaciones
    )


def seed_criterios():
    g = Graph()
    g.bind('', rdf_types.principles_ns)

    # ToDo: Tengo que declarar al menos todas las certificaciones (no "other") de re3data y datacite como criterios de calidad
    # session.add_all([
    #     Certificacion(
    #         id=x['id'],
    #         nombre=x['name'],
    #     ) for x in CERTIFICACIONES
    # ])

    for (target_id, name, url) in cts.criterios_de_calidad:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))

    for (target_criterio_id, criterios_extends_to, criterios_considered) in cts.criterio_de_calidad_extiende_de:
        target_criterio = rdf_types.CriterioDeCalidad.child_uri_ref(target_criterio_id)
        g.set((target_criterio, RDF.type, rdf_types.CriterioDeCalidad))
        for criterio_extends_to_id in criterios_extends_to:
            criterio_extends_to = rdf_types.CriterioDeCalidad.child_uri_ref(criterio_extends_to_id)
            g.set((criterio_extends_to, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target_criterio, rdf_types.extiende_de_criterio, criterio_extends_to))

        for criterio_considered_id in criterios_considered:
            criterio_considered = rdf_types.CriterioDeCalidad.child_uri_ref(criterio_considered_id)
            g.set((criterio_considered, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target_criterio, rdf_types.considera_criterio, criterio_considered))

    # ToDo: same_individuals

    trust = URIRef("%s/trust" % (rdf_types.CriterioDeCalidad.toPython(),), rdf_types.principles_ns)
    # ToDo: Map related_with_funcionalidad
    for (target_id, category, description, related_with_funcionalidad) in cts.metricas_trust:
        target = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, trust))

        grupo_de_criterio = URIRef("%s/%s" % (rdf_types.GrupoDeCriterio.toPython(), category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    plan_s = URIRef("%s/plan_s" % (rdf_types.CriterioDeCalidad.toPython(), ), rdf_types.principles_ns)
    # ToDo: Map importance to model
    for (target_id, _, description, importance, related_with_funcionalidad) in cts.metricas_plan_s:
        target = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, plan_s))

    cts_2022 = URIRef("%s/cts_2022" % (rdf_types.CriterioDeCalidad.toPython(), ), rdf_types.principles_ns)
    for (target_id, category, name, description) in cts.metricas_cts_2022:
        target = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal("%s - %s" % (name, description))))
        g.set((target, rdf_types.extiende_de_criterio, cts_2022))

        grupo_de_criterio = URIRef("%s/%s" % (rdf_types.GrupoDeCriterio.toPython(), category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    criterio_de_calidad_coar = URIRef("%s/coar_v1" % (rdf_types.CriterioDeCalidad.toPython(), ), rdf_types.principles_ns)
    # ToDo: Map importance to model
    for (target_id, category, description, importance, related_with_criterios) in cts.metricas_coar:
        target = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, criterio_de_calidad_coar))

        grupo_de_criterio = URIRef("%s/%s" % (rdf_types.GrupoDeCriterio.toPython(), category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    fair = URIRef("%s/fair" % (rdf_types.CriterioDeCalidad.toPython(),), rdf_types.principles_ns)
    # for (target_id, _) in cts.metricas_fair:
    #     # ToDo: Tengo que relacionar con (same as) con https://w3id.org/fair/principles/terms/ de https://peta-pico.github.io/FAIR-nanopubs/principles/ontology.xml
    #     pass
    for (target_id, _) in cts.fair_maturity_models:
        target = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.extiende_de_criterio, fair))
    rda_fair_maturity_model = URIRef("%s/rda_fair_maturity_model" % (rdf_types.CriterioDeCalidad.toPython(),), rdf_types.principles_ns)
    fsf_fair_maturity_model = URIRef("%s/fsf_fair_maturity_model" % (rdf_types.CriterioDeCalidad.toPython(),), rdf_types.principles_ns)
    # ToDo: Hacer el DSM
    # dsm_fair_maturity_model = URIRef("%s/dsm_fair_maturity_model" % (rdf_types.CriterioDeCalidad.toPython(),), rdf_types.principles_ns)
    for (parent_maturity_model, statements) in [
        (rda_fair_maturity_model, cts.rda_fair_maturity_model_statements),
        (fsf_fair_maturity_model, cts.fsf_fair_maturity_model_statements),
    ]:
        # ToDo: Map metadata_or_data?
        for statement in statements:
            if len(statement) == 5:
                (parent_id, target_id, metadata_or_data, description, importance) = statement
            elif len(statement) == 6:
                (parent_id, target_id, metadata_or_data, name, description, importance) = statement
                description = "%s - %s" % (name, description)
            else:
                raise Exception()
            target = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), target_id,), rdf_types.principles_ns)
            g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
            parent = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), parent_id,), rdf_types.principles_ns)
            g.set((parent, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
            g.set((target, rdf_types.extiende_de_criterio, parent))
            g.set((target, rdf_types.extiende_de_criterio, parent_maturity_model))

    posi = URIRef("%s/posi" % (rdf_types.CriterioDeCalidad.toPython(), ), rdf_types.principles_ns)
    for (target_id, category, description, importance, parents) in cts.metricas_posi:
        target = URIRef("%s/%s" % (rdf_types.CriterioDeCalidad.toPython(), target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))

        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio
        grupo_de_criterio = URIRef("%s/%s" % (rdf_types.GrupoDeCriterio.toPython(), category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))

        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, posi))

    return (g,)


def serialize_file():
    g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones = refine_and_insert_on_rdf()

    orgs_types_literals_query = prepareQuery("""
    SELECT DISTINCT ?o ?t ?l
    WHERE {
      ?i rdf:type :id_de_organizacion .
      ?i :id_de_organizacion_tiene_tipo ?t .
      ?i :id_de_organizacion_tiene_literal ?l .
      ?i :id_de_organizacion_tiene_organizacion ?o
    }""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'})
    orgs_types_literals = {"%s:%s" % (tt, ll.value) for (_, tt, ll) in g_repos.query(orgs_types_literals_query)}

    g_orgs = ror_insert_on_rdf(orgs_types_literals)
    g_repos.serialize(destination='../owl/repositorios.xml', format="xml")
    g_criterios.serialize(destination='../owl/criterios.xml', format="xml")
    g_disciplinas.serialize(destination='../owl/disciplinas.xml', format="xml")
    g_commons.serialize(destination='../owl/commons.xml', format="xml")
    g_locaciones.serialize(destination='../owl/localizaciones.xml', format="xml")
    g_orgs.serialize(destination='../owl/organizaciones.xml', format="xml")


async def serialize_jena():
    g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones = refine_and_insert_on_rdf()
    gg = Graph()
    gg.bind('', rdf_types.my_ns)
    gg += g_commons
    gg += g_locaciones
    gg += g_criterios
    gg += g_disciplinas
    gg += g_repos

    orgs_types_literals_query = prepareQuery("""
    SELECT DISTINCT ?o ?t ?l
    WHERE {
      ?i rdf:type :id_de_organizacion .
      ?i :id_de_organizacion_tiene_tipo ?t .
      ?i :id_de_organizacion_tiene_literal ?l .
      ?i :id_de_organizacion_tiene_organizacion ?o
    }""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'})
    orgs_types_literals = {"%s:%s" % (tt, ll.value) for (_, tt, ll) in gg.query(orgs_types_literals_query)}
    # g_orgs = ror_insert_on_rdf(orgs_types_literals)
    # gg += g_orgs

    items_query = prepareQuery("""
        SELECT DISTINCT ?s ?p ?o
        WHERE {
          ?s ?p ?o
        } ORDER BY DESC(?s) DESC(?p) DESC(?o)""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'})
    items_generator = gg.query(items_query)
    items_count = gg.query(prepareQuery("""
        SELECT (COUNT(DISTINCT *) AS ?count)
        WHERE {
            ?s ?p ?o .
        }""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'}))
    items_count = items_count.result[0][0].value
    CHUNKS_SIZE = 80
    chunk_generator = chunks(iter(items_generator), CHUNKS_SIZE)
    async with JenaClient('dataservice', {'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'}) as client:
        for (idx, ch) in enumerate(chunk_generator):
            await client.insert_many(ch)
            if (idx + 1) % 10 == 0:
                print("%s out of %s" % (CHUNKS_SIZE * (idx + 1), items_count))


async def serialize_schema_jena():
    schema_items_query = prepareQuery("""
        SELECT DISTINCT ?s ?p ?o
        WHERE {
          ?s ?p ?o
        } ORDER BY DESC(?s) DESC(?p) DESC(?o)""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'})
    schema_items_generator = ontology_graph.query(schema_items_query)
    schema_items_count = ontology_graph.query(prepareQuery("""
        SELECT (COUNT(DISTINCT *) AS ?count)
        WHERE {
            ?s ?p ?o .
        }""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'}))
    schema_items_count = schema_items_count.result[0][0].value
    CHUNKS_SIZE = 80
    schema_chunk_generator = chunks(iter(schema_items_generator), CHUNKS_SIZE)
    async with JenaClient('dataservice', {'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'}) as client:
        for (idx, ch) in enumerate(schema_chunk_generator):
            await client.insert_many(ch)
            if (idx + 1) % 10 == 0:
                print("%s out of %s" % (CHUNKS_SIZE * (idx + 1), schema_items_count))


if __name__ == '__main__':
    # serialize_file()
    asyncio.run(serialize_schema_jena())
    # asyncio.run(serialize_jena())
