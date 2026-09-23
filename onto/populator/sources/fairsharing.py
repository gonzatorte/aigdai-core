import re
from rdflib import Graph, Literal
from rdflib.namespace import RDF, XSD
import onto.populator.common as common
from onto.populator.utils import owl_all_different
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
            licence = rdf_types.Licencia.child_uri_ref(licencia['id'])
            all_items.append(licence)
            self.gg.add((licence, rdf_types.tiene_nombre_licencia, Literal(licencia['name'], datatype=XSD.string)))
            self.gg.add((licence, rdf_types.tiene_url_licencia, Literal(licencia['url'])))
        owl_all_different(self.gg, all_items)

    def process_keywords(self, user_defined_tags: list):
        all_items = []
        for user_defined_tag in user_defined_tags:
            palabra_clave = rdf_types.PalabraClave.child_uri_ref(user_defined_tag['id'])
            all_items.append(palabra_clave)
            self.gg.add((palabra_clave, rdf_types.tiene_sinonimo_palabra_clave, Literal(user_defined_tag['label'], datatype=XSD.string)))
            # ToDo: It is not capturing the definitions attribute
            # for definition in user_defined_tag['definitions']:
            #     if palabra_clave != 'N/A':
            #         self.gg.add((palabra_clave, rdf_types.definicion_de, Literal(definition)))
            for synonym in user_defined_tag['synonyms']:
                if synonym != 'N/A':
                    self.gg.add((palabra_clave, rdf_types.tiene_sinonimo_palabra_clave, Literal(synonym, datatype=XSD.string)))
        owl_all_different(self.gg, all_items)

    def process_subjects(self, infos: list):
        gg = self.gg
        all_disciplinas = []
        for info in infos:
            # ToDo: Give it a good id, maybe the iri attribute itself?
            disciplina = rdf_types.Disciplina.child_uri_ref(info['id'])
            all_disciplinas.append(disciplina)
            gg.add((disciplina, RDF.type, rdf_types.Disciplina))

            gg.add((disciplina, rdf_types.nombre_de_disciplina, Literal(info['label'], datatype=XSD.string)))
            # ToDo: Use the "definitions" field, which is an array of str
            # ToDo: Assign the appropriate scheme
            gg.add((disciplina, rdf_types.disciplina_tiene_esquema, Literal('dfg', datatype=XSD.string)))
            for synonym in info['synonyms']:
                gg.add((disciplina, rdf_types.nombre_de_disciplina, Literal(synonym, datatype=XSD.string)))
            for parent in info['parents']:
                parent_g = rdf_types.Disciplina.child_uri_ref(parent['id'])
                gg.add((disciplina, rdf_types.es_sub_disciplina_de, parent_g))
        owl_all_different(gg, all_disciplinas)

    def process_orgs(self, orgs: list):
        gg = self.gg
        all_orgs = []
        for info in orgs:
            org = rdf_types.Organizacion.child_uri_ref(info['id'])
            gg.add((org, RDF.type, rdf_types.Organizacion))

            gg.add((org, rdf_types.tiene_nombre_organizacion, Literal(info['name'].replace('@', ''), lang=ENG_LNG_CODE)))
            for instName in info['alternativeNames']:
                gg.add((org, rdf_types.tiene_nombre_organizacion, Literal(instName.replace('@', ''), lang=ENG_LNG_CODE)))
            for organisationType in info['organisationTypes']:
                gg.add((org, rdf_types.tiene_tipo_de_organizacion, Literal(
                    self.remap_institution_type(organisationType['id'], organisationType['name']),
                    datatype=rdf_types.TipoDeOrganizacion
                )))

            if info['rorLink']:
                idd_match = re.match('^https://ror\.org/(?P<idd>.+)$', info['rorLink'], re.IGNORECASE)
                if not idd_match:
                    raise Exception()
                idd_org = idd_match.groupdict()['idd']
                # ToDo: Do the ror namespace properly: use some prefix and make sure it cannot be used by another IdDeOrganizacion
                id_de_organizacion = rdf_types.IdDeOrganizacion.child_uri_ref("ror-%s" % (idd_org,))
                gg.add((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                gg.add((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, common.ror_id_schema))
                gg.add((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(idd_org, datatype=XSD.string)))
                gg.add((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, org))
        owl_all_different(gg, all_orgs)

    def process_repository(self, info, reduced: bool=False):
        gg = self.gg
        repositorio = rdf_types.Repositorio.child_uri_ref(info['_id'])
        repository_metadata = info['metadata']
        gg.add((repositorio, RDF.type, rdf_types.Repositorio))
        gg.add(
            (repositorio, rdf_types.tiene_nombre_repositorio, Literal(repository_metadata['name'].replace('@', ''), lang=ENG_LNG_CODE)))
        if repository_metadata['abbreviation']:
            gg.add((repositorio, rdf_types.tiene_nombre_repositorio,
                    Literal(repository_metadata['abbreviation'].replace('@', ''), lang=ENG_LNG_CODE)))
        gg.add((repositorio, rdf_types.tiene_descripcion_repositorio,
                Literal(repository_metadata['description'].replace('@', ''), lang=ENG_LNG_CODE)))
        gg.add((repositorio, rdf_types.tiene_url_repositorio, Literal(repository_metadata['homepage'])))
        if info['type'] == "knowledgebase":
            gg.add((repositorio, RDF.type, rdf_types.Agregador))
        elif info['type'] == "repository":
            gg.add((repositorio, RDF.type, rdf_types.Rdd))
        elif info['type'] == "knowledgebase_and_repository":
            gg.add((repositorio, RDF.type, rdf_types.Rdd))
            gg.add((repositorio, RDF.type, rdf_types.Agregador))
        else:
            raise Exception()
        # ToDo: No relations between repo and country defined at onto
        # info['countries']
        for subject in info['subjects']:
            # ToDo: Give it a good id, maybe the iri attribute itself?
            disciplina = rdf_types.Disciplina.child_uri_ref(subject['id'])
            gg.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))
        for organisationLink in info['organisationLinks']:
            org = rdf_types.Organizacion.child_uri_ref(organisationLink['organisation']['id'])
            responsibility_type = self.remap_institution_relation_type(organisationLink['relation'])
            relacion_repositorio_y_organizacion = rdf_types.RelacionRepositorioYOrganizacion.child_uri_ref("%s-%s-%s" % (organisationLink['organisation']['id'], info['id'],responsibility_type))
            gg.add((relacion_repositorio_y_organizacion, RDF.type, rdf_types.RelacionRepositorioYOrganizacion))
            gg.add((
                   relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_repositorio,
                   repositorio))
            gg.add((relacion_repositorio_y_organizacion,
                    rdf_types.relacion_repositorio_y_organizacion_tiene_organizacion, org))
            gg.add((relacion_repositorio_y_organizacion, rdf_types.tiene_tipo_de_relacion_con_organizacion, Literal(
                responsibility_type,
                datatype=rdf_types.TipoDeRelacionConOrganizacion
            )))
            # ToDo: The relation with the grant is missing
            # organisationLink['grant']
        for object_type in info['objectTypes']:
            # ToDo: Handle other, give it an other_id
            # ToDo: Unify enumerated values or declare same-as
            normal_content_type = self.remap_tipo_de_datos(object_type['id'])
            tipo_de_dato = rdf_types.TipoDeDato.child_uri_ref(normal_content_type)
            gg.add((tipo_de_dato, RDF.type, rdf_types.TipoDeDato))
            gg.add((repositorio, rdf_types.repositorio_acepta_tipo_de_contenido, tipo_de_dato))

        if not reduced:
            for user_defined_tag in info['userDefinedTags']:
                palabra_clave = rdf_types.PalabraClave.child_uri_ref(user_defined_tag['id'])
                gg.add((repositorio, rdf_types.tiene_palabra_clave_repositorio, palabra_clave))

        id_repo = rdf_types.IdDeRepositorio.child_uri_ref(info['id'])
        gg.add((id_repo, RDF.type, rdf_types.IdDeRepositorio))
        gg.add((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
        gg.add((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(info['id'], datatype=XSD.string)))
        gg.add((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, common.CatalogoFAIRSharing))

        for cross_reference in repository_metadata.get('cross_references', []):
            if cross_reference['portal'] == 'Other':
                continue
            elif cross_reference['portal'] == 'BioPortal':
                continue
            elif cross_reference['portal'] == 're3data':
                catalog = common.CatalogoRe3Data
                prefix = 're3data'
                id_match = re.match('^https://www\.re3data\.org/repository/(.+)$', cross_reference['url'])
                if not id_match:
                    print('warning: unrecognized id format', cross_reference['url'])
                    continue
                id_de_repo = id_match.groups()[0]
            elif cross_reference['portal'] == 'SciCrunch':
                catalog = common.CatalogoSciCrunch
                prefix = 'scicrunch'
                id_match = re.match('^https://scicrunch\.org/resolver/RRID:(.+)$', cross_reference['url'])
                if not id_match:
                    print('warning: unrecognized id format', cross_reference['url'])
                    continue
                id_de_repo = id_match.groups()[0]
            else:
                raise Exception()
            id_repo = rdf_types.IdDeRepositorio.child_uri_ref("%s-%s" % (prefix, id_de_repo,))
            gg.add((id_repo, RDF.type, rdf_types.IdDeRepositorio))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(id_de_repo, datatype=XSD.string)))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, catalog))

        if info['doi']:
            id_repo = rdf_types.IdDeRepositorio.child_uri_ref("doi-%s" % (info['doi'],))
            gg.add((id_repo, RDF.type, rdf_types.IdDeRepositorio))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(info['doi'], datatype=XSD.string)))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, common.CatalogoDoi))

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
                if record_association['recordAssocLabel'] == 'shares_data_with':
                    linked_to_repo = rdf_types.Repositorio.child_uri_ref(linked_to)
                    aggregator_2 = None
                    aggregated_2 = None
                    if info['type'] == "knowledgebase":
                        aggregator = repositorio
                        aggregated = linked_to_repo
                    elif info['type'] == "repository":
                        aggregator = linked_to_repo
                        aggregated = repositorio
                    elif info['type'] == "knowledgebase_and_repository":
                        aggregator = linked_to_repo
                        aggregated = repositorio
                        aggregator_2 = repositorio
                        aggregated_2 = linked_to_repo
                    else:
                        raise Exception()
                    gg.add((aggregated, rdf_types.repositorio_es_cosechado_por_agregador, aggregator))
                    if aggregator_2 and aggregated_2:
                        gg.add((aggregated_2, rdf_types.repositorio_es_cosechado_por_agregador, aggregator_2))
            elif record_association['recordAssocLabel'] in ['accepts', 'implements', 'outputs']:
                pass
            else:
                raise Exception()

        for licence_link in info['licenceLinks']:
            licence = rdf_types.Licencia.child_uri_ref(licence_link['licence']['id'])
            if licence_link['relation'] == 'applies_to_content':
                gg.add((repositorio, rdf_types.repositorio_permite_licencia, licence))
            else:
                gg.add((repositorio, rdf_types.repositorio_relacionado_con_licencia, licence))

        # "_id" : "ready"
        # "_id" : "deprecated"
        # "_id" : "in_development"
        # "_id" : "uncertain"
        if info['status'] == 'ready':
            gg.add((repositorio, rdf_types.repositorio_esta_activo, Literal(True, datatype=XSD.boolean)))

    def process_registry(self, info, reduced: bool=False):
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
            self.process_repository(info, reduced)
        elif info['registry'] == "Collection":
            pass
        elif info['registry'] == "FAIRassist":
            pass
        else:
            raise Exception("registry type %s unknown" % (info['registry'],))
