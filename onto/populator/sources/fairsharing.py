import typing
import re
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
import onto.populator.common as common
from onto.populator.utils import owl_all_different, find_or_fail
import onto.cts as cts
import onto.populator.rdf_types as rdf_types


ENG_LNG_CODE = 'eng'


class FairSharingSource:
    def __init__(self, gg: Graph):
        self.gg = gg

    def remap_tipo_de_datos(self, id: int):
        return id

    def remap_institution_type(self, institution_type_id: int, institution_type: str):
        if institution_type == 'Company':
            return 'company'
        if institution_type == 'University':
            return 'education'
        if institution_type == 'Research institute':
            return 'facility'
        if institution_type == 'Government body':
            return 'government'
        if institution_type == 'Lab':
            return 'healthcare'
        if institution_type == 'Charitable foundation':
            return 'nonprofit'
        if institution_type == 'Consortium':
            return 'consortium'
        if institution_type == 'Publisher':
            return 'publisher'
        if institution_type == 'Undefined':
            return 'other'
        raise Exception()

    def remap_institution_relation_type(self, relation_type: str):
        if relation_type == 'undefined':
            return 'other'
        elif relation_type == 'funds':
            return 'financiamiento'
        elif relation_type == 'maintains':
            return 'técnica'
        elif relation_type == 'collaborates_on':
            return 'other'
        elif relation_type == 'associated_with':
            return 'other'
        raise Exception()

    def process_licencia(self, licencias: list):
        all_items = []
        for licencia in licencias:
            licence = URIRef(
                "%s/%s" % (rdf_types.Licencia.toPython(), licencia['id'],),
                rdf_types.my_ns)
            all_items.append(licence)
            self.gg.set((licence, rdf_types.tiene_nombre_licencia, Literal(licencia['name'])))
            self.gg.set((licence, rdf_types.tiene_url_licencia, Literal(licencia['url'])))
        owl_all_different(self.gg, all_items)

    def process_keywords(self, user_defined_tags: list):
        all_items = []
        for user_defined_tag in user_defined_tags:
            # ToDo: Hay que reemplzar caracateres raros para que quede una uri valida
            palabra_clave = URIRef(
                "%s/fs-%s" % (rdf_types.PalabraClave.toPython(), user_defined_tag['id'],),
                rdf_types.my_ns)
            all_items.append(palabra_clave)
            self.gg.set((palabra_clave, rdf_types.tiene_sinonimo_palabra_clave, Literal(user_defined_tag['label'])))
            # ToDo: No esta capturando el atributo definitions
            # for definition in user_defined_tag['definitions']:
            #     if palabra_clave != 'N/A':
            #         self.gg.set((palabra_clave, rdf_types.definicion_de, Literal(definition)))
            for synonym in user_defined_tag['synonyms']:
                if synonym != 'N/A':
                    self.gg.set((palabra_clave, rdf_types.tiene_sinonimo_palabra_clave, Literal(synonym)))
        owl_all_different(self.gg, all_items)

    def process_subjects(self, infos: list):
        gg = self.gg
        all_disciplinas = []
        for info in infos:
            # ToDo: Ponerle un id bueno, quizás el mismo atributo iri?
            disciplina = URIRef("%s/%s" % (rdf_types.Disciplina.toPython(), info['id'],), rdf_types.my_ns)
            all_disciplinas.append(disciplina)
            gg.set((disciplina, RDF.type, rdf_types.Disciplina))

            gg.set((disciplina, rdf_types.nombre_de_disciplina, Literal(info['label'])))
            # ToDo: Usar el campo "definitions" que es un array de str
            # ToDo: Ponerle el esquema que corresponda
            gg.set((disciplina, rdf_types.esquema_de_disciplina, Literal('dfg')))
            for synonym in info['synonyms']:
                gg.set((disciplina, rdf_types.nombre_de_disciplina, Literal(synonym)))
            for parent in info['parents']:
                parent_g = URIRef("%s/%s" % (rdf_types.Disciplina.toPython(), parent['id'],), rdf_types.my_ns)
                gg.set((disciplina, rdf_types.es_sub_disciplina_de, parent_g))
        owl_all_different(gg, all_disciplinas)

    def process_orgs(self, orgs: list):
        gg = self.gg
        all_orgs = []
        for info in orgs:
            org = URIRef("%s/%s" % (rdf_types.Organizacion.toPython(), info['id'],), rdf_types.my_ns)
            gg.set((org, RDF.type, rdf_types.Organizacion))

            gg.set((org, rdf_types.tiene_nombre_organizacion, Literal(info['name'], lang=ENG_LNG_CODE)))
            for instName in info['alternativeNames']:
                gg.set((org, rdf_types.tiene_nombre_organizacion, Literal(instName, lang=ENG_LNG_CODE)))
            for organisationType in info['organisationTypes']:
                gg.add((org, rdf_types.tiene_tipo_de_organizacion, Literal(
                    self.remap_institution_type(organisationType['id'], organisationType['name'])
                )))

            if info['rorLink']:
                idd_match = re.match('^https://ror\.org/(?P<idd>.+)$', info['rorLink'], re.IGNORECASE)
                if not idd_match:
                    raise Exception()
                idd_org = idd_match.groupdict()['idd']
                # ToDo: Hacer bien el espacio de nombres de ror, usar algun prefijo y asegurar que no pueda ser usado por otro IdDeOrganizacion
                id_de_organizacion = URIRef("%s/ror-%s" % (rdf_types.IdDeOrganizacion.toPython(), idd_org,), rdf_types.my_ns)
                gg.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                gg.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, common.ror_id_schema))
                gg.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(idd_org)))
                gg.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, org))
        owl_all_different(gg, all_orgs)

    def process_repository(self, info):
        gg = self.gg
        repositorio = URIRef("%s/%s" % (rdf_types.Repositorio.toPython(), info['_id'],), rdf_types.my_ns)
        repository_metadata = info['metadata']
        gg.set((repositorio, RDF.type, rdf_types.Repositorio))
        gg.set(
            (repositorio, rdf_types.tiene_nombre_repositorio, Literal(repository_metadata['name'], lang=ENG_LNG_CODE)))
        gg.set((repositorio, rdf_types.tiene_nombre_repositorio,
                Literal(repository_metadata['abbreviation'], lang=ENG_LNG_CODE)))
        gg.set((repositorio, rdf_types.tiene_descripcion_repositorio,
                Literal(repository_metadata['description'], lang=ENG_LNG_CODE)))
        gg.set((repositorio, rdf_types.tiene_url_repositorio, Literal(repository_metadata['homepage'])))
        if info['type'] == "knowledgebase":
            gg.set((repositorio, RDF.type, rdf_types.Agregador))
        elif info['type'] == "repository":
            gg.set((repositorio, RDF.type, rdf_types.Rdd))
        elif info['type'] == "knowledgebase_and_repository":
            gg.set((repositorio, RDF.type, rdf_types.Rdd))
            gg.set((repositorio, RDF.type, rdf_types.Agregador))
        else:
            raise Exception()
        # ToDo: No relations between repo and country defined at onto
        # info['countries']
        for subject in info['subjects']:
            # ToDo: Ponerle un id bueno, quizás el mismo atributo iri?
            disciplina = URIRef("%s/%s" % (rdf_types.Disciplina.toPython(), subject['id'],), rdf_types.my_ns)
            gg.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))
        for organisationLink in info['organisationLinks']:
            org = URIRef("%s/%s" % (rdf_types.Organizacion.toPython(), organisationLink['organisation']['id'],),
                         rdf_types.my_ns)
            responsibility_type = self.remap_institution_relation_type(organisationLink['relation'])
            relacion_repositorio_y_organizacion = URIRef("%s/%s-%s-%s" % (
            rdf_types.RelacionRepositorioYOrganizacion.toPython(), organisationLink['organisation']['id'], info['id'],
            responsibility_type), rdf_types.my_ns)
            gg.set((relacion_repositorio_y_organizacion, RDF.type, rdf_types.RelacionRepositorioYOrganizacion))
            gg.set((
                   relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_repositorio,
                   repositorio))
            gg.set((relacion_repositorio_y_organizacion,
                    rdf_types.relacion_repositorio_y_organizacion_tiene_organizacion, org))
            gg.set((relacion_repositorio_y_organizacion, rdf_types.tiene_tipo_de_relacion_con_organizacion, Literal(
                responsibility_type
            )))
            # ToDo: Falta la relacion con el grant
            # organisationLink['grant']
        for object_type in info['objectTypes']:
            # ToDo: Manejar other, ponerle other_id
            # ToDo: Unificar enumerados o declarar same-as
            normal_content_type = self.remap_tipo_de_datos(object_type['id'])
            tipo_de_dato = URIRef(
                "%s/%s" % (rdf_types.TipoDeDato.toPython(), normal_content_type,),
                rdf_types.my_ns)
            gg.set((tipo_de_dato, RDF.type, rdf_types.TipoDeDato))
            gg.set((tipo_de_dato, rdf_types.repositorio_aporta_funcionalidad, repositorio))

        for user_defined_tag in info['userDefinedTags']:
            palabra_clave = URIRef(
                "%s/%s" % (rdf_types.PalabraClave.toPython(), user_defined_tag['id'],),
                rdf_types.my_ns)
            gg.set((repositorio, rdf_types.tiene_palabra_clave_repositorio, palabra_clave))

        id_repo = URIRef("%s/fairsharing-%s" % (rdf_types.IdDeRepositorio.toPython(), info['id'],), rdf_types.my_ns)
        gg.set((id_repo, RDF.type, rdf_types.IdDeRepositorio))
        gg.set((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
        gg.set((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(info['id'])))
        gg.set((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, common.CatalogoFAIRSharing))

        for cross_reference in repository_metadata.get('cross_references', []):
            if cross_reference['portal'] == 'Other':
                continue
            elif cross_reference['portal'] == 'BioPortal':
                continue
            elif cross_reference['portal'] == 're3data':
                catalog = common.CatalogoRe3Data
                prefix = 're3data'
                id_de_repo = re.match('^https://www\.re3data\.org/repository/(.+)$', cross_reference['url']).groups()[0]
            elif cross_reference['portal'] == 'SciCrunch':
                catalog = common.CatalogoSciCrunch
                prefix = 'scicrunch'
                id_de_repo = re.match('^https://scicrunch\.org/resolver/RRID:(.+)$', cross_reference['url']).groups()[0]
            else:
                raise Exception()
            id_repo = URIRef("%s/%s-%s" % (rdf_types.IdDeRepositorio.toPython(), prefix, id_de_repo,), rdf_types.my_ns)
            gg.set((id_repo, RDF.type, rdf_types.IdDeRepositorio))
            gg.set((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
            gg.set((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(id_de_repo)))
            gg.set((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, catalog))

        if info['doi']:
            id_repo = URIRef("%s/doi-%s" % (rdf_types.IdDeRepositorio.toPython(), info['doi'],), rdf_types.my_ns)
            gg.set((id_repo, RDF.type, rdf_types.IdDeRepositorio))
            gg.set((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
            gg.set((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(info['doi'])))
            gg.set((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, common.CatalogoDoi))

        for record_association in info['recordAssociations']:
            # "extends" # to database
            # "shares_data_with" # to database
            # "shares_code_with" # to database
            # "deprecates" # to database, deprecated
            # "related_to" # to database, last_resort
            # "accepts" # to standard
            # "implements" # to standard
            # "outputs" # to standard
            linked_to = record_association['linkedRecord']['id']
            if record_association['recordAssocLabel'] in ['extends', 'shares_data_with', 'shares_code_with', 'deprecates', 'related_to']:
                pass
            elif record_association['recordAssocLabel'] in ['accepts', 'implements', 'outputs']:
                pass
            else:
                raise Exception()

        for licence_link in info['licenceLinks']:
            licence = URIRef(
                "%s/%s" % (rdf_types.Licencia.toPython(), licence_link['licence']['id'],),
                rdf_types.my_ns)
            if licence_link['relation'] == 'applies_to_content':
                gg.set((repositorio, rdf_types.repositorio_permite_licencia, licence))
            else:
                gg.set((repositorio, rdf_types.repositorio_relacionado_con_licencia, licence))

        # "_id" : "ready"
        # "_id" : "deprecated"
        # "_id" : "in_development"
        # "_id" : "uncertain"
        if info['status'] == 'ready':
            gg.set((repositorio, rdf_types.repositorio_esta_activo, Literal(True)))

    def process_registry(self, info):
        gg = self.gg
        if info['registry'] == "Standard":
            for record_association in info['recordAssociations']:
                # "part_of" # to standard (principle -> principle)
                # "profiles" # to standard
                # "extends" # to standard
                # "deprecates" # to standard, deprecated
                # "related_to" # to standard or database, last resort
                record_association['recordAssocLabel']
            if info['type'] == "principle":
                pass
            elif info['type'] == "reporting_guideline":
                pass
            elif info['type'] == "terminology_artefact":
                pass
            elif info['type'] == "identifier_schema":
                pass
            elif info['type'] == "model_and_format":
                pass
            else:
                raise Exception()
        elif info['registry'] == "Policy":
            for record_association in info['recordAssociations']:
                # "recommends" # to database, to standard
                # "extends" # to policy
                # "related_to" # to policy, last resort
                # "deprecates" # to policy, deprecated
                pass
            if info['type'] == "project":
                pass
            elif info['type'] == "funder":
                pass
            elif info['type'] == "institution":
                pass
            elif info['type'] == "journal_publisher":
                pass
            elif info['type'] == "journal":
                pass
            elif info['type'] == "society":
                pass
            else:
                raise Exception()
        elif info['registry'] == "Database":
            self.process_repository(info)
        elif info['registry'] == "Collection":
            pass
        elif info['registry'] == "FAIRassist":
            pass
        else:
            raise Exception("registry type %s unknown" % (info['registry'],))
