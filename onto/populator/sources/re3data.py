import re
import onto.populator.common as common
from onto.populator.utils import owl_all_different, find_or_fail
from re3data.extract_from_repo import BLACKLIST
import onto.cts as cts
import onto.populator.rdf_types as rdf_types
from re3data.xsd_transform import refine_repository_info, load_schema
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF
import hashlib


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


# RE3DATA_ORG_ID_SCHEMA_NAMES = [x[0] for x in common.ORG_ID_SCHEMAS]


def process(g_repos, repository_info):
    repositorio = URIRef("%s/%s" % (rdf_types.Repositorio.toPython(), repository_info['id'], ), rdf_types.my_ns)
    g_repos.set((repositorio, RDF.type, rdf_types.Repositorio))
    g_repos.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(repository_info['repositoryName']['text'], lang=repository_info['repositoryName']['lang'])))
    g_repos.set((repositorio, rdf_types.tiene_descripcion_repositorio, Literal(repository_info['description']['text'], lang=repository_info['description']['lang'])))
    g_repos.set((repositorio, rdf_types.tiene_url_repositorio, Literal(repository_info['repositoryURL'])))
    if repository_info['isDataProvider']:
        g_repos.set((repositorio, RDF.type, rdf_types.Rdd))
    if repository_info['isServiceProvider']:
        g_repos.set((repositorio, RDF.type, rdf_types.Agregador))

    for db_instance in repository_info['institutions']:
        id_org = db_instance['id'].replace(' ', '')
        r_instance = URIRef("%s/%s" % (rdf_types.Organizacion.toPython(), id_org,), rdf_types.my_ns)
        g_repos.set((r_instance, RDF.type, rdf_types.Organizacion))

        g_repos.set((r_instance, rdf_types.tiene_nombre_organizacion, Literal(db_instance['institutionName']['text'], lang=db_instance['institutionName']['lang'])))
        for instName in db_instance['institutionAdditionalNames']:
            g_repos.set((r_instance, rdf_types.tiene_nombre_organizacion, Literal(instName['text'], lang=instName['lang'])))

        if db_instance['institutionCountry'] == 'EEC':
            location = URIRef("%s/%s" % (rdf_types.Locacion, 'UE',), rdf_types.my_ns)
            g_repos.set((location, RDF.type, rdf_types.Locacion))
        elif db_instance['institutionCountry'] == 'AAA':
            location = common.locacion_internacional
            g_repos.set((location, RDF.type, rdf_types.Locacion))
        else:
            location = URIRef("%s/%s" % (rdf_types.Pais.toPython(), db_instance['institutionCountry'],), rdf_types.my_ns)
            g_repos.set((location, RDF.type, rdf_types.Pais))
        g_repos.set((r_instance, rdf_types.se_ubica_en, location))

        g_repos.add((r_instance, rdf_types.tiene_tipo_de_organizacion, Literal(
            remap_institution_type(db_instance['institutionType'])
        )))

        for raw_idd_org in db_instance['ids']:
            idd_org = raw_idd_org.replace(' ', '')
            idd_match = re.match('^(?P<type>.+(?=[:;.])|CrossrefFunderID)(?P<idd>.+)$', idd_org, re.IGNORECASE)
            if not idd_match:
                print(idd_org, raw_idd_org)
                continue
            tipo_de_id_de_organizacion_str = idd_match.groupdict().get('type').upper()
            tipo_de_id_de_organizacion = find_or_fail(
                lambda x: x[0] == tipo_de_id_de_organizacion_str,
                common.ORG_ID_SCHEMAS,
                lambda x: Exception("Unrecognized %s org id schema" % (tipo_de_id_de_organizacion_str,))
            )[2]
            idd_org_wo_schema = idd_match.groupdict().get('idd').replace(' ', '')
            id_de_organizacion = URIRef("%s/%s" % (rdf_types.IdDeOrganizacion.toPython(), idd_org,), rdf_types.my_ns)
            g_repos.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
            # ToDo: tipo_de_id_de_organizacion puede ser ROR, RRID, LOCAL y que otro?
            #  new Set(db.drepo.aggregate([{$project: {'institutions': 1}}, {$unwind: '$institutions'},{$project: {'institutions.id': 1}}]).toArray().map(a => a.institutions.id.replace(' ', ':').split(/[:.;]/)[0]))
            g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion))
            g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(idd_org_wo_schema)))
            g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, r_instance))

        inicio_periodo_de_relacion_con_organizacion = db_instance.get('responsibilityTypes', None)
        fin_periodo_de_relacion_con_organizacion = db_instance.get('responsibilityTypes', None)
        for responsibilityType in db_instance.get('responsibilityTypes', []):
            relacion_repositorio_y_organizacion = URIRef("%s/%s-%s-%s" % (rdf_types.RelacionRepositorioYOrganizacion.toPython(), id_org, repository_info['id'], responsibilityType), rdf_types.my_ns)
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
        software = URIRef("%s/%s" % (rdf_types.Software.toPython(), software_name, ), rdf_types.my_ns)
        g_repos.set((software, RDF.type, rdf_types.Software))
        # ToDo: Tendria que decir que todos los motores recabados por re3data con nombres diferentes son diferentes efectivamente?
        #  justo con other_algo no pasa eso. other_1 es diferente a ckan, a dataverse, etc... pero no es diferente a other_2...
        g_repos.set((repositorio, rdf_types.repositorio_asociado_a_software, software))

    for api in repository_info['apis']:
        api_type = api['type']
        if api_type == 'other':
            api_type = "other_%s" % (repository_info['id'],)
        api_para_cosecha = URIRef("%s/%s" % (rdf_types.ApiParaCosecha.toPython(), api_type, ), rdf_types.my_ns)
        g_repos.set((api_para_cosecha, RDF.type, rdf_types.ApiParaCosecha))
        # Should be inferred
        # g_repos.set((api_para_cosecha, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        api_para_cosecha_con_url = URIRef("%s/%s" % (rdf_types.ApiParaCosechaConUrl.toPython(), api['url'], ), rdf_types.my_ns)
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
        esquema_de_metadatos = URIRef("%s/%s" % (rdf_types.EsquemaDeMetadatos.toPython(), metadata_standard_name.lower().replace(' ', '_'), ), rdf_types.my_ns)
        g_repos.set((esquema_de_metadatos, RDF.type, rdf_types.EsquemaDeMetadatos))
        g_repos.set((esquema_de_metadatos, rdf_types.repositorio_aporta_funcionalidad, repositorio))

    for aid_system in repository_info['aidSystems']:
        if aid_system == 'other':
            aid_system = "other_%s" % (repository_info['id'],)
        # ToDo: Unificar enumerados o declarar same-as
        esquema_de_id_de_autor = URIRef("%s/%s" % (rdf_types.EsquemaDeIdDeAutor.toPython(), aid_system, ), rdf_types.my_ns)
        g_repos.set((esquema_de_id_de_autor, RDF.type, rdf_types.EsquemaDeIdDeAutor))
        g_repos.set((esquema_de_id_de_autor, rdf_types.repositorio_aporta_funcionalidad, repositorio))

    for pid_system in repository_info['pidSystems']:
        if pid_system == 'other':
            pid_system = "other_%s" % (repository_info['id'],)
        # ToDo: Unificar enumerados o declarar same-as
        esquema_de_id_persistente = URIRef("%s/%s" % (rdf_types.EsquemaDeIdPersistente.toPython(), pid_system, ), rdf_types.my_ns)
        g_repos.set((esquema_de_id_persistente, RDF.type, rdf_types.EsquemaDeIdPersistente))
        g_repos.set((esquema_de_id_persistente, rdf_types.repositorio_aporta_funcionalidad, repositorio))

    for content_type in repository_info['contentType']:
        # ToDo: Manejar other, ponerle other_id
        # ToDo: Unificar enumerados o declarar same-as
        tipo_de_dato = URIRef("%s/%s" % (rdf_types.TipoDeDato.toPython(), content_type.lower().replace(' ', '_'), ), rdf_types.my_ns)
        g_repos.set((tipo_de_dato, RDF.type, rdf_types.TipoDeDato))
        g_repos.set((tipo_de_dato, rdf_types.repositorio_aporta_funcionalidad, repositorio))

    # for quality_management in repository_info['qualityManagement']:
    #     # ToDo: Revisar si es un ObjectProperty, y si modelarlo como bool
    #     servicio_de_curaduria = URIRef("servicio_de_curaduria/%s" % (quality_management, ), rdf_types.my_ns)
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
        politica = URIRef("%s/%s" % (rdf_types.Politica.toPython(), local_id_politica, ), rdf_types.my_ns)
        # ToDo: Revisar si es un ObjectProperty
        g_repos.set((politica, RDF.type, rdf_types.Politica))
        g_repos.set((politica, rdf_types.repositorio_aporta_funcionalidad, repositorio))
        g_repos.set((politica, rdf_types.tiene_nombre_politica, Literal(policy['name'])))
        g_repos.set((politica, rdf_types.tiene_url_politica, Literal(policy['url'])))

    for data_license in repository_info['dataLicenses']:
        local_id_data_license = hashlib.md5(data_license['url'].encode('utf-8')).hexdigest()
        licencia_data = URIRef("%s/%s" % (rdf_types.Licencia.toPython(), local_id_data_license, ), rdf_types.my_ns)
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
        disciplina = URIRef("%s/%s" % (rdf_types.Disciplina.toPython(), subject,), rdf_types.my_ns)
        g_repos.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))

