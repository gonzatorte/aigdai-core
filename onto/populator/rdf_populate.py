import re
from re3data.extract_from_repo import BLACKLIST
import onto.cts as cts
import onto.generator.rdf as rdf_types
from lib.no_relational_database import get_database_client
from re3data.xsd_transform import refine_repository_info, load_schema
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, OWL
import hashlib

from ror.extractor import insert_on_rdf


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

def remap_institution_type(institution_type: str):
    if institution_type == 'commercial':
        return 'comercial'
    elif institution_type == 'non-profit':
        return 'nonprofit'
    elif institution_type is None:
        return None
    raise Exception()


def remap_institution_relation_type(relation_type: str):
    if relation_type == 'sponsoring':
        return 'patrocinio'
    elif relation_type == 'general':
        return 'general'
    elif relation_type == 'funding':
        return 'financiamiento'
    elif relation_type == 'technical':
        return 'técnica'
    elif relation_type is None:
        return None
    raise Exception()


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
    g_locaciones.serialize(destination='../owl/localizaciones.xml', format="xml")

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
        g_repos.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(repository_info['repositoryName']['text'], lang=repository_info['repositoryName']['lang'])))
        g_repos.set((repositorio, rdf_types.tiene_descripcion_repositorio, Literal(repository_info['description']['text'], lang=repository_info['description']['lang'])))
        g_repos.set((repositorio, rdf_types.tiene_url_repositorio, Literal(repository_info['repositoryURL'])))

        for db_instance in repository_info['institutions']:
            id_org = db_instance['id'].replace(' ', '')
            r_instance = URIRef("#organizacion/%s" % (id_org,), rdf_types.my_ns)
            g_repos.set((r_instance, RDF.type, rdf_types.Organizacion))

            g_repos.set((r_instance, rdf_types.tiene_nombre_organizacion, Literal(db_instance['institutionName']['text'], lang=db_instance['institutionName']['lang'])))
            for instName in db_instance['institutionAdditionalNames']:
                g_repos.set((r_instance, rdf_types.tiene_nombre_organizacion, Literal(instName['text'], lang=instName['lang'])))

            if db_instance['institutionCountry'] == 'EEC':
                location = URIRef("#locacion/%s" % ('UE',), rdf_types.my_ns)
                g_repos.set((location, RDF.type, rdf_types.Locacion))
            elif db_instance['institutionCountry'] == 'AAA':
                location = URIRef("#locacion/global", rdf_types.my_ns)
                g_repos.set((location, RDF.type, rdf_types.Locacion))
            else:
                location = URIRef("#pais/%s" % (db_instance['institutionCountry'],), rdf_types.my_ns)
                g_repos.set((location, RDF.type, rdf_types.Pais))
            g_repos.set((r_instance, rdf_types.se_ubica_en, location))

            g_repos.add((r_instance, rdf_types.tiene_tipo_de_organizacion, Literal(
                remap_institution_type(db_instance['institutionType'])
            )))

            for raw_idd_org in db_instance['ids']:
                idd_org = raw_idd_org.replace(' ', '')
                idd_match = re.match('^(?P<type>.+(?=[:;.])|CrossrefFunderID)', idd_org, re.IGNORECASE)
                if not idd_match:
                    print(idd_org, raw_idd_org)
                    continue
                tipo_de_id_de_organizacion_str = idd_match.groupdict().get('type')
                tipo_de_id_de_organizacion = URIRef("#tipo_de_id_de_organizacion/%s" % (tipo_de_id_de_organizacion_str.upper(),), rdf_types.my_ns)

                # ToDo: Ver si el id_org tiene un prefijo
                id_de_organizacion = URIRef("#id_de_organizacion/%s" % (idd_org,), rdf_types.my_ns)
                g_repos.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                # ToDo: tipo_de_id_de_organizacion puede ser ROR, RRID, LOCAL y que otro?
                #  new Set(db.drepo.aggregate([{$project: {'institutions': 1}}, {$unwind: '$institutions'},{$project: {'institutions.id': 1}}]).toArray().map(a => a.institutions.id.replace(' ', ':').split(/[:.;]/)[0]))
                g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion))
                g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(idd_org)))
                g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, r_instance))

            inicio_periodo_de_relacion_con_organizacion = db_instance.get('responsibilityTypes', None)
            fin_periodo_de_relacion_con_organizacion = db_instance.get('responsibilityTypes', None)
            for responsibilityType in db_instance.get('responsibilityTypes', []):
                relacion_repositorio_y_organizacion = URIRef("#relacion_repositorio_y_organizacion/%s-%s-%s" % (id_org, repository_info['id'], responsibilityType), rdf_types.my_ns)
                g_repos.set((relacion_repositorio_y_organizacion, RDF.type, rdf_types.RelacionRepositorioYOrganizacion))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_repositorio, repositorio))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_organizacion, r_instance))
                if inicio_periodo_de_relacion_con_organizacion:
                    g_repos.set((relacion_repositorio_y_organizacion, rdf_types.tiene_inicio_periodo_de_relacion_con_organizacion, Literal(inicio_periodo_de_relacion_con_organizacion)))
                if fin_periodo_de_relacion_con_organizacion:
                    g_repos.set((relacion_repositorio_y_organizacion, rdf_types.tiene_fin_periodo_de_relacion_con_organizacion, Literal(fin_periodo_de_relacion_con_organizacion)))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.tiene_tipo_de_relacion_con_organizacion, Literal(
                    remap_institution_relation_type(responsibilityType)
                )))

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

        for api in repository_info['apis']:
            api_type = api['type']
            if api_type == 'other':
                api_type = "other_%s" % (repository_info['id'],)
            api_para_cosecha = URIRef("#api_para_cosecha/%s" % (api_type, ), rdf_types.my_ns)
            g_repos.set((api_para_cosecha, RDF.type, rdf_types.ApiParaCosecha))
            # Should be inferred
            # g_repos.set((api_para_cosecha, rdf_types.repositorio_aporta_funcionalidad, repositorio))

            api_para_cosecha_con_url = URIRef("#api_para_cosecha_con_url/%s" % (api['url'], ), rdf_types.my_ns)
            g_repos.set((api_para_cosecha_con_url, RDF.type, rdf_types.ApiParaCosechaConUrl))
            g_repos.set((api_para_cosecha_con_url, rdf_types.api_para_cosecha_con_url_tiene_url, Literal(api['url'])))
            g_repos.set((api_para_cosecha_con_url, rdf_types.api_para_cosecha_con_url_tiene_api_para_cosecha, api_para_cosecha))
            g_repos.set((api_para_cosecha_con_url, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for metadata_standard in repository_info['metadataStandards']:
            # ToDo: Poner modelo intermedio con evidencia
            metadata_standard_name = metadata_standard['name']
            if metadata_standard_name == 'other':
                metadata_standard_name = "other_%s" % (repository_info['id'],)
            # ToDo: Unificar enumerados o declarar same-as
            esquema_de_metadatos = URIRef("#esquema_de_metadatos/%s" % (metadata_standard_name.lower().replace(' ', '_'), ), rdf_types.my_ns)
            g_repos.set((esquema_de_metadatos, RDF.type, rdf_types.EsquemaDeMetadatos))
            g_repos.set((esquema_de_metadatos, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for aid_system in repository_info['aidSystems']:
            if aid_system == 'other':
                aid_system = "other_%s" % (repository_info['id'],)
            # ToDo: Unificar enumerados o declarar same-as
            esquema_de_id_de_autor = URIRef("#esquema_de_id_de_autor/%s" % (aid_system, ), rdf_types.my_ns)
            g_repos.set((esquema_de_id_de_autor, RDF.type, rdf_types.EsquemaDeIdDeAutor))
            g_repos.set((esquema_de_id_de_autor, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for pid_system in repository_info['pidSystems']:
            if pid_system == 'other':
                pid_system = "other_%s" % (repository_info['id'],)
            # ToDo: Unificar enumerados o declarar same-as
            esquema_de_id_persistente = URIRef("#esquema_de_id_persistente/%s" % (pid_system, ), rdf_types.my_ns)
            g_repos.set((esquema_de_id_persistente, RDF.type, rdf_types.EsquemaDeIdPersistente))
            g_repos.set((esquema_de_id_persistente, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for content_type in repository_info['contentType']:
            # ToDo: Manejar other, ponerle other_id
            # ToDo: Unificar enumerados o declarar same-as
            tipo_de_dato = URIRef("#tipo_de_dato/%s" % (content_type.lower().replace(' ', '_'), ), rdf_types.my_ns)
            g_repos.set((tipo_de_dato, RDF.type, rdf_types.TipoDeDato))
            g_repos.set((tipo_de_dato, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        # for quality_management in repository_info['qualityManagement']:
        #     # ToDo: Revisar si es un ObjectProperty, y si modelarlo como bool
        #     servicio_de_curaduria = URIRef("#servicio_de_curaduria/%s" % (quality_management, ), rdf_types.my_ns)
        #     g_repos.set((servicio_de_curaduria, RDF.type, rdf_types.ServicioDeCuraduria))
        #     g_repos.set((servicio_de_curaduria, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        # databaseLicenses
        # databaseAccess
        # dataLicenses
        # dataAccess
        # dataUploadLicenses
        # dataUpload

        for policy in repository_info['policies']:
            local_id_politica = hashlib.md5(policy['url'].encode('utf-8')).hexdigest()
            politica = URIRef("#politica/%s" % (local_id_politica, ), rdf_types.my_ns)
            # ToDo: Revisar si es un ObjectProperty
            g_repos.set((politica, RDF.type, rdf_types.Politica))
            g_repos.set((politica, rdf_types.repositorio_aporta_funcionalidad, repositorio))
            g_repos.set((politica, rdf_types.tiene_nombre_politica, Literal(policy['name'])))
            g_repos.set((politica, rdf_types.tiene_url_politica, Literal(policy['url'])))

        for data_license in repository_info['dataLicenses']:
            local_id_data_license = hashlib.md5(data_license['url'].encode('utf-8')).hexdigest()
            licencia_data = URIRef("#licencia/%s" % (local_id_data_license, ), rdf_types.my_ns)
            # ToDo: Revisar si es un ObjectProperty
            g_repos.set((licencia_data, RDF.type, rdf_types.Licencia))
            g_repos.set((licencia_data, rdf_types.repositorio_aporta_funcionalidad, repositorio))
            g_repos.set((licencia_data, rdf_types.tiene_nombre_politica, Literal(data_license['name'])))
            g_repos.set((licencia_data, rdf_types.tiene_url_politica, Literal(data_license['url'])))

        # data_access_types = [x['type'] for x in repository_info['dataAccess']]
        # is_open_access_supported = 'open' in data_access_types
        # is_restricted_access_supported = 'restricted' in data_access_types
        # # restrictions
        # is_closed_access_supported = 'closed' in data_access_types

        for subject in repository_info['subjects']:
            disciplina = URIRef("#disciplina/%s" % (subject,), rdf_types.my_ns)
            g_repos.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))

    repository_infos = refine_iterator(instances, not_repeated_ids, True)
    total = len(repository_infos)
    print("To process %s" % (total, ))
    counter = 0
    for r_info in repository_infos:
        process(r_info)
        counter += 1
        if counter % 10 == 0:
            print("ready %s out of %s" % (counter, total))
    g_repos.serialize(destination='../owl/repositorios.xml', format="xml")
    # print(g.serialize(destination='../owl/repositorios.xml', format="pretty-xml"))

CERTIFICACIONES = []
LENGUAJES = []
PID_ESQUEMA = []

def seed_commons():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    for (my_type, name, items) in [
        (rdf_types.MotorDeRepositorio, 'motor_de_repositorio', cts.motores),
        (rdf_types.EsquemaDeIdDeAutor, 'esquema_de_id_de_autor', cts.esquemas_de_id_de_autor),
        (rdf_types.EsquemaDeIdPersistente, 'esquema_de_id_persistente', cts.esquemas_de_id_persistente),
        (rdf_types.EsquemaDeMetadatos, 'esquema_de_metadatos', cts.esquemas_de_metadatos),
        (rdf_types.Licencia, 'licencia', cts.licencias),
        (rdf_types.TipoDeDato, 'tipo_de_dato', cts.tipos_de_dato),
        (rdf_types.ApiParaCosecha, 'api_para_cosecha', cts.apis_para_cosecha),
        (rdf_types.IntegracionConRedSocial, 'integracion_con_red_social', cts.integraciones_con_red_social),
        (rdf_types.ExportacionDeCitas, 'exportacion_de_citas', cts.formatos_de_exportacion_de_citas),
        (rdf_types.ServicioDeCuraduria, 'servicio_de_curaduria', cts.enum_servicio_de_curaduria),
        (rdf_types.ServicioDeVersionado, 'servicio_de_versionado', cts.enum_versionado),
    ]:
        items_g = []
        for item_id in items:
            old_id = item_id
            if type(item_id) is tuple:
                item_id = item_id[0]
            item = URIRef("#%s/%s" % (name, item_id), rdf_types.my_ns)
            items_g.append(item)
            g.set((item, RDF.type, my_type))
        owl_all_different(g, items_g)

    for (esquema_de_metadatos, esquema_hijos) in cts.esquemas_de_metadatos:
        item = URIRef("#esquema_de_metadatos/%s" % (esquema_de_metadatos, ), rdf_types.my_ns)
        for esquema_hijo in esquema_hijos:
            item_hijo = URIRef("#esquema_de_metadatos/%s" % (esquema_hijo, ), rdf_types.my_ns)
            g.set((item, rdf_types.extiende_a_esquema_de_metadatos, item_hijo))

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

    for (target_id, name, url) in cts.criterios_de_calidad:
        target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))

    for (target_criterio_id, criterios_extends_to, criterios_considered) in cts.criterio_de_calidad_extiende_de:
        target_criterio = URIRef("#criterio_de_calidad/%s" % (target_criterio_id,), rdf_types.principles_ns)
        g.set((target_criterio, RDF.type, rdf_types.CriterioDeCalidad))
        for criterio_extends_to_id in criterios_extends_to:
            criterio_extends_to = URIRef("#criterio_de_calidad/%s" % (criterio_extends_to_id,), rdf_types.principles_ns)
            g.set((criterio_extends_to, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target_criterio, rdf_types.extiende_de_criterio, criterio_extends_to))

        for criterio_considered_id in criterios_considered:
            criterio_considered = URIRef("#criterio_de_calidad/%s" % (criterio_considered_id,), rdf_types.principles_ns)
            g.set((criterio_considered, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target_criterio, rdf_types.considera_criterio, criterio_considered))

    # ToDo: same_individuals

    trust = URIRef("#criterio_de_calidad/trust", rdf_types.principles_ns)
    # ToDo: Map related_with_funcionalidad
    for (target_id, category, description, related_with_funcionalidad) in cts.metricas_trust:
        target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, trust))

        grupo_de_criterio = URIRef("#grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    plan_s = URIRef("#criterio_de_calidad/plan_s", rdf_types.principles_ns)
    # ToDo: Map importance to model
    for (target_id, _, description, importance, related_with_funcionalidad) in cts.metricas_plan_s:
        target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, plan_s))

    cts_2022 = URIRef("#criterio_de_calidad/cts_2022", rdf_types.principles_ns)
    for (target_id, category, name, description) in cts.metricas_cts_2022:
        target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal("%s - %s" % (name, description))))
        g.set((target, rdf_types.extiende_de_criterio, cts_2022))

        grupo_de_criterio = URIRef("#grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    criterio_de_calidad_coar = URIRef("#criterio_de_calidad/coar_v1", rdf_types.principles_ns)
    # ToDo: Map importance to model
    for (target_id, category, description, importance, related_with_criterios) in cts.metricas_coar:
        target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
        g.set((target, rdf_types.extiende_de_criterio, criterio_de_calidad_coar))

        grupo_de_criterio = URIRef("#grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
        g.set((grupo_de_criterio, RDF.type, rdf_types.GrupoDeCriterio))
        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio

    fair = URIRef("#criterio_de_calidad/fair", rdf_types.principles_ns)
    # for (target_id, _) in cts.metricas_fair:
    #     # ToDo: Tengo que relacionar con (same as) con https://w3id.org/fair/principles/terms/ de https://peta-pico.github.io/FAIR-nanopubs/principles/ontology.xml
    #     pass
    for (target_id, _) in cts.fair_maturity_models:
        target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
        g.set((target, rdf_types.extiende_de_criterio, fair))
    rda_fair_maturity_model = URIRef("#criterio_de_calidad/rda_fair_maturity_model", rdf_types.principles_ns)
    fsf_fair_maturity_model = URIRef("#criterio_de_calidad/fsf_fair_maturity_model", rdf_types.principles_ns)
    # ToDo: Hacer el DSM
    # dsm_fair_maturity_model = URIRef("#criterio_de_calidad/dsm_fair_maturity_model", rdf_types.principles_ns)
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
            target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
            g.set((target, RDF.type, rdf_types.CriterioDeCalidad))
            parent = URIRef("#criterio_de_calidad/%s" % (parent_id,), rdf_types.principles_ns)
            g.set((parent, RDF.type, rdf_types.CriterioDeCalidad))
            g.set((target, rdf_types.criterio_tiene_descripcion, Literal(description)))
            g.set((target, rdf_types.extiende_de_criterio, parent))
            g.set((target, rdf_types.extiende_de_criterio, parent_maturity_model))

    posi = URIRef("#criterio_de_calidad/posi", rdf_types.principles_ns)
    for (target_id, category, description, importance, parents) in cts.metricas_posi:
        target = URIRef("#criterio_de_calidad/%s" % (target_id,), rdf_types.principles_ns)
        g.set((target, RDF.type, rdf_types.CriterioDeCalidad))

        # ToDo: Falta decir que criterio_de_calidad tiene ese grupo_de_criterio
        grupo_de_criterio = URIRef("#grupo_de_criterio/%s" % (category,), rdf_types.principles_ns)
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
    internacional = URIRef("#locacion/global", rdf_types.my_ns)
    cys.append(internacional)
    g.set((internacional, RDF.type, rdf_types.Locacion))
    for country_or_block in cts.countries:
        if len(country_or_block) >= 3:
            bl = URIRef("#locacion/%s" % (country_or_block[0],), rdf_types.my_ns)
            cys.append(bl)
            g.set((bl, RDF.type, rdf_types.Locacion))
            g.set((bl, rdf_types.nombre_de_locacion, Literal(country_or_block[1])))
            g.set((bl, rdf_types.incluido_en, internacional))
            for country in country_or_block[2]:
                cy = URIRef("#pais/%s" % (country[0],), rdf_types.my_ns)
                cys.append(cy)
                g.set((cy, RDF.type, rdf_types.Pais))
                g.set((cy, rdf_types.incluido_en, bl))
                g.set((cy, rdf_types.alfa_3_de_pais, Literal(country[0])))
                g.set((cy, rdf_types.nombre_de_locacion, Literal(country[1])))
        else:
            cy = URIRef("#pais/%s" % (country_or_block[0],), rdf_types.my_ns)
            cys.append(cy)
            g.set((cy, RDF.type, rdf_types.Pais))
            g.set((cy, rdf_types.incluido_en, internacional))
            g.set((cy, rdf_types.alfa_3_de_pais, Literal(country_or_block[0])))
            g.set((cy, rdf_types.nombre_de_locacion, Literal(country_or_block[1])))
    owl_all_different(g, cys)
    return (g,)


if __name__ == '__main__':
    refine_and_insert_on_rdf()
    insert_on_rdf()
