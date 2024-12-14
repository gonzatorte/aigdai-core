import re
from re3data.extract_from_repo import BLACKLIST
import onto.cts as cts
import onto.generator.rdf as rdf_types
from lib.no_relational_database import get_database_client
from re3data.xsd_transform import refine_repository_info, load_schema
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, OWL

def owl_all_different(g, instances):
    for (idx, instance1) in enumerate(instances):
        for instance2 in instances[idx+1:]:
            g.add((instance1, OWL.differentFrom, instance2))

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
    g_criterios.serialize(destination='../owl/criterios.xml', format="xml")
    (g_disciplinas, ) = seed_disciplinas()
    g_disciplinas.serialize(destination='../owl/disciplinas.xml', format="xml")
    (g_commons, ) = seed_commons()
    g_commons.serialize(destination='../owl/commons.xml', format="xml")
    (g_locaciones, ) = seed_locaciones()
    g_locaciones.serialize(destination='../owl/locations.xml', format="xml")


    # database = get_database_async()
    database = get_database_client()
    # drepo_collection = database['drepo']
    raw_drepo_collection = database['raw_drepo']
    skip_count = 0
    limit_count = 20
    instances = raw_drepo_collection.find({}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    # instances_count = raw_drepo_collection.count_documents({})
    instance_ids = raw_drepo_collection.find({}, {'idd': True}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    instance_ids = [x['idd'] for x in instance_ids]

    # rdf_ids = {x: URIRef("#repositorio/%s" % (x,), my_ns) for x in instance_ids}
    # not_repeated_ids = [x for x in instance_ids if rdf_ids[x] not in g[rdf_ids[x]]]
    not_repeated_ids = instance_ids

    def process(repository_info):
        repositorio = URIRef("#repositorio/%s" % (repository_info['id'], ), rdf_types.my_ns)
        g_repos.set((repositorio, RDF.type, rdf_types.Repositorio))
        g_repos.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(repository_info['repositoryName'])))

        for db_instance in repository_info['institutions']:
            id_org = db_instance['id'].replace(' ', '')
            r_instance = URIRef("#organizacion/%s" % (id_org,), rdf_types.my_ns)
            g_repos.set((r_instance, RDF.type, rdf_types.Organizacion))
            g_repos.set((r_instance, rdf_types.tiene_nombre_organizacion, Literal(db_instance['institutionName'])))
            if db_instance['institutionCountry'] != 'EEC':
                location = URIRef("#pais/%s" % (db_instance['institutionCountry'],), rdf_types.my_ns)
                g_repos.set((location, RDF.type, rdf_types.Pais))
            else:
                location = URIRef("#bloque_comercial/%s" % ('UE',), rdf_types.my_ns)
                g_repos.set((location, RDF.type, rdf_types.BloqueComercial))
            g_repos.set((r_instance, rdf_types.se_ubica_en, location))

            g_repos.add((r_instance, rdf_types.tiene_tipo_de_organizacion, Literal(db_instance['institutionType'])))

            id_match = re.match('^(?P<type>.+(?=[:;.])|CrossrefFunderID)', id_org)
            if not id_match:
                print(id_org, repository_info['id'])
                continue
            tipo_de_id_de_organizacion_str = id_match.groupdict().get('type')
            tipo_de_id_de_organizacion = URIRef("#tipo_de_id_de_organizacion/%s" % (tipo_de_id_de_organizacion_str.upper(),), rdf_types.my_ns)

            # ToDo: Ver si el id_org tiene un prefijo
            id_de_organizacion = URIRef("#id_de_organizacion/%s" % (id_org,), rdf_types.my_ns)
            g_repos.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
            # ToDo: tipo_de_id_de_organizacion puede ser ROR, RRID, local y que otro?
            g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion))
            g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(id_org)))
            g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, r_instance))

            # ToDo: Falta el tipo de relacion que tiene con el repositorio
            #     <DatatypeDefinition>
            #         <Datatype IRI="tipo_de_organizacion"/>
            #         <DataOneOf>
            #             <Literal>comercial</Literal>
            #             <Literal>no-comercial</Literal>
            #         </DataOneOf>
            #     </DatatypeDefinition>
            #     <DatatypeDefinition>
            #         <Datatype IRI="tipo_de_relacion_con_organizacion"/>
            #         <DataOneOf>
            #             <Literal>administrativa</Literal>
            #             <Literal>financiamiento</Literal>
            #             <Literal>técnica</Literal>
            #         </DataOneOf>
            #     </DatatypeDefinition>

            for responsibilityType in db_instance.get('responsibilityType', []):
                # ToDo: responsibilityType puede ser general, profit, non-profit, y que otro?
                relacion_repositorio_y_organizacion = URIRef("#relacion_repositorio_y_organizacion/%s-%s-%s" % (id_org, repository_info['id'], responsibilityType), rdf_types.my_ns)
                g_repos.set((relacion_repositorio_y_organizacion, RDF.type, rdf_types.RelacionRepositorioYOrganizacion))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_repositorio, repositorio))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_organizacion, r_instance))
                # g.set((relacion_repositorio_y_organizacion, tiene_periodo_de_relacion_con_organizacion, ))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.tiene_tipo_de_relacion_con_organizacion, Literal(responsibilityType)))

        software_names = [x for x in repository_info['softwareNames'] if x != 'unknown']
        software_name = software_names[0] if len(software_names) >= 1 else None
        if software_name == 'other':
            software_name = "other_%s" % (repository_info['id'],)
        if software_name is not None:
            motor = URIRef("#motor_de_repositorio/%s" % (software_name, ), rdf_types.my_ns)
            g_repos.set((motor, RDF.type, rdf_types.MotorDeRepositorio))
            # ToDo: Tendria que decir que todos los motores recabados por re3data con nombres diferentes son diferentes efectivamente?
            #  justo con other_algo no pasa eso. other_1 es diferente a ckan, a dataverse, etc... pero no es diferente a other_2...
            g_repos.set((repositorio, rdf_types.utiliza_motor, motor))

        # for api in repository_info['apis']:
        #     r_instance = Api(
        #         id=api['url'],
        #         type=api['type'],
        #     )
        #     session.add(r_instance)
        #     result = r_instance

        for db_instance in repository_info['subjects']:
            r_instance = URIRef("#disciplina/%s" % (db_instance,), rdf_types.my_ns)
            g_repos.add((repositorio, rdf_types.repositorio_afin_a_disciplina, r_instance))

    repository_infos = refine_iterator(instances, not_repeated_ids, True)
    total = len(repository_infos)
    print("To process %s" % (total, ))
    counter = 0
    for r_info in repository_infos:
        process(r_info)
        counter += 1
        if counter % 10 == 0:
            print("ready %s out of %s" % (counter, total))
    g_repos.serialize(destination='../owl/instances.xml', format="xml")
    # print(g.serialize(destination='../owl/instances.xml', format="pretty-xml"))

