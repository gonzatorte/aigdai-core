import onto.populator.common as common
from onto.populator.utils import owl_all_different, find_or_fail
import onto.populator.rdf_types as rdf_types
from rdflib import Graph, Literal
from rdflib.namespace import RDF

ENG_LNG_CODE = 'eng'
DUMMY_VALUES = [
    {
        "ids": [
            {
                "value": "1",
                "catalog": common.CatalogoDummy,
            },
            {
                "value": "dummy/123.123.123",
                "catalog": common.CatalogoDoi,
            },
        ],
        "names": ["sample repo", "repo ejemplo"], "description": "my example repo",
        "createdAtYear": 2020, "isActive": True, "isDataProvider": True, "isServiceProvider": True,
        "organizations": [
            {
                "id_aliases": [
                    {
                        "value": "456",
                        "type": "ROR",
                    },
                    {
                        "value": "123123",
                        "type": "ISNI",
                    },
                ],
                "names": [
                    "universidad de ningun lugar",
                    "UNOW",
                    "university of nowhere",
                ],
                "types": ["education"],
                "countries": ["AAA"],
                "responsibilities": [
                    {
                        "type": "tecnica",
                        "endDate": "2020-12-25",
                        "startDate": "2008-10-31",
                    },
                    {
                        "type": "general",
                        "startDate": "2008-10-31",
                    },
                ],
            },
            {
                "id_aliases": [
                    {
                        "value": "123",
                        "type": "ROR",
                    },
                ],
            },
        ],
        "pidSystems": ["ark", "purl"],
        # ToDo: Tienen fecha de aplicacion tb
        "certificate": ["cts", "trac"],
        "languages": ["eng", "ita"],
        "subjects": ["1001", "210"],
    },
    {
        "ids": [
            {
                "value": "2",
                "catalog": common.CatalogoDummy,
            },
            {
                "value": "dummy/456.456.456",
                "catalog": common.CatalogoDoi,
            },
        ],
        "names": ["other repo", "otro repo"], "description": "their another repo",
        "createdAtYear": 2015, "isActive": False, "isDataProvider": False, "isServiceProvider": True,
        "organizations": [
            {
                "id_aliases": [
                    {
                        "value": "123123",
                        "type": "WIKIDATA",
                    },
                    {
                        "value": "123",
                        "type": "ROR",
                    },
                ],
                "names": [
                    "EXAMPLE RESEARCH CENTER",
                    "centre de recherche exemple",
                    "CE.DE.EX",
                ],
                "types": ["facility", "funder"],
                "countries": ["FRA", "ENG"],
                "responsibilities": [
                    {
                        "type": "tecnica",
                        "endDate": "2020-01-01",
                        "startDate": "2012-01-01",
                    },
                    {
                        "type": "financiamiento",
                        "endDate": "2021-12-01",
                        "startDate": "2024-01-01",
                    },
                ],
            },
        ],
        "pidSystems": ["doi", "purl"],
        "certificate": ["trac"],
        "languages": ["spa", "ita"],
        "subjects": ["311", "210", "1"],
    },
]