def seed_disciplinas():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    # ToDo: DFG disciplina es una clase definida por todas las disciplinas DFG?
    all_dfg_disciplinas = []
    def tree_walk_disciplina(forest, parent):
        for tr in forest:
            disciplina = URIRef("%s/%s" % (rdf_types.Disciplina.toPython(), tr[0],), rdf_types.my_ns)
            all_dfg_disciplinas.append(disciplina)
            g.set((disciplina, RDF.type, rdf_types.Disciplina))
            g.set((disciplina, rdf_types.nombre_de_disciplina, Literal(tr[1])))
            g.set((disciplina, rdf_types.esquema_de_disciplina, Literal('dfg')))

            if parent is not None:
                parent_g = URIRef("%s/%s" % (rdf_types.Disciplina.toPython(), parent,), rdf_types.my_ns)
                g.set((disciplina, rdf_types.es_sub_disciplina_de, parent_g))
            if len(tr) >= 3:
                children = tr[2]
                tree_walk_disciplina(children, tr[0])
    tree_walk_disciplina(cts.dfg_subjects, None)
    owl_all_different(g, all_dfg_disciplinas)

    return (g,)


class Re3DataSource:
    #
    def organizations(self):
        # ToDo: Ver si retornar un iterador async o que sea un generator o algo asi
        pass
