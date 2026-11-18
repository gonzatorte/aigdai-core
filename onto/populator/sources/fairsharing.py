import hashlib
import re
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD
import onto.populator.common as common
from onto.populator.utils import owl_all_different
import onto.populator.rdf_types as rdf_types
import onto.cts as cts


ENG_LNG_CODE = 'eng'


class FairSharingSource:
    def __init__(self, gg: Graph, records: dict = None):
        self.gg = gg
        # FAIRsharing id -> (registry, DOI) of every record, to resolve the targets of the record associations
        self.records = records or {}

    def record_iri(self, record_id) -> URIRef:
        # The IRI of a FAIRsharing record, the same that cts.fairsharing_de_enumerados uses: its DOI suffix when it
        # has one (https://fairsharing.org/FAIRsharing.xxxx), its numeric id otherwise
        (_, doi) = self.records.get(record_id, (None, None))
        return URIRef('https://fairsharing.org/%s' % (doi.split('/', 1)[1] if doi else record_id,))

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
            # Prefixed, like the identifiers of the other sources, so that a FAIRsharing id cannot take the IRI of another organization
            org = rdf_types.Organizacion.child_uri_ref('fairsharing-%s' % (info['id'],))
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
        # Prefixed with the source, like the records of the other sources (re3data ids already start with r3d)
        repositorio = rdf_types.Repositorio.child_uri_ref('fairsharing-%s' % (info['_id'],))
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
            org = rdf_types.Organizacion.child_uri_ref('fairsharing-%s' % (organisationLink['organisation']['id'],))
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

        id_repo = rdf_types.IdDeRepositorio.child_uri_ref('fairsharing-%s' % (info['id'],))
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
            common.add_doi_id(gg, info['doi'], repositorio)

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
                    linked_to_repo = rdf_types.Repositorio.child_uri_ref('fairsharing-%s' % (linked_to,))
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

        self.process_data_conditions(repositorio, info)

        # "_id" : "ready"
        # "_id" : "deprecated"
        # "_id" : "in_development"
        # "_id" : "uncertain"
        if info['status'] == 'ready':
            gg.add((repositorio, rdf_types.repositorio_esta_activo, Literal(True, datatype=XSD.boolean)))

        # The URL and the status again, keeping which catalog states them, so that they can be compared between catalogs
        url_en_catalogo = rdf_types.UrlEnCatalogo.child_uri_ref("fairsharing-%s" % (info['id'],))
        gg.add((url_en_catalogo, RDF.type, rdf_types.UrlEnCatalogo))
        gg.add((url_en_catalogo, rdf_types.metadato_en_catalogo_sobre_repositorio, repositorio))
        gg.add((url_en_catalogo, rdf_types.metadato_en_catalogo_emitido_por_catalogo, common.CatalogoFAIRSharing))
        gg.add((url_en_catalogo, rdf_types.url_en_catalogo_tiene_url, Literal(repository_metadata['homepage'])))
        # "in_development" and "uncertain" do not say whether it is active, so they state nothing
        if info['status'] in ('ready', 'deprecated'):
            estado_en_catalogo = rdf_types.EstadoEnCatalogo.child_uri_ref("fairsharing-%s" % (info['id'],))
            gg.add((estado_en_catalogo, RDF.type, rdf_types.EstadoEnCatalogo))
            gg.add((estado_en_catalogo, rdf_types.metadato_en_catalogo_sobre_repositorio, repositorio))
            gg.add((estado_en_catalogo, rdf_types.metadato_en_catalogo_emitido_por_catalogo, common.CatalogoFAIRSharing))
            gg.add((estado_en_catalogo, rdf_types.estado_en_catalogo_esta_activo, Literal(info['status'] == 'ready', datatype=XSD.boolean)))

    def process_data_conditions(self, repositorio, info):
        # Data access, processes, curation, deposition, versioning, documentation, preservation, sustainability and
        # certifications, from the metadata of the database record. "not found" and "not applicable" state nothing.
        gg = self.gg
        metadata = info['metadata']
        rid = info['id']

        for link in metadata.get('support_links') or []:
            if link.get('url') and link.get('type') in ('Help documentation', 'Frequently Asked Questions (FAQs)', 'Training documentation'):
                gg.add((repositorio, rdf_types.repositorio_tiene_documentacion, Literal(link['url'])))

        for badge in metadata.get('certifications_and_community_badges') or []:
            name = (badge.get('name') or '').lower()
            cert_id = next((cert for (text, cert) in cts.certificaciones_fairsharing if text in name), None)
            if cert_id is None:
                continue
            certificacion = common.certification_ref(cert_id)
            gg.add((certificacion, RDF.type, rdf_types.Certificacion))
            aplicacion_de_cert = rdf_types.AplicacionDeCertificacionARepositorio.child_uri_ref("fairsharing-%s-%s" % (rid, cert_id))
            gg.add((aplicacion_de_cert, RDF.type, rdf_types.AplicacionDeCertificacionARepositorio))
            gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_repositorio, repositorio))
            gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_certificacion, certificacion))
            # ToDo: Some names carry the validity period ("valid until 2025-02-17", "(2020-2026)"); it is not parsed

        # The access services and the evaluations (curation, deposition, preservation, sustainability) range over rdd:
        # only records typed rdd get them, so that a knowledgebase is not inferred to be a data repository.
        if info['type'] not in ('repository', 'knowledgebase_and_repository'):
            return

        access = metadata.get('data_access_condition') or {}
        nivel_de_acceso = None
        if access.get('type') in cts.niveles_de_acceso_fairsharing:
            nivel_de_acceso = rdf_types.NivelDeAcceso.child_uri_ref(access['type'])
            gg.add((nivel_de_acceso, RDF.type, rdf_types.NivelDeAcceso))
        processes = metadata.get('data_processes_and_conditions') or []
        if not processes and nivel_de_acceso is not None:
            processes = [{'type': 'read'}]
        for idx, process in enumerate(processes):
            servicio = rdf_types.ServicioDeAccesoADatos.child_uri_ref("fairsharing-%s-%s" % (rid, idx))
            gg.add((servicio, RDF.type, rdf_types.ServicioDeAccesoADatos))
            gg.add((servicio, rdf_types.servicio_de_acceso_a_datos_tiene_repositorio, repositorio))
            # The access condition is about reading the data
            if nivel_de_acceso is not None and process.get('type') in ('read', 'read and write'):
                gg.add((servicio, rdf_types.servicio_de_acceso_a_datos_tiene_nivel_de_acceso, nivel_de_acceso))
            if process.get('name'):
                gg.add((servicio, rdf_types.servicio_de_acceso_a_datos_tiene_nombre, Literal(process['name'], datatype=XSD.string)))
            if process.get('url'):
                gg.add((servicio, rdf_types.servicio_de_acceso_a_datos_tiene_direccion_de_entrada, Literal(process['url'])))
            documentacion = process.get('documentation_url') or access.get('url')
            if documentacion:
                gg.add((servicio, rdf_types.servicio_de_acceso_a_datos_tiene_documentacion, Literal(documentacion)))
            protocolo_id = cts.metodos_de_acceso_fairsharing.get(process.get('access_method'))
            if protocolo_id:
                protocolo = rdf_types.ProtocoloDeCosecha.child_uri_ref(protocolo_id)
                gg.add((protocolo, RDF.type, rdf_types.ProtocoloDeCosecha))
                gg.add((repositorio, rdf_types.soporta_protocolo_de_cosecha, protocolo))

        curation = (metadata.get('data_curation') or {}).get('type')
        if curation in cts.niveles_de_curaduria_fairsharing:
            nivel_de_curaduria = rdf_types.NivelDeCuraduria.child_uri_ref(curation.replace('/', '_'))
            gg.add((nivel_de_curaduria, RDF.type, rdf_types.NivelDeCuraduria))
            curaduria = rdf_types.AplicacionDeCuraduriaEnRepositorio.child_uri_ref("fairsharing-%s" % (rid,))
            gg.add((curaduria, RDF.type, rdf_types.AplicacionDeCuraduriaEnRepositorio))
            gg.add((curaduria, rdf_types.evaluacion_de_repositorio_tiene_repositorio, repositorio))
            gg.add((curaduria, rdf_types.aplicacion_de_curaduria_en_repositorio_tiene_nivel_de_curaduria, nivel_de_curaduria))

        deposit = (metadata.get('data_deposition_condition') or {}).get('type')
        if deposit in cts.niveles_de_deposito_fairsharing:
            nivel_de_deposito = rdf_types.NivelDeAperturaParaEscritura.child_uri_ref(deposit)
            gg.add((nivel_de_deposito, RDF.type, rdf_types.NivelDeAperturaParaEscritura))
            apertura = rdf_types.AperturaDeRepositorio.child_uri_ref("fairsharing-%s-deposito" % (rid,))
            gg.add((apertura, RDF.type, rdf_types.AperturaDeRepositorio))
            gg.add((apertura, rdf_types.evaluacion_de_repositorio_tiene_repositorio, repositorio))
            gg.add((apertura, rdf_types.apertura_de_repositorio_tiene_nivel_de_apertura, nivel_de_deposito))

        if metadata.get('data_versioning') in ('yes', 'no'):
            gg.add((repositorio, rdf_types.soporta_versionado_repositorio, Literal(metadata['data_versioning'] == 'yes', datatype=XSD.boolean)))

        preservation = metadata.get('data_preservation_policy') or {}
        if preservation.get('url'):
            politica = rdf_types.Politica.child_uri_ref(hashlib.md5(preservation['url'].encode('utf-8')).hexdigest())
            gg.add((politica, RDF.type, rdf_types.Politica))
            if preservation.get('name'):
                gg.add((politica, rdf_types.tiene_nombre_politica, Literal(preservation['name'], datatype=XSD.string)))
            gg.set((politica, rdf_types.tiene_url_politica, Literal(preservation['url'])))
            gg.add((repositorio, rdf_types.repositorio_usa_politica, politica))
            aplicacion = rdf_types.AplicacionDePoliticaDePreservacionEnRepositorio.child_uri_ref("fairsharing-%s" % (rid,))
            gg.add((aplicacion, RDF.type, rdf_types.AplicacionDePoliticaDePreservacionEnRepositorio))
            gg.add((aplicacion, rdf_types.evaluacion_de_repositorio_tiene_repositorio, repositorio))
            gg.add((aplicacion, rdf_types.aplicacion_de_politica_de_preservacion_en_repositorio_tiene_politica, politica))

        sustainability = metadata.get('resource_sustainability') or {}
        if sustainability.get('url'):
            sustentabilidad = rdf_types.SustentabilidadEnRepositorio.child_uri_ref("fairsharing-%s" % (rid,))
            gg.add((sustentabilidad, RDF.type, rdf_types.SustentabilidadEnRepositorio))
            gg.add((sustentabilidad, rdf_types.evaluacion_de_repositorio_tiene_repositorio, repositorio))
            gg.add((sustentabilidad, rdf_types.evaluacion_de_repositorio_tiene_url, Literal(sustainability['url'])))

    def process_policy(self, info):
        # A policy of a journal, publisher, funder, institution, project or society, and what it recommends. The
        # organisations that maintain or fund it are not linked: the TBox has no property from organisation to policy.
        gg = self.gg
        politica = rdf_types.Politica.child_uri_ref('fairsharing-%s' % (info['id'],))
        gg.add((politica, RDF.type, rdf_types.Politica))
        gg.add((politica, rdf_types.tiene_nombre_politica, Literal(info['name'].replace('@', ''), datatype=XSD.string)))
        if info.get('homepage'):
            gg.set((politica, rdf_types.tiene_url_politica, Literal(info['homepage'])))
        for record_association in info.get('recordAssociations') or []:
            label = record_association['recordAssocLabel']
            linked_id = record_association['linkedRecord']['id']
            (registry, _) = self.records.get(linked_id, (None, None))
            if label == 'recommends' and registry == 'Database':
                repositorio = rdf_types.Repositorio.child_uri_ref('fairsharing-%s' % (linked_id,))
                gg.add((politica, rdf_types.politica_recomienda_repositorio, repositorio))
            elif label == 'recommends' and registry == 'Standard':
                estandar = self.record_iri(linked_id)
                gg.add((estandar, RDF.type, rdf_types.Estandar))
                gg.add((politica, rdf_types.politica_recomienda_estandar, estandar))
            elif label == 'extends' and registry == 'Policy':
                gg.add((politica, rdf_types.politica_extiende_a_politica, rdf_types.Politica.child_uri_ref('fairsharing-%s' % (linked_id,))))
            elif label == 'related_to' and registry == 'Policy':
                gg.add((politica, rdf_types.politica_relacionada_con_politica, rdf_types.Politica.child_uri_ref('fairsharing-%s' % (linked_id,))))
            # "deprecates", and associations to other registries, are left out

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
            self.process_policy(info)
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
