import argparse
import re
import contextlib
import itertools
import shutil
import tempfile
import logging
import time
from collections import defaultdict
from onto.populator.common import seed_commons, seed_locaciones, certification_ref
from onto.populator.ontology import ontology_graph
from onto.populator.jena_reasoner import materialize
from onto.populator.sources.datacite import DataCiteSource
from onto.populator.sources.doi import DoiSource
from onto.populator.sources.dummy import DummySource
from onto.populator.sources.fairsharing import FairSharingSource
from onto.populator.sources.re3data import seed_disciplinas, Re3DataSource
import onto.cts as cts
import onto.populator.rdf_types as rdf_types
from lib.no_relational_database import get_database_client
from rdflib import Graph, Literal, URIRef
from onto.populator.utils import owl_all_different
from rdflib.namespace import RDF, OWL, XSD
from rdflib.plugins.sparql import prepareQuery
from ror.extractor import insert_on_rdf as ror_insert_on_rdf

ALL_SOURCES = ('re3data', 'fairsharing', 'datacite', 'doi', 'dummy')
DEFAULT_SOURCES = ('re3data', 'fairsharing', 'datacite', 'doi')
ALL_SEEDS = ('commons', 'locaciones')
DEFAULT_SEEDS = ()
DEFAULT_REDUCED_LIMIT = 500

logger = logging.getLogger('populate')


@contextlib.contextmanager
def stage(name: str, graph: Graph = None):
    # Logs how long a stage takes and, if a graph is given, how many triples it adds
    before = len(graph) if graph is not None else None
    logger.info('start %s', name)
    started = time.perf_counter()
    yield
    elapsed = time.perf_counter() - started
    if graph is not None:
        logger.info('end %s: %.1f s, +%s triples (%s total)', name, elapsed, len(graph) - before, len(graph))
    else:
        logger.info('end %s: %.1f s', name, elapsed)


def walk_dummy(gg: Graph):
    source = DummySource(gg)
    source.process()

def walk_datacite(gg: Graph, reduced: bool=False, skip: int=None, limit: int=None):
    database = get_database_client()

    source = DataCiteSource(gg)
    source.mappings()

    col_datacite = database['datacite']
    skip_count = skip if skip is not None else 0
    limit_count = limit if limit is not None else (DEFAULT_REDUCED_LIMIT if reduced else 0)
    instances = col_datacite.find({}).sort({'_id': -1}).skip(skip_count).limit(limit_count)
    total = col_datacite.count_documents({})
    for idx, r_info in enumerate(instances):
        source.process(r_info)
        if idx % 20 == 0:
            print("ready %s out of %s" % (idx, total))


def walk_doi(gg: Graph, reduced: bool=False, skip: int=None, limit: int=None):
    # The metadata fetched by DOI is stored by each extractor next to the record that states the DOI
    database = get_database_client()
    source = DoiSource(gg)
    skip_count = skip if skip is not None else 0
    limit_count = limit if limit is not None else (DEFAULT_REDUCED_LIMIT if reduced else 0)
    # (collection, query, field with the metadata): the re3data DOIs that DataCite lists, and the FAIRsharing databases
    for (collection_name, query, field) in (
        ('datacite', {'doi_metadata.attributes': {'$exists': True}}, 'doi_metadata'),
        ('fs_registry', {'registry': 'Database', 'doi_data.attributes': {'$exists': True}}, 'doi_data'),
    ):
        collection = database[collection_name]
        instances = collection.find(query, {field: 1}).sort({'_id': -1}).skip(skip_count).limit(limit_count)
        total = collection.count_documents(query)
        for idx, r_info in enumerate(instances):
            source.process(r_info[field])
            if idx % 20 == 0:
                print("ready %s out of %s DOIs of %s" % (idx, total, collection_name))


