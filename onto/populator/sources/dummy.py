import onto.populator.common as common
from onto.populator.utils import owl_all_different
import onto.populator.rdf_types as rdf_types
from rdflib import Graph, Literal
from rdflib.namespace import RDF

ENG_LNG_CODE = 'eng'

class DummySource:
    def __init__(self, gg: Graph):
        self.gg = gg

    def process(self):
        gg = self.gg
        for info in [
            {
                "id": 1, "names": ["sample repo", "repo ejemplo"], "description": "my example repo",
                "createdAtYear": 2020, "isActive": True, "isDataProvider": True, "isServiceProvider": True,
                "doi": "dummy/123.123.123",
                "pidSystems": ["doi", "ark", "purl"],
                "certificate": ["cts", "trac"],
                "languages": ["eng", "ita"],
                "subjects": ["1001", "210"],
            },
            {
                "id": 2, "names": ["other repo", "otro repo"], "description": "their another repo",
                "createdAtYear": 2015, "isActive": False, "isDataProvider": False, "isServiceProvider": True,
                "doi": "dummy/456.456.456",
                "pidSystems": ["ark", "purl"],
                "certificate": ["trac"],
                "languages": ["spa", "ita"],
                "subjects": ["311", "210"],
            },
        ]:
            repositorio = rdf_types.Repositorio.child_uri_ref(info['id'])
            # repositorio = URIRef("%s/%s" % (rdf_types.Repositorio.toPython(), info['id'],), rdf_types.my_ns)
            gg.set((repositorio, RDF.type, rdf_types.Repositorio))

            for name in info['names']:
                gg.set((repositorio, rdf_types.tiene_nombre_repositorio, Literal(name, lang=ENG_LNG_CODE)))
            gg.set((repositorio, rdf_types.tiene_descripcion_repositorio, Literal(info['description'], lang=ENG_LNG_CODE)))
            gg.set((repositorio, rdf_types.repositorio_creado_en_anio, Literal(info['createdAtYear'])))
            gg.set((repositorio, rdf_types.repositorio_esta_activo, Literal(bool(info['isActive']))))

            if info['isDataProvider']:
                gg.set((repositorio, RDF.type, rdf_types.Rdd))
            if info['isServiceProvider']:
                gg.set((repositorio, RDF.type, rdf_types.Agregador))

            if info["doi"]:
                id_repo = rdf_types.IdDeRepositorio.child_uri_ref(info["doi"])
                gg.set((id_repo, RDF.type, rdf_types.IdDeRepositorio))
                gg.set((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
                gg.set((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(info["doi"])))
                gg.set((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, common.CatalogoDoi))

            all_items = []
            for pid_system in info['pidSystems']:
                esquema_de_id_persistente = rdf_types.EsquemaDeIdPersistente.child_uri_ref(pid_system)
                all_items.append(esquema_de_id_persistente)
                gg.set((esquema_de_id_persistente, RDF.type, rdf_types.EsquemaDeIdPersistente))
                # ToDo: Dejar de usar repositorio_aporta_funcionalidad y poner algo mas especifico
                gg.set((esquema_de_id_persistente, rdf_types.repositorio_aporta_funcionalidad, repositorio))
            owl_all_different(gg, all_items)

            all_items = []
            for cert_d in info['certificate']:
                certificacion = rdf_types.Certificacion.child_uri_ref(cert_d)
                all_items.append(certificacion)
                gg.set((certificacion, RDF.type, rdf_types.Certificacion))
                aplicacion_de_cert = rdf_types.AplicacionDeCertificacionARepositorio.child_uri_ref("%s-%s" % (info['id'], cert_d))
                gg.set((aplicacion_de_cert, RDF.type, rdf_types.AplicacionDeCertificacionARepositorio))
                gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_repositorio, repositorio))
                gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_certificacion, certificacion))
                # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_inicio_periodo, certificacion))
                # gg.set((aplicacion_de_cert, rdf_types.aplicacion_de_certificacion_a_repositorio_tiene_fin_periodo, certificacion))
            owl_all_different(gg, all_items)

            for lang in info['languages']:
                gg.set((repositorio, rdf_types.usa_lenguaje_repositorio, Literal(lang)))

            all_items = []
            for subject in info['subjects']:
                disciplina = rdf_types.Disciplina.child_uri_ref(subject)
                all_items.append(disciplina)
                gg.set((disciplina, rdf_types.nombre_de_disciplina, Literal(subject)))
                gg.set((disciplina, rdf_types.disciplina_tiene_esquema, Literal('dfg')))
                gg.add((repositorio, rdf_types.repositorio_afin_a_disciplina, disciplina))
            owl_all_different(gg, all_items)
