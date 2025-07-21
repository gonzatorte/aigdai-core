from onto.populator.re3data import process as process_re3data
from re3data.extract_from_repo import BLACKLIST
import onto.cts as cts
import onto.populator.rdf_types as rdf_types
from lib.no_relational_database import get_database_client
from re3data.xsd_transform import refine_repository_info, load_schema
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, OWL
import config
from rdflib.plugins.sparql import prepareQuery
from ror.extractor import insert_on_rdf


def refine_iterator(iterator, white_list: [str], allow_whitelist: bool):
    schema = load_schema()
    refined = []
    for x in iterator:
        if x['idd'] in BLACKLIST:
            continue
        # if allow_whitelist:
        #     if x['idd'] not in white_list:
        #         continue
        rrr = refine_repository_info(schema, x['bin'])
        refined.append(rrr)
    return refined


def refine_and_insert_on_rdf():
    g_repos = Graph()
    # g = Graph(store="BerkeleyDB")
    # g.open("/some/folder/location")
    # g.close()
    # g.parse("....")
    g_repos.bind('', rdf_types.my_ns)

    (g_criterios, ) = seed_criterios()
    (g_disciplinas, ) = seed_disciplinas()
    (g_commons, ) = seed_commons()
    (g_locaciones, ) = seed_locaciones()

    # database = get_database_async()
    database = get_database_client()
    # drepo_collection = database['drepo']
    raw_drepo_collection = database['raw_drepo']
    skip_count = 0
    limit_count = 0
    instances = raw_drepo_collection.find({}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    # instances_count = raw_drepo_collection.count_documents({})
    instance_ids = raw_drepo_collection.find({}, {'idd': True}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    instance_ids = [x['idd'] for x in instance_ids]

    # rdf_ids = {x: URIRef("repositorio/%s" % (x,), my_ns) for x in instance_ids}
    # not_repeated_ids = [x for x in instance_ids if rdf_ids[x] not in g[rdf_ids[x]]]
    not_repeated_ids = instance_ids

    repository_infos = refine_iterator(instances, not_repeated_ids, True)
    total = len(repository_infos)
    print("To process %s" % (total, ))
    counter = 0
    for r_info in repository_infos:
        process_re3data(g_repos, r_info)
        counter += 1
        if counter % 10 == 0:
            print("ready %s out of %s" % (counter, total))
    return g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones

CERTIFICACIONES = []
ORG_ID_SCHEMAS = [
    ('FUNDREF', ['FUNDREF', 'CrossrefFunderID']),
    ('GRID', ['GRID']),
    ('ISNI', ['ISNI']),
    ('WIKIDATA', ['WIKIDATA']),
    ('LOCAL', ['LOCAL']),
]
ORG_ID_SCHEMA_NAMES = [x[0] for x in ORG_ID_SCHEMAS]


def seed_commons():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    for (org_id_name, prefixes) in ORG_ID_SCHEMAS:
        tipo_de_id_de_organizacion = URIRef("tipo_de_id_de_organizacion/%s" % (org_id_name,), rdf_types.my_ns)
        g.set((tipo_de_id_de_organizacion, RDF.type, rdf_types.TipoDeIdDeOrganizacion))
        # for prefix in prefixes:
        #     pass

    for (my_type, name, items) in [
        (rdf_types.MotorDeRepositorio, 'motor_de_repositorio', cts.motores),
        (rdf_types.EsquemaDeIdDeAutor, 'esquema_de_id_de_autor', cts.esquemas_de_id_de_autor),
        (rdf_types.EsquemaDeIdPersistente, 'esquema_de_id_persistente', cts.esquemas_de_id_persistente),
        (rdf_types.EsquemaDeMetadatos, 'esquema_de_metadatos', cts.esquemas_de_metadatos),
        (rdf_types.Licencia, 'licencia', cts.licencias),
        (rdf_types.TipoDeDato, 'tipo_de_dato', cts.tipos_de_dato),
        (rdf_types.ApiParaCosecha, 'api_para_cosecha', cts.apis_para_cosecha),
        (rdf_types.RedSocial, 'red_social', cts.red_social),
        (rdf_types.ExportacionDeCitas, 'exportacion_de_citas', cts.formatos_de_exportacion_de_citas),
    ]:
        items_g = []
        for item_id in items:
            old_id = item_id
            if type(item_id) is tuple:
                item_id = item_id[0]
            item = URIRef("%s/%s" % (name, item_id), rdf_types.my_ns)
            items_g.append(item)
            g.set((item, RDF.type, my_type))
        owl_all_different(g, items_g)

    for (esquema_de_metadatos, esquema_hijos) in cts.esquemas_de_metadatos:
        item = URIRef("esquema_de_metadatos/%s" % (esquema_de_metadatos, ), rdf_types.my_ns)
        for esquema_hijo in esquema_hijos:
            item_hijo = URIRef("esquema_de_metadatos/%s" % (esquema_hijo, ), rdf_types.my_ns)
            g.set((item, rdf_types.extiende_a_esquema_de_metadatos, item_hijo))

    formatos = []
    formato_de_archivo = URIRef('formato_de_archivo', rdf_types.my_ns)
    formato_de_archivo_abierto = URIRef('formato_de_archivo_abierto', rdf_types.my_ns)
    for formato in cts.formatos_de_archivo:
        item = URIRef("formato_de_archivo/%s" % (formato,), rdf_types.my_ns)
        formatos.append(item)
        g.set((item, RDF.type, formato_de_archivo))
    for (formato, _) in cts.formatos_de_archivo_abierto:
        item = URIRef("formato_de_archivo/%s" % (formato.lower(),), rdf_types.my_ns)
        formatos.append(item)
        g.set((item, RDF.type, formato_de_archivo_abierto))
    owl_all_different(g, formatos)

    return (g,)

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
        target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))

    for (target_criterio_id, criterios_extends_to, criterios_considered) in cts.criterio_de_calidad_extiende_de:
        target_criterio = URIRef("criterio_de_calidad/%s" % (target_criterio_id,), rdf_types.principles_ns)
        g.set((target_criterio, RDF.type, rdf_types.CriterioDeCalidad))
        for criterio_extends_to_id in criterios_extends_to:
            criterio_extends_to = URIRef("criterio_de_calidad/%s" % (criterio_extends_to_id,), rdf_types.principles_ns)
            g.set((criterio_extends_to, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target_criterio, rdf_types.extiende_de_criterio, criterio_extends_to))

        for criterio_considered_id in criterios_considered:
            criterio_considered = URIRef("criterio_de_calidad/%s" % (criterio_considered_id,), rdf_types.principles_ns)
            g.set((criterio_considered, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target_criterio, rdf_types.considera_criterio, criterio_considered))

    # ToDo: same_individuals

    trust = URIRef("criterio_de_calidad/trust", rdf_types.principles_ns)
    # ToDo: Map related_with_funcionalidad
    for (target_id, category, description, related_with_funcionalidad) in cts.metricas_trust:
        target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, trust))

        grupo_de_criterio = URIRef("grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    plan_s = URIRef("criterio_de_calidad/plan_s", rdf_types.principles_ns)
    # ToDo: Map importance to model
    for (target_id, _, description, importance, related_with_funcionalidad) in cts.metricas_plan_s:
        target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, plan_s))

    cts_2022 = URIRef("criterio_de_calidad/cts_2022", rdf_types.principles_ns)
    for (target_id, category, name, description) in cts.metricas_cts_2022:
        target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal("%s - %s" % (name, description))))
        g.set((target, rdf_types.extiende_de_criterio, cts_2022))

        grupo_de_criterio = URIRef("grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    criterio_de_calidad_coar = URIRef("criterio_de_calidad/coar_v1", rdf_types.principles_ns)
    # ToDo: Map importance to model
    for (target_id, category, description, importance, related_with_criterios) in cts.metricas_coar:
        target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, criterio_de_calidad_coar))

        grupo_de_criterio = URIRef("grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    fair = URIRef("criterio_de_calidad/fair", rdf_types.principles_ns)
    # for (target_id, _) in cts.metricas_fair:
    #     # ToDo: Tengo que relacionar con (same as) con https://w3id.org/fair/principles/terms/ de https://peta-pico.github.io/FAIR-nanopubs/principles/ontology.xml
    #     pass
    for (target_id, _) in cts.fair_maturity_models:
        target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.extiende_de_criterio, fair))
    rda_fair_maturity_model = URIRef("criterio_de_calidad/rda_fair_maturity_model", rdf_types.principles_ns)
    fsf_fair_maturity_model = URIRef("criterio_de_calidad/fsf_fair_maturity_model", rdf_types.principles_ns)
    # ToDo: Hacer el DSM
    # dsm_fair_maturity_model = URIRef("criterio_de_calidad/dsm_fair_maturity_model", rdf_types.principles_ns)
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
            target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
            g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
            parent = URIRef("criterio_de_calidad/%s" % (parent_id,), rdf_types.principles_ns)
            g.set((parent, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
            g.set((target, rdf_types.extiende_de_criterio, parent))
            g.set((target, rdf_types.extiende_de_criterio, parent_maturity_model))

    posi = URIRef("criterio_de_calidad/posi", rdf_types.principles_ns)
    for (target_id, category, description, importance, parents) in cts.metricas_posi:
        target = URIRef("criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))

        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio
        grupo_de_criterio = URIRef("grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))

        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, posi))

    return (g,)

def seed_disciplinas():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    # ToDo: DFG disciplina es una clase definida por todas las disciplinas DFG?
    all_dfg_disciplinas = []
    def tree_walk_disciplina(forest, parent):
        for tr in forest:
            disciplina = URIRef("disciplina/%s" % (tr[0],), rdf_types.my_ns)
            all_dfg_disciplinas.append(disciplina)
            g.set((disciplina, RDF.type, rdf_types.Disciplina))
            g.set((disciplina, rdf_types.nombre_de_disciplina, Literal(tr[1])))
            g.set((disciplina, rdf_types.esquema_de_disciplina, Literal('dfg')))

            if parent is not None:
                parent_g = URIRef("disciplina/%s" % (parent,), rdf_types.my_ns)
                g.set((disciplina, rdf_types.es_sub_disciplina_de, parent_g))
            if len(tr) >= 3:
                children = tr[2]
                tree_walk_disciplina(children, tr[0])
    tree_walk_disciplina(cts.dfg_subjects, None)
    owl_all_different(g, all_dfg_disciplinas)

    return (g,)

def seed_locaciones():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    cys = []
    internacional = URIRef("locacion/global", rdf_types.my_ns)
    cys.append(internacional)
    g.set((internacional, RDF.type, rdf_types.Locacion))
    for country_or_block in cts.countries:
        if len(country_or_block) >= 3:
            bl = URIRef("locacion/%s" % (country_or_block[0],), rdf_types.my_ns)
            cys.append(bl)
            g.set((bl, RDF.type, rdf_types.Locacion))
            g.set((bl, rdf_types.nombre_de_locacion, Literal(country_or_block[1])))
            g.set((bl, rdf_types.incluido_en, internacional))
            for country in country_or_block[2]:
                cy = URIRef("pais/%s" % (country[0],), rdf_types.my_ns)
                cys.append(cy)
                g.set((cy, RDF.type, rdf_types.Pais))
                g.set((cy, rdf_types.incluido_en, bl))
                g.set((cy, rdf_types.alfa_3_de_pais, Literal(country[0])))
                g.set((cy, rdf_types.nombre_de_locacion, Literal(country[1])))
        else:
            cy = URIRef("pais/%s" % (country_or_block[0],), rdf_types.my_ns)
            cys.append(cy)
            g.set((cy, RDF.type, rdf_types.Pais))
            g.set((cy, rdf_types.incluido_en, internacional))
            g.set((cy, rdf_types.alfa_3_de_pais, Literal(country_or_block[0])))
            g.set((cy, rdf_types.nombre_de_locacion, Literal(country_or_block[1])))
    owl_all_different(g, cys)
    return (g,)


def serialize_all():
    g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones = refine_and_insert_on_rdf()
    # print(g.serialize(destination='../owl/repositorios.xml', format="pretty-xml"))
    # g_repos.objects(subject=None, predicate=None, unique=True)

    orgs_types_literals_query = prepareQuery("""
    SELECT DISTINCT ?o ?t ?l
    WHERE {
      ?i rdf:type :id_de_organizacion .
      ?i :id_de_organizacion_tiene_tipo ?t .
      ?i :id_de_organizacion_tiene_literal ?l .
      ?i :id_de_organizacion_tiene_organizacion ?o
    }""", initNs={'my': rdf_types.my_ns, 'rdf': RDF, '': 'http://aigdai-tbox.owl/'})
    orgs_types_literals = {"%s:%s" % (tt, ll.value) for (_, tt, ll) in g_repos.query(orgs_types_literals_query)}

    g_orgs = insert_on_rdf(orgs_types_literals)
    # g_orgs.remove((bob, None, None))
    # ToDo: alternativa es mandarlo todo a fuseki usando cosas como
    # curl 'http://localhost:3030/ElQuijote/' \
    # -H 'Accept: text/plain,*/*;q=0.9' \
    # -H 'Content-Type: application/x-www-form-urlencoded' \
    # --data-raw 'update=encodeURIComponent(
    # INSERT DATA {
    #	ns:Pepe ns:knows  ns:Don_Quijote .
    # }
    # )'

    g_repos.serialize(destination='../owl/repositorios.xml', format="xml")
    g_criterios.serialize(destination='../owl/criterios.xml', format="xml")
    g_disciplinas.serialize(destination='../owl/disciplinas.xml', format="xml")
    g_commons.serialize(destination='../owl/commons.xml', format="xml")
    g_locaciones.serialize(destination='../owl/localizaciones.xml', format="xml")
    g_orgs.serialize(destination='../owl/organizaciones.xml', format="xml")


def reason_on_memory():
    # g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones = refine_and_insert_on_rdf()
    # g_orgs = insert_on_rdf()
    import owlready2 as ow

    ow.JAVA_EXE = config.JAVA_EXE_PATH
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


if __name__ == '__main__':
    serialize_all()
    # reason_on_memory()