class DummySource:
    def __init__(self, gg: Graph):
        self.gg = gg

    def process(self):
        gg = self.gg
        repo_entities = []
        for idx, info in enumerate(DUMMY_VALUES):
            repo_id = info['ids'][0]["value"] if len(info['ids']) > 0 else f"{idx}-of-dummy"
            repositorio = rdf_types.Repositorio.child_uri_ref(repo_id)
            repo_entities.append(repositorio)
            gg.set((repositorio, RDF.type, rdf_types.Repositorio))

            for name in info.get('names', []):
                gg.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(name, lang=ENG_LNG_CODE)))
            gg.set((repositorio, rdf_types.tiene_descripcion_repositorio, Literal(info['description'], lang=ENG_LNG_CODE)))
            gg.set((repositorio, rdf_types.repositorio_creado_en_anio, Literal(info['createdAtYear'])))
            gg.set((repositorio, rdf_types.repositorio_esta_activo, Literal(bool(info['isActive']))))

            if info.get('isDataProvider', None):
                gg.set((repositorio, RDF.type, rdf_types.Rdd))
            if info.get('isServiceProvider', None):
                gg.set((repositorio, RDF.type, rdf_types.Agregador))

            all_items = []
            for composed_id in info.get("ids", []):
                catalog_id = composed_id["catalog"].local_uri
                id_repo = rdf_types.IdDeRepositorio.child_uri_ref("%s-%s" % (catalog_id, composed_id["value"]))
                all_items.append(id_repo)
                gg.set((id_repo, RDF.type, rdf_types.IdDeRepositorio))
                gg.set((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
                gg.set((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(composed_id["value"])))
                gg.set((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, composed_id["catalog"]))
            owl_all_different(gg, all_items)

            all_items = []
            for pid_system in info.get('pidSystems', []):
                esquema_de_id_persistente = rdf_types.EsquemaDeIdPersistente.child_uri_ref(pid_system)
                all_items.append(esquema_de_id_persistente)
                gg.set((esquema_de_id_persistente, RDF.type, rdf_types.EsquemaDeIdPersistente))
                # ToDo: Dejar de usar repositorio_aporta_funcionalidad y poner algo mas especifico
                gg.set((esquema_de_id_persistente, rdf_types.repositorio_aporta_funcionalidad, repositorio))
            owl_all_different(gg, all_items)

            all_items = []
            for cert_d in info.get('certificate', []):
                certificacion = rdf_types.Certificacion.child_uri_ref(cert_d)
                all_items.append(certificacion)
                gg.set((certificacion, RDF.type, rdf_types.Certificacion))
                aplicacion_de_cert = rdf_types.AplicacionDeCertificacionARepositorio.child_uri_ref("%s-%s" % (repo_id, cert_d))
                gg.set((aplicacion_de_cert, RDF.type, rdf_types.AplicacionDeCertificacionARepositorio))
                gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_repositorio, repositorio))
                gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_certificacion, certificacion))
                # ToDo: Agregar fecha de aplicacion
                # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_inicio_periodo, certificacion))
                # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_fin_periodo, certificacion))
            owl_all_different(gg, all_items)

            for lang in info.get('languages', []):
                gg.set((repositorio, rdf_types.usa_lenguaje_repositorio, Literal(lang)))

            all_items = []
            for subject in info.get('subjects', []):
                disciplina = rdf_types.Disciplina.child_uri_ref(subject)
                all_items.append(disciplina)
                gg.set((disciplina, rdf_types.nombre_de_disciplina, Literal(subject)))
                gg.set((disciplina, rdf_types.disciplina_tiene_esquema, Literal('dfg')))
                gg.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))
            owl_all_different(gg, all_items)

            all_items = []
            for idx_org, organization in enumerate(info.get('organizations', [])):
                id_aliases = organization.get('id_aliases', [])
                id_org = "%s-%s" % (id_aliases[0]["type"], id_aliases[0]["value"]) if len(id_aliases) > 0 else f"org-{idx_org}-of-{repo_id}"
                org_instance = rdf_types.Organizacion.child_uri_ref(id_org)
                all_items.append(org_instance)
                gg.set((org_instance, RDF.type, rdf_types.Organizacion))

                for instName in organization.get('names', []):
                    gg.set((org_instance, rdf_types.tiene_nombre_organizacion, Literal(instName)))

                for country in organization.get('countries', []):
                    if country == 'AAA':
                        location = common.locacion_internacional
                        gg.set((location, RDF.type, rdf_types.Locacion))
                    else:
                        location = rdf_types.Pais.child_uri_ref(country)
                        gg.set((location, RDF.type, rdf_types.Pais))
                    gg.set((org_instance, rdf_types.organizacion_se_ubica_en, location))

                for org_type in organization.get('types', []):
                    gg.add((org_instance, rdf_types.tiene_tipo_de_organizacion, Literal(org_type, datatype="tipo_de_organizacion")))

                id_aliases_entities = []
                for id_alias in id_aliases:
                    id_de_organizacion = rdf_types.IdDeOrganizacion.child_uri_ref(id_alias['value'])
                    id_aliases_entities.append(id_de_organizacion)
                    gg.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                    tipo_de_id_de_organizacion = find_or_fail(
                        common.ORG_ID_SCHEMAS,
                        lambda x: id_alias['type'] in [tt.upper() for tt in x[1]]
                    )[2]
                    gg.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion))
                    gg.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(id_alias['value'])))
                    gg.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, org_instance))
                owl_all_different(gg, id_aliases_entities)

                responsibility_entities = []
                for responsibility in organization.get('responsibilities', []):
                    responsibility_type = responsibility['type']
                    relacion_repositorio_y_organizacion = rdf_types.RelacionRepositorioYOrganizacion.child_uri_ref("%s-%s-%s" % (id_org, repo_id, responsibility_type))
                    responsibility_entities.append(relacion_repositorio_y_organizacion)
                    gg.set((relacion_repositorio_y_organizacion, RDF.type, rdf_types.RelacionRepositorioYOrganizacion))
                    gg.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_repositorio, repositorio))
                    gg.set((relacion_repositorio_y_organizacion, rdf_types.relacion_repositorio_y_organizacion_tiene_organizacion, org_instance))
                    # ToDo: Ver como funciona el casteo a date u otros datatypes cuando es un literal
                    inicio_periodo_de_relacion_con_organizacion = responsibility.get('startDate', None)
                    if inicio_periodo_de_relacion_con_organizacion:
                        gg.set((relacion_repositorio_y_organizacion, rdf_types.tiene_inicio_periodo_de_relacion_con_organizacion, Literal(inicio_periodo_de_relacion_con_organizacion, datatype="gross_date")))
                    fin_periodo_de_relacion_con_organizacion = responsibility.get('endDate', None)
                    if fin_periodo_de_relacion_con_organizacion:
                        gg.set((relacion_repositorio_y_organizacion, rdf_types.tiene_fin_periodo_de_relacion_con_organizacion, Literal(fin_periodo_de_relacion_con_organizacion, datatype="gross_date")))
                    gg.set((relacion_repositorio_y_organizacion, rdf_types.tiene_tipo_de_relacion_con_organizacion, Literal(responsibility_type, datatype="tipo_de_relacion_con_organizacion")))
                owl_all_different(gg, responsibility_entities)
            owl_all_different(gg, all_items)
        owl_all_different(gg, repo_entities)
