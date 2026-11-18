import onto.populator.common as common
from onto.populator.utils import owl_all_different, gross_date_bounds
import onto.populator.rdf_types as rdf_types
from rdflib import Graph, Literal
from rdflib.namespace import RDF, OWL, XSD
import datetime

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

    DISC_NAME_MAP = {
        "animal_and_dairy_science": None,
        "other_agricultural_sciences": None,
    }

    TIPOS_DE_DATOS = [
        'dataset'
    ]

    def mappings(self):
        for tipo_de_dato in self.TIPOS_DE_DATOS:
            obj = rdf_types.TipoDeDato.child_uri_ref(tipo_de_dato)
            self.gg.add((obj, RDF.type, rdf_types.TipoDeDato))

        # ToDo: Implement mapping with commons
        for a, b in self.CERT_NAME_MAP.items():
            certificacion = rdf_types.Certificacion.child_uri_ref(a)
            certificacion_normal = rdf_types.Certificacion.child_uri_ref(b)
            self.gg.add((certificacion, OWL.sameAs, certificacion_normal))

        for a, b in self.DISC_NAME_MAP.items():
            disciplina = rdf_types.Disciplina.child_uri_ref(a)
            if not b:
                self.gg.add((disciplina, RDF.type, rdf_types.Disciplina))
            else:
                disciplina_normal = rdf_types.Disciplina.child_uri_ref(b)
                self.gg.add((disciplina, OWL.sameAs, disciplina_normal))

    def process(self, info):
        gg = self.gg
        uid = info['uid']
        # Prefixed with the source, like the records of the other sources (re3data ids already start with r3d)
        repositorio = rdf_types.Repositorio.child_uri_ref('datacite-%s' % (uid,))
        gg.add((repositorio, RDF.type, rdf_types.Repositorio))

        # doi_metadata (the DOI of the re3data record) is processed by the doi source (onto/populator/sources/doi.py)
        graphql_data = info['datacite_graphql_data']

        if graphql_data['providerType'] == 'dataProvider':
            gg.add((repositorio, RDF.type, rdf_types.Rdd))
        if graphql_data['providerType'] == 'serviceProvider':
            gg.add((repositorio, RDF.type, rdf_types.Agregador))

        if graphql_data.get('name', None):
            gg.add((repositorio, rdf_types.tiene_nombre_repositorio, Literal(graphql_data['name'].replace('@', ''), datatype=XSD.string)))
        for alternateName in graphql_data['alternateName']:
            gg.add((repositorio, rdf_types.tiene_nombre_repositorio, Literal(alternateName.replace('@', ''), datatype=XSD.string)))

        # Without a re3data DOI the literal would be "None", shared by every such record, and they would be reconciled together
        if graphql_data.get('re3dataDoi'):
            common.add_doi_id(gg, graphql_data['re3dataDoi'], repositorio)

        if graphql_data['type'] != 'Repository':
            raise Exception()

        for pid_d_system in graphql_data['pidSystem']:
            if pid_d_system == 'none':
                continue
            if pid_d_system == 'other':
                pid_system = "other_%s" % (uid,)
            else:
                pid_system = pid_d_system
            # ToDo: Unify enumerated values or declare same-as
            #     "_id" : "doi",
            #     "_id" : "none",
            #     "_id" : "hdl",
            #     "_id" : "urn",
            #     "_id" : "purl",
            #     "_id" : "ark",
            esquema_de_id_persistente = rdf_types.EsquemaDeIdPersistente.child_uri_ref(pid_system)
            gg.add((esquema_de_id_persistente, RDF.type, rdf_types.EsquemaDeIdPersistente))
            gg.add((repositorio, rdf_types.acepta_esquema_de_identificadores_persistentes, esquema_de_id_persistente))

        for cert_d in graphql_data['certificate']:
            if cert_d == 'none':
                continue
            if cert_d == 'other':
                cert = "other_%s" % (uid,)
            else:
                cert = self.CERT_NAME_MAP[cert_d]
            # ToDo: Unify enumerated values or declare same-as
            certificacion = common.certification_ref(cert)
            gg.add((certificacion, RDF.type, rdf_types.Certificacion))
            # ToDo: All different for the certifications, or is it something already stated before?
            aplicacion_de_cert = rdf_types.AplicacionDeCertificacionARepositorio.child_uri_ref("%s-%s" % (uid, cert))
            gg.add((aplicacion_de_cert, RDF.type, rdf_types.AplicacionDeCertificacionARepositorio))
            gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_repositorio, repositorio))
            gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_certificacion, certificacion))
            # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_inicio_periodo, certificacion))
            # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_fin_periodo, certificacion))

        for lang in graphql_data['language']:
            gg.add((repositorio, rdf_types.usa_lenguaje_repositorio, Literal(normalize_lang_code(lang), datatype=XSD.string)))

        all_items = []
        for keyword in graphql_data['keyword']:
            palabra_clave = rdf_types.PalabraClave.child_uri_ref(keyword)
            all_items.append(palabra_clave)
            gg.add((palabra_clave, rdf_types.tiene_sinonimo_palabra_clave, Literal(keyword, datatype=XSD.string)))
            gg.add((repositorio, rdf_types.tiene_palabra_clave_repositorio, palabra_clave))
        owl_all_different(gg, all_items)

        all_items = []
        for subject in graphql_data['subject']:
            disciplina = rdf_types.Disciplina.child_uri_ref(subject['termCode'])
            all_items.append(disciplina)
            gg.add((disciplina, rdf_types.nombre_de_disciplina, Literal(subject['name'], datatype=XSD.string)))
            gg.set((disciplina, rdf_types.disciplina_tiene_esquema, Literal('dfg', datatype=XSD.string)))
            # ToDo: Use the "description" field, which is an array of str
            # gg.set((disciplina, rdf_types.descripcion_de_disciplina, Literal(subject['description'], datatype=XSD.string)))
            gg.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))
        owl_all_different(gg, all_items)

        if 'viewCount' in graphql_data:
            pass
        if 'downloadCount' in graphql_data:
            pass

        estadisticos = graphql_data['datasets']
        generado_en = datetime.datetime.now()
        (generado_en_desde, generado_en_hasta) = gross_date_bounds(generado_en)
        total_count = estadisticos['totalCount']
        if 'published' in estadisticos:
            for itm in estadisticos['published']:
                year = int(itm['id'])
                estadistico_itm = rdf_types.EstadisticoSobrePublicacion.child_uri_ref("%s-%s" % (uid, year))
                gg.add((estadistico_itm, RDF.type, rdf_types.EstadisticoSobrePublicacion))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_valor, Literal(itm['count'])))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_repositorio, repositorio))
                gg.set((estadistico_itm, rdf_types.estadistico_sobre_publicacion_tiene_fecha, Literal(year, datatype=rdf_types.GrossDate)))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha, Literal(generado_en.isoformat(), datatype=rdf_types.CustomDate)))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha_desde, generado_en_desde))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha_hasta, generado_en_hasta))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_total, Literal(total_count)))
        if 'fieldsOfScienceCombined' in estadisticos:
            for itm in estadisticos['fieldsOfScienceCombined']:
                if itm['id'] == '__missing__':
                    continue
                elif itm['id'] == '__other__':
                    continue
                # elif itm['id'] not in self.DISC_NAME_MAP:
                #     raise Exception()
                disciplina_norm = itm['id']
                disciplina = rdf_types.Disciplina.child_uri_ref(disciplina_norm)
                estadistico_itm = rdf_types.EstadisticoSobreDisciplina.child_uri_ref("%s-%s" % (uid, disciplina_norm))
                gg.add((estadistico_itm, RDF.type, rdf_types.EstadisticoSobreDisciplina))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_valor, Literal(itm['count'])))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_repositorio, repositorio))
                gg.set((estadistico_itm, rdf_types.estadistico_sobre_disciplina_tiene_disciplina, disciplina))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha, Literal(generado_en.isoformat(), datatype=rdf_types.CustomDate)))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha_desde, generado_en_desde))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha_hasta, generado_en_hasta))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_total, Literal(total_count)))
        if 'funders' in estadisticos:
            for itm in estadisticos['funders']:
                if itm['id'] == '__missing__':
                    continue
                if itm['id'] == '__other__':
                    continue
        if 'affiliations' in estadisticos:
            for itm in estadisticos['affiliations']:
                if itm['id'] == '__missing__':
                    continue
                if itm['id'] == '__other__':
                    continue
        if 'licenses' in estadisticos:
            for itm in estadisticos['licenses']:
                # beware of __missing__
                if itm['id'] == '__missing__':
                    continue
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
                if itm['id'] == '__missing__':
                    continue
                elif itm['id'] == '__other__':
                    continue
                elif itm['id'] not in self.TIPOS_DE_DATOS:
                    raise Exception()
                tipo_de_dato = rdf_types.TipoDeDato.child_uri_ref(itm['id'])
                estadistico_itm = rdf_types.EstadisticoSobreTipoDeDato.child_uri_ref("%s-%s" % (uid, itm['id']))
                gg.add((estadistico_itm, RDF.type, rdf_types.EstadisticoSobreTipoDeDato))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_valor, Literal(itm['count'])))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_repositorio, repositorio))
                gg.set((estadistico_itm, rdf_types.estadistico_sobre_tipo_de_dato_tiene_tipo_de_dato, tipo_de_dato))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha, Literal(generado_en.isoformat(), datatype=rdf_types.CustomDate)))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha_desde, generado_en_desde))
                gg.set((estadistico_itm, rdf_types.estadistico_generado_en_fecha_hasta, generado_en_hasta))
                gg.set((estadistico_itm, rdf_types.estadistico_tiene_total, Literal(total_count)))