CERTIFICACIONES = []
LENGUAJES = []
PID_ESQUEMA = []

def seed_commons():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    for (name, items) in [
        ('motor_de_repositorio', cts.motores),
        ('esquema_de_id_de_autor', cts.esquemas_de_id_de_autor),
        ('esquema_de_id_persistente', cts.esquemas_de_id_persistente),
        ('esquema_de_metadatos', cts.esquemas_de_metadatos),
        ('licencia', cts.licencias),
        ('tipo_de_dato', cts.tipos_de_dato),
        ('api_para_cosecha', cts.apis_para_cosecha),
        ('integracion_con_red_social', cts.integraciones_con_red_social),
        ('exportacion_de_citas', cts.formatos_de_exportacion_de_citas),
    ]:
        my_type = URIRef('#%s' % (name,), rdf_types.my_ns)
        items_g = []
        for item_id in items:
            item = URIRef("#%s/%s" % (name, item_id), rdf_types.my_ns)
            items_g.append(item)
            g.set((item, RDF.type, my_type))
        owl_all_different(g, items_g)

    formatos = []
    formato_de_archivo = URIRef('#formato_de_archivo', rdf_types.my_ns)
    formato_de_archivo_abierto = URIRef('#formato_de_archivo_abierto', rdf_types.my_ns)
    for formato in cts.formatos_de_archivo:
        item = URIRef("#formato_de_archivo/%s" % (formato,), rdf_types.my_ns)
        formatos.append(item)
        g.set((item, RDF.type, formato_de_archivo))
    for (formato, _) in cts.formatos_de_archivo_abierto:
        item = URIRef("#formato_de_archivo/%s" % (formato.lower(),), rdf_types.my_ns)
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

    criterio_de_calidad_coar = URIRef("#criterio_de_calidad/coar", rdf_types.principles_ns)
    g.set((criterio_de_calidad_coar, RDF.type, rdf_types.CriterioDeCalidad))
    for (idd, category, description, importance, related_with_criterios) in cts.metricas_coar:
        criterio_de_calidad = URIRef("#criterio_de_calidad/%s" % (idd,), rdf_types.principles_ns)
        g.set((criterio_de_calidad, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((criterio_de_calidad, rdf_types.criterio_tiene_descripcion, Literal(description)))
        grupo_de_criterio = URIRef("#grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        g.set((criterio_de_calidad, rdf_types.extiende_de_criterio, criterio_de_calidad_coar))

    for (idd, name, url) in cts.criterios_de_calidad:
        criterio_de_calidad = URIRef("#criterio_de_calidad/%s" % (idd,), rdf_types.principles_ns)
        g.set((criterio_de_calidad, RDF.type, rdf_types.CriterioDeCalidad))

    for (target_criterio_id, criterios_extends_to, criterios_considered) in cts.criterio_de_calidad_extiende_de:
        target_criterio = URIRef("#criterio_de_calidad/%s" % (target_criterio_id,), rdf_types.principles_ns)
        g.set((target_criterio, RDF.type, rdf_types.CriterioDeCalidad))
        for criterio_extends_to_id in criterios_extends_to:
            criterio_extends_to = URIRef("#criterio_de_calidad/%s" % (criterio_extends_to_id,), rdf_types.principles_ns)
            g.set((criterio_extends_to, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target_criterio, rdf_types.extiende_de_criterio, criterio_extends_to))

        for criterio_considered_id in criterios_considered:
            criterio_considered = URIRef("#criterio_de_calidad/%s" % (criterio_considered_id,), rdf_types.principles_ns)
            g.set((target_criterio, rdf_types.considera_criterio, criterio_considered))
    return (g,)

def seed_disciplinas():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    # ToDo: DFG disciplina es una clase definida por todas las disciplinas DFG?
    all_dfg_disciplinas = []
    def tree_walk_disciplina(forest, parent):
        for tr in forest:
            disciplina = URIRef("#disciplina/%s" % (tr[0],), rdf_types.my_ns)
            all_dfg_disciplinas.append(disciplina)
            g.set((disciplina, RDF.type, rdf_types.Disciplina))
            g.set((disciplina, rdf_types.nombre_de_disciplina, Literal(tr[1])))
            g.set((disciplina, rdf_types.esquema_de_disciplina, Literal('dfg')))

            if parent is not None:
                parent_g = URIRef("#disciplina/%s" % (parent,), rdf_types.my_ns)
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
    planeta_tierra = URIRef("#planeta/%s" % ('tierra',), rdf_types.my_ns)
    cys.append(planeta_tierra)
    g.set((planeta_tierra, RDF.type, rdf_types.Planeta))
    for country_or_block in cts.countries:
        if len(country_or_block) >= 3:
            bl = URIRef("#bloque_comercial/%s" % (country_or_block[0],), rdf_types.my_ns)
            cys.append(bl)
            g.set((bl, RDF.type, rdf_types.BloqueComercial))
            bl.nombre_de_bloque = country_or_block[1]
            g.set((bl, rdf_types.incluido_en, planeta_tierra))
            for country in country_or_block[2]:
                cy = URIRef("#pais/%s" % (country[0],), rdf_types.my_ns)
                cys.append(cy)
                g.set((cy, RDF.type, rdf_types.Pais))
                g.set((cy, rdf_types.incluido_en, bl))
                g.set((cy, rdf_types.alfa_3_de_pais, Literal(country[0])))
                g.set((cy, rdf_types.nombre_de_pais, Literal(country[1])))
        else:
            cy = URIRef("#pais/%s" % (country_or_block[0],), rdf_types.my_ns)
            cys.append(cy)
            g.set((cy, RDF.type, rdf_types.Pais))
            g.set((cy, rdf_types.incluido_en, planeta_tierra))
            g.set((cy, rdf_types.alfa_3_de_pais, Literal(country_or_block[0])))
            g.set((cy, rdf_types.nombre_de_pais, Literal(country_or_block[1])))
    owl_all_different(g, cys)
    return (g,)


if __name__ == '__main__':
    refine_and_insert_on_rdf()