def walk_fairsharing(gg: Graph, reduced: bool=False, skip: int=None, limit: int=None):
    database = get_database_client()

    col_registry = database['fs_registry']
    records = {r['id']: (r.get('registry'), r.get('doi')) for r in col_registry.find({}, {'id': 1, 'registry': 1, 'doi': 1})}
    source = FairSharingSource(gg, records)

    if not reduced:
        col_subjects = database['fs_subjects']
        subjects = col_subjects.find({}).sort({'_id': -1})
        source.process_subjects(list(subjects))

    # In pymongo limit(0) means no limit; a negative limit returns a single batch (one document with -1)
    skip_org_count = skip if skip is not None else (100 if reduced else 0)
    limit_org_count = limit if limit is not None else (500 if reduced else 0)
    col_orgs = database['fs_orgs']
    orgs = col_orgs.find({}).sort({'_id': -1}).skip(skip_org_count).limit(limit_org_count)
    org_list = list(orgs)
    print("loading", len(org_list), "orgs")
    source.process_orgs(org_list)

    if not reduced:
        col_licence = database['fs_licence']
        licences = col_licence.find({}).sort({'_id': -1})
        source.process_licencia(list(licences))

    if not reduced:
        col_keyword = database['fs_keyword']
        keywords = col_keyword.find({}).sort({'_id': -1})
        source.process_keywords(list(keywords))

    col_registry = database['fs_registry']
    skip_count = skip if skip is not None else (1000 if reduced else 0)
    limit_count = limit if limit is not None else (200 if reduced else 0)
    instances = col_registry.find({}).sort({'_id': -1}).skip(skip_count).limit(limit_count)
    total = col_registry.count_documents({})
    for idx, r_info in enumerate(instances):
        source.process_registry(r_info, reduced)
        if idx % 20 == 0:
            print("ready %s out of %s" % (idx, total))


