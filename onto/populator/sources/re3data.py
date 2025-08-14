import re
import onto.populator.common as common
from onto.populator.utils import owl_all_different, find_or_fail
from re3data.extract_from_repo import BLACKLIST
import onto.cts as cts
import onto.populator.rdf_types as rdf_types
from re3data.xsd_transform import refine_repository_info, load_schema
from rdflib import Graph, Literal
from rdflib.namespace import RDF
import hashlib


class Re3DataSource:
    def __init__(self, gg: Graph):
        self.gg = gg

    def remap_tipo_de_datos(self, tipo_de_dato: str):
        return tipo_de_dato.lower().replace(' ', '_')

    def remap_institution_type(self, institution_type: str):
        if institution_type == '':
            return 'archive'
        if institution_type == 'commercial':
            return 'comercial'
        if institution_type == '':
            return 'company'
        if institution_type == '':
            return 'education'
        if institution_type == '':
            return 'facility'
        if institution_type == '':
            return 'funder'
        if institution_type == '':
            return 'government'
        if institution_type == '':
            return 'healthcare'
        if institution_type == '':
            return 'no-comercial'
        if institution_type == 'non-profit':
            return 'nonprofit'
        if institution_type == '':
            return 'other'
        raise Exception()

    def remap_institution_relation_type(self, relation_type: str):
        if relation_type == 'sponsoring':
            return 'patrocinio'
        elif relation_type == 'general':
            return 'general'
        elif relation_type == 'funding':
            return 'financiamiento'
        elif relation_type == 'technical':
            return 'tecnica'
        raise Exception()

    def refine_iterator(self, iterator):
        schema = load_schema()
        refined = []
        for x in iterator:
            if x['idd'] in BLACKLIST:
                continue
            rrr = refine_repository_info(schema, x['bin'])
            refined.append(rrr)
        return refined

    def process(self, repository_info):
        g_repos = self.gg
        repositorio = rdf_types.Repositorio.child_uri_ref(repository_info['id'])
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
            r_instance = rdf_types.Organizacion.child_uri_ref(id_org)
            g_repos.set((r_instance, RDF.type, rdf_types.Organizacion))

            g_repos.set((r_instance, rdf_types.tiene_nombre_organizacion, Literal(db_instance['institutionName']['text'], lang=db_instance['institutionName']['lang'])))
            for instName in db_instance['institutionAdditionalNames']:
                g_repos.set((r_instance, rdf_types.tiene_nombre_organizacion, Literal(instName['text'], lang=instName['lang'])))

            if db_instance['institutionCountry'] == 'EEC':
                # ToDo: Usar de commons
                location = rdf_types.Locacion.child_uri_ref('UE')
                g_repos.set((location, RDF.type, rdf_types.Locacion))
            elif db_instance['institutionCountry'] == 'AAA':
                location = common.locacion_internacional
                g_repos.set((location, RDF.type, rdf_types.Locacion))
            else:
                location = rdf_types.Pais.child_uri_ref(db_instance['institutionCountry'])
                g_repos.set((location, RDF.type, rdf_types.Pais))
            g_repos.set((r_instance, rdf_types.organizacion_se_ubica_en, location))

            g_repos.add((r_instance, rdf_types.tiene_tipo_de_organizacion, Literal(
                self.remap_institution_type(db_instance['institutionType'])
            )))

            for raw_idd_org in db_instance['ids']:
                idd_org = raw_idd_org.replace(' ', '')
                idd_type_is_other = re.match('^other:.*$', idd_org, re.IGNORECASE)
                if idd_type_is_other:
                    print(idd_org, raw_idd_org)
                    continue
                # idd_match = re.match('^(?<!other)(?P<type>.+(?=[:;.])|CrossrefFunderID)(?P<idd>.+)$', idd_org, re.IGNORECASE)
                idd_match = re.match('^(?P<type>.+(?=[:;.])|CrossrefFunderID)(?P<idd>.+)$', idd_org, re.IGNORECASE)
                if not idd_match:
                    print(idd_org, raw_idd_org)
                    continue
                tipo_de_id_de_organizacion_str = idd_match.groupdict().get('type').upper()
                try:
                    tipo_de_id_de_organizacion = find_or_fail(
                        common.ORG_ID_SCHEMAS,
                        lambda x: tipo_de_id_de_organizacion_str in [tt.upper() for tt in x[1]]
                    )[2]
                except KeyError:
                    print("Unrecognized %s org id schema for %s" % (tipo_de_id_de_organizacion_str, idd_org))
                    continue
                idd_org_wo_schema = idd_match.groupdict().get('idd').replace(' ', '')
                id_de_organizacion = rdf_types.IdDeOrganizacion.child_uri_ref(idd_org)
                g_repos.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                # ToDo: tipo_de_id_de_organizacion puede ser ROR, RRID, LOCAL y que otro?
                #  new Set(db.drepo.aggregate([{$project: {'institutions': 1}}, {$unwind: '$institutions'},{$project: {'institutions.id': 1}}]).toArray().map(a => a.institutions.id.replace(' ', ':').split(/[:.;]/)[0]))
                g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion))
                g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(idd_org_wo_schema)))
                g_repos.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, r_instance))

            # ToDo: Aca esta buscando la clave equivocada, responsibilityTypes en vez de inicio de periodo
            inicio_periodo_de_relacion_con_organizacion = db_instance.get('responsibilityTypes', None)
            fin_periodo_de_relacion_con_organizacion = db_instance.get('responsibilityTypes', None)
            for responsibilityType in db_instance.get('responsibilityTypes', []):
                relacion_repositorio_y_organizacion = rdf_types.RelacionRepositorioYOrganizacion.child_uri_ref("%s-%s-%s" % (id_org, repository_info['id'], responsibilityType))
                g_repos.set((relacion_repositorio_y_organizacion, RDF.type, rdf_types.RelacionRepositorioYOrganizacion))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_repositorio, repositorio))
                g_repos.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_organizacion, r_instance))
                if inicio_periodo_de_relacion_con_organizacion:
                    g_repos.set((relacion_repositorio_y_organizacion, rdf_types.tiene_inicio_periodo_de_relacion_con_organizacion, Literal(inicio_periodo_de_relacion_con_organizacion)))
                if fin_periodo_de_relacion_con_organizacion:
                    g_repos.set((relacion_repositorio_y_organizacion, rdf_types.tiene_fin_periodo_de_relacion_con_organizacion, Literal(fin_periodo_de_relacion_con_organizacion)))
                if responsibilityType:
                    g_repos.set((relacion_repositorio_y_organizacion, rdf_types.tiene_tipo_de_relacion_con_organizacion, Literal(
                        self.remap_institution_relation_type(responsibilityType)
                    )))

        software_names = [x for x in repository_info['softwareNames'] if x != 'unknown']
        software_name = software_names[0] if len(software_names) >= 1 else None
        if software_name == 'other':
            software_name = "other_%s" % (repository_info['id'],)
        if software_name is not None:
            software = rdf_types.Software.child_uri_ref(software_name)
            g_repos.set((software, RDF.type, rdf_types.Software))
            # ToDo: Tendria que decir que todos los motores recabados por re3data con nombres diferentes son diferentes efectivamente?
            #  justo con other_algo no pasa eso. other_1 es diferente a ckan, a dataverse, etc... pero no es diferente a other_2...
            g_repos.set((repositorio, rdf_types.repositorio_asociado_a_software, software))

        for api in repository_info['apis']:
            api_type = api['type']
            if api_type == 'other':
                api_type = "other_%s" % (repository_info['id'],)
            # ToDo: Unificar con commons
            api_para_cosecha = rdf_types.ProtocoloDeCosecha.child_uri_ref(api_type)
            g_repos.set((api_para_cosecha, RDF.type, rdf_types.ProtocoloDeCosecha))
            # ToDo: Should be inferred
            # g_repos.set((api_para_cosecha, rdf_types.repositorio_aporta_funcionalidad, repositorio))

            # ToDo: Habilitar de nuevo
            # api_para_cosecha_con_url = URIRef("%s/%s" % (rdf_types.ApiParaCosechaConUrl.toPython(), api['url'], ), rdf_types.my_ns)
            # g_repos.set((api_para_cosecha_con_url, RDF.type, rdf_types.ApiParaCosechaConUrl))
            # g_repos.set((api_para_cosecha_con_url, rdf_types.api_para_cosecha_con_url_tiene_url, Literal(api['url'])))
            # g_repos.set((api_para_cosecha_con_url, rdf_types.api_para_cosecha_con_url_tiene_api_para_cosecha, api_para_cosecha))
            # g_repos.set((api_para_cosecha_con_url, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for metadata_standard in repository_info['metadataStandards']:
            # ToDo: Poner modelo intermedio con evidencia
            metadata_standard_name = metadata_standard['name']
            if metadata_standard_name == 'other':
                metadata_standard_name = "other_%s" % (repository_info['id'],)
            # ToDo: Unificar enumerados o declarar same-as
            esquema_de_metadatos = rdf_types.EsquemaDeMetadatos.child_uri_ref(metadata_standard_name)
            g_repos.set((esquema_de_metadatos, RDF.type, rdf_types.EsquemaDeMetadatos))
            g_repos.set((esquema_de_metadatos, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for aid_system in repository_info['aidSystems']:
            if aid_system == 'other':
                aid_system = "other_%s" % (repository_info['id'],)
            # ToDo: Unificar enumerados o declarar same-as
            esquema_de_id_de_autor = rdf_types.EsquemaDeIdDeAutor.child_uri_ref(aid_system)
            g_repos.set((esquema_de_id_de_autor, RDF.type, rdf_types.EsquemaDeIdDeAutor))
            g_repos.set((esquema_de_id_de_autor, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for pid_system in repository_info['pidSystems']:
            if pid_system == 'other':
                pid_system = "other_%s" % (repository_info['id'],)
            # ToDo: Unificar enumerados o declarar same-as
            esquema_de_id_persistente = rdf_types.EsquemaDeIdPersistente.child_uri_ref(pid_system)
            g_repos.set((esquema_de_id_persistente, RDF.type, rdf_types.EsquemaDeIdPersistente))
            g_repos.set((esquema_de_id_persistente, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for content_type in repository_info['contentType']:
            # ToDo: Manejar other, ponerle other_id
            # ToDo: Unificar enumerados o declarar same-as
            normal_content_type = self.remap_tipo_de_datos(content_type)
            tipo_de_dato = rdf_types.TipoDeDato.child_uri_ref(normal_content_type)
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
            politica = rdf_types.Politica.child_uri_ref(local_id_politica)
            # ToDo: Revisar si es un ObjectProperty
            g_repos.set((politica, RDF.type, rdf_types.Politica))
            g_repos.set((politica, rdf_types.repositorio_aporta_funcionalidad, repositorio))
            g_repos.set((politica, rdf_types.tiene_nombre_politica, Literal(policy['name'])))
            g_repos.set((politica, rdf_types.tiene_url_politica, Literal(policy['url'])))

        for data_license in repository_info['dataLicenses']:
            local_id_data_license = hashlib.md5(data_license['url'].encode('utf-8')).hexdigest()
            # ToDo: Unificar
            licencia_data = rdf_types.Licencia.child_uri_ref(local_id_data_license)
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
            disciplina = rdf_types.Disciplina.child_uri_ref(subject)
            g_repos.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))


def seed_disciplinas():
    g = Graph()
    g.bind('', rdf_types.my_ns)

    # ToDo: DFG disciplina es una clase definida por todas las disciplinas DFG?
    all_dfg_disciplinas = []
    def tree_walk_disciplina(forest, parent):
        for tr in forest:
            disciplina = rdf_types.Disciplina.child_uri_ref(tr[0])
            all_dfg_disciplinas.append(disciplina)
            g.set((disciplina, RDF.type, rdf_types.Disciplina))
            g.set((disciplina, rdf_types.nombre_de_disciplina, Literal(tr[1])))
            g.set((disciplina, rdf_types.disciplina_tiene_esquema, Literal('dfg')))

            if parent is not None:
                parent_g = rdf_types.Disciplina.child_uri_ref(parent)
                g.set((disciplina, rdf_types.es_sub_disciplina_de, parent_g))
            if len(tr) >= 3:
                children = tr[2]
                tree_walk_disciplina(children, tr[0])
    tree_walk_disciplina(cts.dfg_subjects, None)
    owl_all_different(g, all_dfg_disciplinas)

    return (g,)
