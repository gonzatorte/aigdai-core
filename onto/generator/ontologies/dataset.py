from .base import onto as base_onto, initiate as initiate_base
from .foaf import onto as foaf_onto, initiate as initiate_foaf
from owlready2 import *

onto = get_ontology("http://test.org/dataset.owl")


def initiate():
    initiate_foaf()
    initiate_base()
    with onto:
        # base_onto.__enter__()
        # base_onto.__exit__()

        class resultado_de_investigacion(Thing):
            pass

        class articulo(resultado_de_investigacion):
            pass

        class cdd(resultado_de_investigacion):
            pass

        cdd.nombre_usual = [
            locstr("coleccion de datos", lang="es"),
            locstr("dataset", lang="en"),
        ]
        cdd.sinonimo = [
            locstr("conjunto de datos", lang="es"),
        ]

        class autor(foaf_onto.Person):
            pass

        class productor_de_datos(autor):
            pass

        class es_producido_por_productor_de_datos(cdd >> productor_de_datos):
            pass

        class caracteristica_de_cdd(Thing):
            pass

        class caracteristica_de_productor_de_datos(caracteristica_de_cdd):
            pass

        class esquema_de_identificador_de_autor(caracteristica_de_productor_de_datos):
            pass

        esquema_de_identificador_de_autor.nombre_usual = [
            locstr("esquema de identificador de autores", lang="es"),
            locstr("author identification schema", lang="en"),
        ]
        esquema_de_identificador_de_autor.sinonimo = [
            locstr("aids", lang="en"),
        ]

        class admite_disciplina(caracteristica_de_cdd >> base_onto.disciplina):
            pass
        admite_disciplina.nombre_usual = [
            locstr("admite disciplina", lang="es"),
            locstr("admits subject", lang="en"),
        ]

        class esquema_de_identificador_persistente(caracteristica_de_cdd):
            pass
        esquema_de_identificador_persistente.nombre_usual = [
            locstr("esquema de identificador persistente", lang="es"),
            locstr("persistent identifier schema", lang="en"),
        ]

        class esquema_de_metadatos(caracteristica_de_cdd):
            pass
        esquema_de_metadatos.nombre_usual = [
            locstr("esquema de metadatos", lang="es"),
            locstr("metadata schema", lang="en"),
        ]

        class tamanio(caracteristica_de_cdd):
            pass

        class tamanio_en_disco(tamanio):
            pass

        class cantidad_de_elementos(tamanio):
            pass

        class cantidad_de_contenedores(tamanio):
            pass

        class licencia(caracteristica_de_cdd):
            pass

        class utiliza_formato_de_archivo(caracteristica_de_cdd):
            pass
        utiliza_formato_de_archivo.nombre_usual = [
            locstr("utiliza formato de archivo", lang="es"),
            locstr("use file format", lang="en"),
        ]

        class utiliza_tipo_de_dato(caracteristica_de_cdd):
            pass

        # AllDisjoint([
        #     esquema_de_identificador_de_autor,
        #     admite_disciplina,
        #     esquema_de_identificador_persistente,
        #     utiliza_formato_de_archivo,
        #     esquema_de_metadatos,
        #     licencia,
        #     utiliza_tipo_de_dato,
        # ])

        esquema_de_identificador_de_autores_instances = list(map(lambda x: esquema_de_identificador_de_autor(x), [
            'authorclaim',
            'isni',
            'orcid',
            'researcherid',
        ]))
        AllDifferent(esquema_de_identificador_de_autores_instances)
        licencia_instances = list(map(lambda x: licencia(x), [
            'cc_by',
            'cc0',
            'gpl',
            'mit',
        ]))
        AllDifferent(licencia_instances)
        [doi, _, handle, *_] = esquema_de_identificador_persistente_instances = list(map(lambda x: esquema_de_identificador_persistente(x), [
            'doi',
            'ark',
            'handle',
            'purl',
        ]))
        AllDifferent(esquema_de_identificador_persistente_instances)
        esquema_de_metadatos_instances = list(map(lambda x: esquema_de_metadatos(x), [
            'dc',
            'ddi',
            'oai_pmh',
            'schemaorg',
            'doi-datacite',
            'doi-crossref',
        ]))
        AllDifferent(esquema_de_metadatos_instances)

        class resultado_relacionado(resultado_de_investigacion >> resultado_de_investigacion):
            pass

        class cdd_es_identificado_por(resultado_de_investigacion >> esquema_de_identificador_persistente):
            pass

        class id_de_cdd(DataProperty, FunctionalProperty):
            domain = [cdd_es_identificado_por]
            range = [str]

        class autor_es_identificado_por(autor >> esquema_de_identificador_de_autor):
            pass

        class id_de_autor(DataProperty, FunctionalProperty):
            domain = [autor_es_identificado_por]
            range = [str]

        class extiende_a_esquema_de_identificador_persistente(esquema_de_identificador_persistente >> esquema_de_identificador_persistente):
            pass

        class extiende_a_esquema_de_metadatos(esquema_de_metadatos >> esquema_de_metadatos):
            pass

        doi.extiende_a_esquema_de_identificador_persistente.append(handle)


if __name__ == '__main__':
    initiate()
    import owlready2
    owlready2.JAVA_EXE = "/usr/bin/java"
    owlready2.sync_reasoner()
    if len(list(owlready2.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
