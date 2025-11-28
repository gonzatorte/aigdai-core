import re
import onto.populator.common as common
from onto.populator.utils import owl_all_different
import onto.populator.rdf_types as rdf_types
from rdflib import Graph, Literal
from rdflib.namespace import RDF, OWL

ENG_LNG_CODE = 'eng'

def normalize_lang_code(lang: str):
    if ENG_LNG_CODE != 'en':
        return ENG_LNG_CODE
    lang_n1 = lang.split('-')[0]
    if len(lang_n1) == 3:
        return lang_n1
    elif len(lang_n1) == 2:
        return "%sg" % (lang_n1, )
    else:
        raise Exception()

class DataCiteSource:
    def __init__(self, gg: Graph):
        self.gg = gg

    CERT_NAME_MAP = {
        "DSA": 'dsa',
        "Trusted Digital Repository": 'tdr',
        "WDS": 'wds',
        "DIN 31644": 'din31644',
        "DINI": 'dini',
        "CLARIN certificate B": 'clarin_b',
        "CoreTrustSeal": 'cts',
        "RatSWD": 'ratswd',
        "DINI Certificate": 'dini',
        "CLARIN": 'clarin',
    }

    TIPOS_DE_DATOS = [
        'dataset'
    ]

    def mappings(self):
        for tipo_de_dato in self.TIPOS_DE_DATOS:
            obj = rdf_types.TipoDeDato.child_uri_ref(tipo_de_dato)
            self.gg.set((obj, RDF.type, rdf_types.TipoDeDato))

        # ToDo: Implement mapping with commons
        for a, b in self.CERT_NAME_MAP.items():
            certificacion = rdf_types.Certificacion.child_uri_ref(a)
            certificacion_normal = rdf_types.Certificacion.child_uri_ref(b)
            self.gg.set((certificacion, OWL.sameAs, certificacion_normal))

    def process(self, info):
        gg = self.gg
        uid = info['uid']
        repositorio = rdf_types.Repositorio.child_uri_ref(uid)
        gg.set((repositorio, RDF.type, rdf_types.Repositorio))

        if info.get('doi_metadata', None) and info['doi_metadata'] != 'error' and info['doi_metadata'].get('attributes', None):
            doi_metadata = info['doi_metadata']['attributes']
            if doi_metadata['schemaVersion'] != 'http://datacite.org/schema/kernel-4':
                raise Exception()
            for _ in doi_metadata['identifiers']:
                raise Exception('always empty until now. not implemented')
            for _ in doi_metadata['alternateIdentifiers']:
                raise Exception('always empty until now. not implemented')
            for _ in doi_metadata['rightsList']:
                raise Exception('always empty until now. not implemented')
            for _ in doi_metadata['formats']:
                raise Exception('always empty until now. not implemented')
            for _ in doi_metadata['geoLocations']:
                raise Exception('always empty until now. not implemented')
            for _ in doi_metadata['viewsOverTime']:
                raise Exception('always empty until now. not implemented')
            # ToDo: have to create a model on ontology
            # for facetOverTime in doi_metadata['citationsOverTime']:
            #     print(int(facetOverTime["year"]), int(facetOverTime["total"]))
            for title in doi_metadata['titles']:
                gg.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(title['title'], lang=normalize_lang_code(title['lang']))))
            for description in doi_metadata['descriptions']:
                if description['descriptionType'] != 'Abstract':
                    raise Exception()
                gg.set((repositorio, rdf_types.tiene_descripcion_repositorio, Literal(description['description'], lang=normalize_lang_code(description['lang']))))
            if len(doi_metadata['dates']) > 1:
                raise Exception('always only issue date until now. not implemented')
            gg.set((repositorio, rdf_types.repositorio_creado_en_anio, Literal(doi_metadata['publicationYear'])))
            # ToDo: All are active according to datacite. Doesnt seems realistic...
            gg.set((repositorio, rdf_types.repositorio_esta_activo, Literal(bool(doi_metadata['isActive']))))
            # ToDo: have to create a model on ontology
            # for facetOverTime in doi_metadata['downloadsOverTime']:
            #     print(int(facetOverTime["year"]), int(facetOverTime["total"]))

            # ToDo: Still have to map: doi_metadata
            #   sizes
            #   fundingReferences funderName + grant?
        graphql_data = info['datacite_graphql_data']

        if graphql_data['providerType'] == 'dataProvider':
            gg.set((repositorio, RDF.type, rdf_types.Rdd))
        if graphql_data['providerType'] == 'serviceProvider':
            gg.set((repositorio, RDF.type, rdf_types.Agregador))

        if graphql_data.get('name', None):
            gg.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(graphql_data['name'])))
        for alternateName in graphql_data['alternateName']:
            gg.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(alternateName)))

        id_repo = rdf_types.IdDeRepositorio.child_uri_ref("datacite-%s" % (uid,))
        gg.set((id_repo, RDF.type, rdf_types.IdDeRepositorio))
        gg.set((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
        gg.set((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(graphql_data['re3dataDoi'])))
        gg.set((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, common.CatalogoDoi))

        if graphql_data['type'] != 'Repository':
            raise Exception()

        for pid_d_system in graphql_data['pidSystem']:
            if pid_d_system == 'none':
                continue
            if pid_d_system == 'other':
                pid_system = "other_%s" % (uid,)
            else:
                pid_system = pid_d_system
            # ToDo: Unificar enumerados o declarar same-as
            #     "_id" : "doi",
            #     "_id" : "none",
            #     "_id" : "hdl",
            #     "_id" : "urn",
            #     "_id" : "purl",
            #     "_id" : "ark",
            esquema_de_id_persistente = rdf_types.EsquemaDeIdPersistente.child_uri_ref(pid_system)
            gg.set((esquema_de_id_persistente, RDF.type, rdf_types.EsquemaDeIdPersistente))
            gg.set((repositorio, rdf_types.acepta_esquema_de_identificadores_persistentes, esquema_de_id_persistente))

        for cert_d in graphql_data['certificate']:
            if cert_d == 'none':
                continue
            if cert_d == 'other':
                cert = "other_%s" % (uid,)
            else:
                cert = self.CERT_NAME_MAP[cert_d]
            # ToDo: Unificar enumerados o declarar same-as
            certificacion = rdf_types.Certificacion.child_uri_ref(cert)
            gg.set((certificacion, RDF.type, rdf_types.Certificacion))
            # ToDo: All different las certificaciones o es algo que ya se dijo antes?
            # ToDo: El id es solo del cert, tiene que tener parte del repo...
            aplicacion_de_cert = rdf_types.AplicacionDeCertificacionARepositorio.child_uri_ref(cert)
            gg.set((aplicacion_de_cert, RDF.type, rdf_types.AplicacionDeCertificacionARepositorio))
            gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_repositorio, repositorio))
            gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_certificacion, certificacion))
            # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_inicio_periodo, certificacion))
            # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_fin_periodo, certificacion))

        for lang in graphql_data['language']:
            gg.set((repositorio, rdf_types.usa_lenguaje_repositorio, Literal(normalize_lang_code(lang))))

        all_items = []
        for keyword in graphql_data['keyword']:
            palabra_clave = rdf_types.PalabraClave.child_uri_ref(keyword)
            all_items.append(palabra_clave)
            gg.set((palabra_clave, rdf_types.tiene_sinonimo_palabra_clave, Literal(keyword)))
            gg.set((repositorio, rdf_types.tiene_palabra_clave_repositorio, palabra_clave))
        owl_all_different(gg, all_items)

        all_items = []
        for subject in graphql_data['subject']:
            disciplina = rdf_types.Disciplina.child_uri_ref(subject['termCode'])
            all_items.append(disciplina)
            gg.set((disciplina, rdf_types.nombre_de_disciplina, Literal(subject['name'])))
            gg.set((disciplina, rdf_types.disciplina_tiene_esquema, Literal('dfg')))
            # ToDo: Usar el campo "description" que es un array de str
            # gg.set((disciplina, rdf_types.descripcion_de_disciplina, Literal(subject['description'])))
            gg.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))
        owl_all_different(gg, all_items)

        if 'viewCount' in graphql_data:
            pass
        if 'downloadCount' in graphql_data:
            pass

        estadisticos = graphql_data['datasets']
        if 'totalCount' in estadisticos:
            pass
        if 'published' in estadisticos:
            for itm in estadisticos['published']:
                year = int(itm['id'])
                estadistico_itm = rdf_types.EstadisticoSobrePublicacion.child_uri_ref("%s-%s" % (uid, year))
                gg.set((estadistico_itm, RDF.type, rdf_types.EstadisticoSobrePublicacion))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_valor, Literal(itm['count'])))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_repositorio, repositorio))
                gg.set((estadistico_itm, rdf_types.estadistico_sobre_publicacion_tiene_fecha, Literal(year)))
        if 'fieldsOfScienceCombined' in estadisticos:
            for itm in estadisticos['fieldsOfScienceCombined']:
                pass
        if 'funders' in estadisticos:
            for itm in estadisticos['funders']:
                if itm['id'] == '__missing__':
                    pass
                if itm['id'] == '__other__':
                    pass
        if 'affiliations' in estadisticos:
            for itm in estadisticos['affiliations']:
                if itm['id'] == '__missing__':
                    pass
                if itm['id'] == '__other__':
                    pass
        if 'licenses' in estadisticos:
            for itm in estadisticos['licenses']:
                # ojo con __missing__
                if itm['id'] == '__missing__':
                    pass
                if itm['id'] == 'cc-by-3.0':
                    pass
                if itm['id'] == 'cc-by-4.0':
                    pass
                if itm['id'] == 'cc-by-nc-4.0':
                    pass
                if itm['id'] == 'cc-by-nc-3.0':
                    pass
                if itm['id'] == 'cc-by-nc-nd-3.0':
                    pass
        if 'openLicenseResourceTypes' in estadisticos:
            for itm in estadisticos['openLicenseResourceTypes']:
                # ojo con __missing__
                if itm['id'] == '__missing__':
                    pass
                elif itm['id'] == '__other__':
                    pass
                elif itm['id'] not in self.TIPOS_DE_DATOS:
                    raise Exception()
                tipo_de_dato = rdf_types.TipoDeDato.child_uri_ref(itm['id'])
                estadistico_itm = rdf_types.EstadisticoSobreTipoDeDato.child_uri_ref("%s-%s" % (uid, itm['id']))
                gg.set((estadistico_itm, RDF.type, rdf_types.EstadisticoSobreTipoDeDato))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_valor, Literal(itm['count'])))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_repositorio, repositorio))
                gg.set((estadistico_itm, rdf_types.estadistico_sobre_tipo_de_dato_tiene_tipo_de_dato, tipo_de_dato))