def walk_re3data(g_repos: Graph, reduced: bool=False, skip: int=None, limit: int=None):
    database = get_database_client()
    raw_drepo_collection = database['raw_drepo_2']
    skip_count = skip if skip is not None else 0
    limit_count = limit if limit is not None else (500 if reduced else 0)
    instances = raw_drepo_collection.find({}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    # instances_count = raw_drepo_collection.count_documents({})

    source = Re3DataSource(g_repos)
    repository_infos = source.refine_iterator(instances)
    total = len(repository_infos)
    counter = 0
    for r_info in repository_infos:
        source.process(r_info, reduced)
        counter += 1
        if counter % 20 == 0:
            print("ready %s out of %s" % (counter, total))


def reconcile_repositories(g_repos: Graph):
    # Two identifiers with the same catalog and literal identify the same repository (the HasKey of
    # id_de_repositorio). The repositories they are about are declared the same with owl:sameAs. This also
    # covers a single identifier node about two repositories, which happens when two sources build the same IRI.
    # It groups in Python instead of a SPARQL self-join, which rdflib does not finish on the full graph.
    # ToDo: These owl:sameAs are a workaround, so that the reconciliation is visible in a dataset without
    #  reasoner. There are two cases:
    #  - Two identifier nodes with the same catalog and literal: only the HasKey of id_de_repositorio makes
    #    them equal. owlready2 drops HasKey when it reads the TBox, and ELK and the Jena rules do not implement it.
    #  - One identifier node about two repositories (today, all of them: re3data and the FAIRsharing
    #    cross-references build the same IRI): the functional id_de_repositorio_tiene_repositorio is enough,
    #    and the Jena rules (fp1) would infer it, but with_data runs no reasoner.
    #  With HermiT through OWLAPI, or a Jena reasoner on the dataset, the asserted ones could be removed.
    by_key = defaultdict(set)
    for id_repo in set(g_repos.subjects(rdf_types.id_de_repositorio_tiene_literal, None)):
        for literal in g_repos.objects(id_repo, rdf_types.id_de_repositorio_tiene_literal):
            for catalog in g_repos.objects(id_repo, rdf_types.id_de_repositorio_tiene_catalogo):
                by_key[(catalog, str(literal))].add(id_repo)
    same_ids = set()
    same_repos = set()
    for ids in by_key.values():
        ids = sorted(ids)
        repos = sorted({r for id_repo in ids for r in g_repos.objects(id_repo, rdf_types.id_de_repositorio_tiene_repositorio)})
        same_ids.update(itertools.combinations(ids, 2))
        same_repos.update(itertools.combinations(repos, 2))
    for (id1, id2) in same_ids:
        g_repos.add((id1, OWL.sameAs, id2))
    for (r1, r2) in same_repos:
        g_repos.add((r1, OWL.sameAs, r2))
    largest = max(by_key.items(), key=lambda kv: len(kv[1]), default=(None, ()))
    logger.info('reconciliation: %s owl:sameAs between identifiers, %s between repositories; largest identifier group: %s (%s)',
                len(same_ids), len(same_repos), len(largest[1]), largest[0])


def satisfied_criteria(g_repos: Graph):
    # A repository with a certification application satisfies the certification as a quality criterion. The
    # validity period is ignored on purpose: whether a certification is current is always queried on the
    # application itself. The chain repositorio_satisface_criterio ∘ inv(extiende_de_criterio) of the TBox then
    # carries the satisfaction to the statements of the criterion.
    for aplicacion in set(g_repos.subjects(RDF.type, rdf_types.AplicacionDeCertificacionARepositorio)):
        for repositorio in g_repos.objects(aplicacion, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_repositorio):
            for certificacion in g_repos.objects(aplicacion, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_certificacion):
                g_repos.add((repositorio, rdf_types.repositorio_satisface_criterio, certificacion))


def refine_and_insert_on_rdf(sources=DEFAULT_SOURCES, seeds=DEFAULT_SEEDS, reduced: bool=True, skip: int=None, limit: int=None,
                             reconcile: bool=True):
    with stage('seed criterios'):
        (g_criterios, ) = seed_criterios()
    with stage('seed disciplinas'):
        (g_disciplinas, ) = seed_disciplinas()
    g_commons = Graph()
    g_commons.bind('', rdf_types.my_ns)
    if 'commons' in seeds:
        with stage('seed commons', g_commons):
            seed_commons(g_commons)
    g_locaciones = Graph()
    g_locaciones.bind('', rdf_types.my_ns)
    if 'locaciones' in seeds:
        with stage('seed locaciones', g_locaciones):
            seed_locaciones(g_locaciones)

    g_repos = Graph()
    g_repos.bind('', rdf_types.my_ns)
    if 'dummy' in sources:
        with stage('walk dummy', g_repos):
            walk_dummy(g_repos)
    if 're3data' in sources:
        with stage('walk re3data', g_repos):
            walk_re3data(g_repos, reduced, skip, limit)
    if 'fairsharing' in sources:
        with stage('walk fairsharing', g_repos):
            walk_fairsharing(g_repos, reduced, skip, limit)
    if 'datacite' in sources:
        with stage('walk datacite', g_repos):
            walk_datacite(g_repos, reduced, skip, limit)
    if 'doi' in sources:
        with stage('walk doi', g_repos):
            walk_doi(g_repos, reduced, skip, limit)

    with stage('satisfied criteria', g_repos):
        satisfied_criteria(g_repos)

    # With --dl-reasoner the owl:sameAs come from HermiT instead (see onto/populator/hermit_reasoner.py)
    if reconcile:
        with stage('reconciliation', g_repos):
            reconcile_repositories(g_repos)

    return (
        g_repos,
        g_commons,
        g_criterios,
        g_disciplinas,
        g_locaciones,
    )


def seed_criterios():
    g = Graph()
    g.bind('', rdf_types.principles_ns)

    # ToDo: I have to declare at least all the certifications (not "other") from re3data and datacite as quality criteria
    # session.add_all([
    #     Certificacion(
    #         id=x['id'],
    #         nombre=x['name'],
    #     ) for x in CERTIFICACIONES
    # ])

    for (target_id, name, url) in cts.criterios_de_calidad:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.add((target, RDF.type, rdf_types.CriterioDeCalidad))

    for (target_criterio_id, criterios_extends_to, criterios_considered) in cts.criterio_de_calidad_extiende_de:
        target_criterio = rdf_types.CriterioDeCalidad.child_uri_ref(target_criterio_id)
        g.add((target_criterio, RDF.type, rdf_types.CriterioDeCalidad))
        for criterio_extends_to_id in criterios_extends_to:
            criterio_extends_to = rdf_types.CriterioDeCalidad.child_uri_ref(criterio_extends_to_id)
            g.add((criterio_extends_to, RDF.type, rdf_types.CriterioDeCalidad))
            g.add((target_criterio, rdf_types.extiende_de_criterio, criterio_extends_to))

        for criterio_considered_id in criterios_considered:
            criterio_considered = rdf_types.CriterioDeCalidad.child_uri_ref(criterio_considered_id)
            g.add((criterio_considered, RDF.type, rdf_types.CriterioDeCalidad))
            g.add((target_criterio, rdf_types.considera_criterio, criterio_considered))

    # ToDo: same_individuals

    # The unversioned CoreTrustSeal ('cts') is different from the other certifications but not from its versions,
    # which are different from each other: two groups instead of one (see cts.certificaciones_distintas).
    otras = [certification_ref(cert_id) for cert_id in cts.certificaciones_distintas]
    versiones_cts = [rdf_types.CriterioDeCalidad.child_uri_ref(cert_id) for cert_id in cts.versiones_de_cts]
    cts_sin_version = certification_ref('cts')
    for certificacion in otras + versiones_cts + [cts_sin_version]:
        g.add((certificacion, RDF.type, rdf_types.Certificacion))
    owl_all_different(g, otras + versiones_cts)
    owl_all_different(g, otras + [cts_sin_version])

    trust = rdf_types.CriterioDeCalidad.child_uri_ref('trust')
    # ToDo: Map related_with_funcionalidad
    for (target_id, category, description, related_with_funcionalidad) in cts.metricas_trust:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.add((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.add((target, rdf_types.criterio_tiene_descripcion, Literal(description, datatype=XSD.string)))
        g.add((target, rdf_types.extiende_de_criterio, trust))

        grupo_de_criterio = rdf_types.CriterioDeCalidad.child_uri_ref(category)
        g.add((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: It still has to be stated which criterio_de_calidad has that grupo_de_criterio

    plan_s = rdf_types.CriterioDeCalidad.child_uri_ref("plan_s")
    # ToDo: Map importance to model
    for (target_id, _, description, importance, related_with_funcionalidad) in cts.metricas_plan_s:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.add((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.add((target, rdf_types.criterio_tiene_descripcion, Literal(description, datatype=XSD.string)))
        g.add((target, rdf_types.extiende_de_criterio, plan_s))

    cts_2022 = rdf_types.CriterioDeCalidad.child_uri_ref("cts_2022")
    for (target_id, category, name, description) in cts.metricas_cts_2022:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.add((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.add((target, rdf_types.criterio_tiene_descripcion, Literal("%s - %s" % (name, description), datatype=XSD.string)))
        g.add((target, rdf_types.extiende_de_criterio, cts_2022))

        grupo_de_criterio = rdf_types.GrupoDeCriterio.child_uri_ref(category)
        g.add((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: It still has to be stated which criterio_de_calidad has that grupo_de_criterio

    criterio_de_calidad_coar = rdf_types.CriterioDeCalidad.child_uri_ref("coar_v1")
    # ToDo: Map importance to model
    for (target_id, category, description, importance, related_with_criterios) in cts.metricas_coar:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.add((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.add((target, rdf_types.criterio_tiene_descripcion, Literal(description, datatype=XSD.string)))
        g.add((target, rdf_types.extiende_de_criterio, criterio_de_calidad_coar))

        grupo_de_criterio = rdf_types.GrupoDeCriterio.child_uri_ref(category)
        g.add((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: It still has to be stated which criterio_de_calidad has that grupo_de_criterio

    fair = rdf_types.CriterioDeCalidad.child_uri_ref("fair")
    # for (target_id, _) in cts.metricas_fair:
    #     # ToDo: I have to relate (same as) to https://w3id.org/fair/principles/terms/ from https://peta-pico.github.io/FAIR-nanopubs/principles/ontology.xml
    #     pass
    for (target_id, _) in cts.fair_maturity_models:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.add((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.add((target, rdf_types.extiende_de_criterio, fair))
    rda_fair_maturity_model = rdf_types.CriterioDeCalidad.child_uri_ref("rda_fair_maturity_model")
    fsf_fair_maturity_model = rdf_types.CriterioDeCalidad.child_uri_ref("fsf_fair_maturity_model")
    # ToDo: Build the DSM
    # dsm_fair_maturity_model = rdf_types.CriterioDeCalidad.child_uri_ref("dsm_fair_maturity_model")
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
            target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
            g.add((target, RDF.type, rdf_types.CriterioDeCalidad))
            parent = rdf_types.CriterioDeCalidad.child_uri_ref(parent_id)
            g.add((parent, RDF.type, rdf_types.CriterioDeCalidad))
            g.add((target, rdf_types.criterio_tiene_descripcion, Literal(description, datatype=XSD.string)))
            g.add((target, rdf_types.extiende_de_criterio, parent))
            g.add((target, rdf_types.extiende_de_criterio, parent_maturity_model))

    posi = rdf_types.CriterioDeCalidad.child_uri_ref("posi")
    for (target_id, category, description, importance, parents) in cts.metricas_posi:
        target = rdf_types.CriterioDeCalidad.child_uri_ref(target_id)
        g.add((target, RDF.type, rdf_types.CriterioDeCalidad))

        # ToDo: It still has to be stated which criterio_de_calidad has that grupo_de_criterio
        grupo_de_criterio = rdf_types.GrupoDeCriterio.child_uri_ref(category)
        g.add((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))

        g.add((target, rdf_types.criterio_tiene_descripcion, Literal(description, datatype=XSD.string)))
        g.add((target, rdf_types.extiende_de_criterio, posi))

    return (g,)


def extract_ror_involved_orgs(gg: Graph):
    orgs_types_literals_query = prepareQuery("""
    SELECT DISTINCT ?o ?t ?l
    WHERE {
      ?i rdf:type :id_de_organizacion .
      ?i :id_de_organizacion_tiene_tipo ?t .
      ?i :id_de_organizacion_tiene_literal ?l .
      ?i :id_de_organizacion_tiene_organizacion ?o
    }""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai.tbox.owl/'})
    orgs_types_literals = {"%s:%s" % (tt.replace('http://aigdai.tbox.owl/tipo_de_id_de_organizacion/', '').upper(), ll.value) for (_, tt, ll) in gg.query(orgs_types_literals_query)}
    return ror_insert_on_rdf(orgs_types_literals)


def build_data_graph(**kwargs):
    g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones = refine_and_insert_on_rdf(**kwargs)
    gg = Graph()
    gg.bind('', rdf_types.my_ns)
    with stage('merge graphs', gg):
        gg += g_commons
        gg += g_locaciones
        gg += g_criterios
        gg += g_disciplinas
        gg += g_repos

    with stage('ror organizations', gg):
        g_orgs = extract_ror_involved_orgs(gg)
        gg += g_orgs

    with stage('fairsharing records and levels', gg):
        link_fairsharing_records(gg)
        order_access_levels(gg)
    with stage('licence reconciliation', gg):
        reconcile_licences(gg)
    return gg


def link_fairsharing_records(gg: Graph):
    # Each enumerated value present in the graph is the same as its FAIRsharing record (cts.fairsharing_de_enumerados),
    # so the values that the sources name differently but share a record end up the same through it.
    classes = {
        'esquema_de_metadatos': rdf_types.EsquemaDeMetadatos,
        'esquema_de_id_persistente': rdf_types.EsquemaDeIdPersistente,
        'esquema_de_id_de_autor': rdf_types.EsquemaDeIdDeAutor,
        'protocolo_de_cosecha': rdf_types.ProtocoloDeCosecha,
        'formato_de_sindicacion': rdf_types.FormatoDeSindicacion,
    }
    for (class_key, mapping) in cts.fairsharing_de_enumerados.items():
        for (value, fairsharing_id) in mapping.items():
            if class_key == 'certificacion':
                individual = certification_ref(value)
            else:
                individual = classes[class_key].child_uri_ref(value)
            if (individual, None, None) in gg or (None, None, individual) in gg:
                gg.add((individual, OWL.sameAs, URIRef('https://fairsharing.org/%s' % (fairsharing_id,))))


def reconcile_licences(gg: Graph):
    # Licences with the same URL (lower case, without scheme, "www." or trailing slashes) are the same. FAIRsharing's
    # licences are keyed by their numeric id and declared owl:AllDifferent, so a URL shared by two of them is skipped.
    by_url = defaultdict(set)
    for (licencia, url) in gg.subject_objects(rdf_types.tiene_url_licencia):
        normal = re.sub(r'/+$', '', re.sub(r'^[a-z]+://(www\.)?', '', str(url).strip().lower()))
        if normal:
            by_url[normal].add(licencia)
    same = 0
    for licencias in by_url.values():
        fairsharing = [l for l in licencias if str(l).rsplit('/', 1)[1].isdigit()]
        if len(fairsharing) > 1 or len(licencias) < 2:
            continue
        licencias = sorted(licencias)
        target = fairsharing[0] if fairsharing else licencias[0]
        for licencia in licencias:
            if licencia != target:
                gg.add((licencia, OWL.sameAs, target))
                same += 1
    logger.info('licence reconciliation: %s owl:sameAs', same)


def order_access_levels(gg: Graph):
    # cts.niveles_de_acceso_fairsharing goes from the broadest to the narrowest
    niveles = [rdf_types.NivelDeAcceso.child_uri_ref(n) for n in cts.niveles_de_acceso_fairsharing]
    for (broader, narrower) in zip(niveles, niveles[1:]):
        gg.add((broader, rdf_types.es_acceso_mas_amplio, narrower))


def materialize_property_chains(gg: Graph) -> int:
    # Without --dl-reasoner, the values of the property chains of the TBox (SubObjectPropertyOf with
    # ObjectPropertyChain), which Jena does not apply, are added here until nothing new comes out. With
    # --dl-reasoner HermiT computes them instead (see onto/populator/hermit_reasoner.py). Returns the triples added.
    from onto.populator.hermit_reasoner import property_chains
    chains = property_chains(ontology_graph)
    added = 0
    while True:
        new = set()
        for (prop, members) in chains:
            def step(nodes, member):
                (member_prop, inverse) = member
                out = set()
                for (start, node) in nodes:
                    values = gg.subjects(member_prop, node) if inverse else gg.objects(node, member_prop)
                    out.update((start, value) for value in values)
                return out
            (first_prop, first_inverse) = members[0]
            pairs = {(o, s) if first_inverse else (s, o) for (s, o) in gg.subject_objects(first_prop)}
            for member in members[1:]:
                pairs = step(pairs, member)
            new.update((s, prop, o) for (s, o) in pairs if (s, prop, o) not in gg)
        if not new:
            return added
        for triple in new:
            gg.add(triple)
        added += len(new)


def split_all_different(gg: Graph) -> Graph:
    # Moves the owl:AllDifferent of the graph, with their member lists, to a separate graph that is returned.
    # The Jena rules (distinct2) expand each one to an owl:differentFrom per pair of members, in both directions,
    # which is quadratic in the size of the group.
    different = Graph()
    for node in list(gg.subjects(RDF.type, OWL.AllDifferent)):
        triples = list(gg.triples((node, None, None)))
        for list_node in gg.objects(node, OWL.distinctMembers):
            while list_node is not None and list_node != RDF.nil:
                triples.extend(gg.triples((list_node, None, None)))
                list_node = gg.value(list_node, RDF.rest)
        for triple in triples:
            gg.remove(triple)
            different.add(triple)
    return different


def write_graph(output: str, dl_reasoner: bool = False, different_statements: bool = False, jena: bool = True, **kwargs):
    # Writes to output, as N-Triples, the schema plus the data, to be loaded by hand into a Fuseki dataset with
    # tdb2.tdbloader (see onto/README.md), after materializing the reasoning:
    # - What Jena does not do, on the subgraphs of onto/populator/hermit_reasoner.py: the owl:sameAs between
    #   repositories (shared identifiers) and the values of the property chains. With --dl-reasoner, HermiT, without the
    #   HasKey axioms, with which it does not finish; otherwise, the same rules applied in Python
    #   (reconcile_repositories, which groups by key, and materialize_property_chains), which is much faster.
    # - Everything else: the Jena reasoner (the rules of OWLFBRuleReasoner without the equality ones, see
    #   onto/populator/jena_reasoner.py) on the whole graph plus the schema. With jena=False
    #   (--no-jena) this step is skipped and the graph is written as it is, with the keys and chains already applied.
    # The steps run once each, in that order: what Jena infers afterwards (e.g. values copied through owl:sameAs) does
    # not go back through the keys or the chains.
    # The owl:AllDifferent never go through Jena, which would expand them to pairs (see split_all_different). With
    # different_statements they are added as they are to the output of Jena; otherwise they are left out.
    gg = build_data_graph(reconcile=not dl_reasoner, **kwargs)
    if dl_reasoner:
        from onto.populator.hermit_reasoner import hermit_inferences
        with stage('hermit reasoning', gg):
            same_repositories, chain_values = hermit_inferences(gg, ontology_graph)
            gg += same_repositories
            gg += chain_values
    else:
        with stage('property chains', gg):
            materialize_property_chains(gg)
    with stage('set aside owl:AllDifferent', gg):
        different = split_all_different(gg)
    with stage('add schema', gg):
        for triple in ontology_graph:
            gg.add(triple)
    if jena:
        with tempfile.TemporaryDirectory(prefix='populate-') as staging:
            with stage('jena reasoning'):
                closure_path = materialize(gg, staging)
            shutil.move(closure_path, output)
    else:
        with stage('write without the Jena reasoner (%s triples)' % (len(gg),)):
            gg.serialize(destination=output, format='nt', encoding='utf-8')
    if different_statements:
        with stage('add owl:AllDifferent (%s triples)' % (len(different),)):
            with open(output, 'a', encoding='utf-8') as closure:
                closure.write(different.serialize(format='nt'))
    logger.info('wrote %s: load it with tdb2.tdbloader (see onto/README.md)', output)


def _comma_separated(valid: tuple, name: str):
    def parse(raw: str):
        if raw.strip() in ('', 'none'):
            return ()
        values = tuple(x.strip() for x in raw.split(',') if x.strip())
        unknown = [x for x in values if x not in valid]
        if unknown:
            raise argparse.ArgumentTypeError('%s invalid: %s. Options: %s' % (name, ', '.join(unknown), ', '.join(valid)))
        return values
    return parse


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Populates the knowledge base from the raw data in Mongo. It writes the whole '
                    'graph (schema plus data, with the reasoning materialized) to an N-Triples file, to be loaded by hand '
                    'into a Fuseki dataset with tdb2.tdbloader (see onto/README.md). The populator does not touch Fuseki.',
        epilog='Examples: '
               '"populate --output graph.nt --full --seeds commons,locaciones" (all the records); '
               '"populate --output graph.nt" (a sample); '
               '"populate --output graph.nt --sources dummy" (the dummy source).')
    parser.add_argument('--output', required=True,
                        help='N-Triples file to write, e.g. graph.nt; it is overwritten.')
    parser.add_argument('--sources', type=_comma_separated(ALL_SOURCES, 'source'), default=DEFAULT_SOURCES,
                        help='Sources to walk, comma separated (%s). Default: %s.' % (', '.join(ALL_SOURCES), ', '.join(DEFAULT_SOURCES)))
    parser.add_argument('--seeds', type=_comma_separated(ALL_SEEDS, 'seed'), default=DEFAULT_SEEDS,
                        help='Seeds to sow, comma separated (%s). Default: none.' % ', '.join(ALL_SEEDS))
    reduced_group = parser.add_mutually_exclusive_group()
    reduced_group.add_argument('--reduced', dest='reduced', action='store_true', default=True,
                               help='Walk a sample instead of all the records (default).')
    reduced_group.add_argument('--full', dest='reduced', action='store_false',
                               help='Walk all the records.')
    parser.add_argument('--dl-reasoner', action='store_true',
                        help='Use HermiT (through the OWL API) for what the Jena reasoner does not do: the owl:sameAs between '
                             'repositories that share an identifier and the values of the property chains, on two '
                             'subgraphs, without the HasKey axioms (with them HermiT does not finish on the whole graph). '
                             'The reconciliation subgraph takes about 2 minutes on the whole graph; the chains one was '
                             'only measured on samples. Without it, the same rules are applied in '
                             'Python, in seconds. Unless --no-jena, the Jena reasoner then runs on the whole graph.')
    parser.add_argument('--no-jena', dest='jena', action='store_false',
                        help='Skip the Jena reasoner: the graph is written with the owl:sameAs of the keys and the values of '
                             'the property chains (Python rules or HermiT), but without the rest of the inferences. For '
                             'populating while the Jena reasoner does not finish on the whole graph.')
    parser.add_argument('--different-statements', action='store_true',
                        help='Add to the output the owl:AllDifferent of each group of individuals (licenses, disciplines, '
                             'keywords, etc.). They are set aside before the Jena reasoner, which would expand each one to '
                             'an owl:differentFrom per pair of members, and are added as they are to its output. Without it, '
                             'the output has no owl:AllDifferent.')
    parser.add_argument('--skip', type=int, default=None, help='Skip the first N records of each source.')
    parser.add_argument('--limit', type=int, default=None, help='Process at most N records per source.')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
    logger.info('arguments: %s', vars(args))
    walk_kwargs = {
        'sources': args.sources,
        'seeds': args.seeds,
        'reduced': args.reduced,
        'skip': args.skip,
        'limit': args.limit,
    }
    with stage('populate'):
        write_graph(args.output, dl_reasoner=args.dl_reasoner, different_statements=args.different_statements,
                    jena=args.jena, **walk_kwargs)


if __name__ == '__main__':
    main()
