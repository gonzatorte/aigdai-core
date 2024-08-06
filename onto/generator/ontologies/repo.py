from .base import onto as base_onto, initiate as base_initiate
from owlready2 import *

onto = get_ontology("http://test.org/repo.owl")


def initiate():
    base_initiate()
    with onto:
        class politica(Thing):
            pass
        politica.nombre_usual = [
            locstr("política", lang="es"),
            locstr("policy", lang="en"),
        ]

        class repositorio(Thing):
            pass
        repositorio.nombre_usual = [
            locstr("repositorio", lang="es"),
            locstr("repository", lang="en"),
        ]
        repositorio.sinonimo = [
            locstr("archivo", lang="es"),
            locstr("archive", lang="en"),
        ]

        class motor_de_repositorio(Thing):
            pass

        class agregador(Thing):
            pass
        agregador.nombre_usual = [
            locstr("agregador", lang="es"),
            locstr("aggregator", lang="en"),
        ]
        agregador.sinonimo = [
            locstr("buscador", lang="es"),
        ]

        class catalogo_de_repositorio(Thing):
            pass
        catalogo_de_repositorio.nombre_usual = [
            locstr("catalogo de repositorios", lang="es"),
            locstr("repository_catalog", lang="en"),
        ]
        catalogo_de_repositorio.sinonimo = [
            locstr("proveedor de servicio", lang="en"),
        ]

        class funcionalidad(Thing):
            pass
        funcionalidad.nombre_usual = [
            locstr("funcionalidad", lang="es"),
            locstr("feature", lang="en"),
        ]

        class funcionalidad_para_cdd(funcionalidad):
            pass
        funcionalidad_para_cdd.nombre_usual = [
            locstr("funcionalidad para colecciones", lang="es"),
            locstr("collection feature", lang="en"),
        ]

        class exportacion_de_citas(funcionalidad):
            pass
        exportacion_de_citas.nombre_usual = [
            locstr("exportación de citas", lang="es"),
            locstr("cite export", lang="en"),
        ]

        class api_para_cosecha(funcionalidad):
            pass
        api_para_cosecha.nombre_usual = [
            locstr("api para cosecha", lang="es"),
            locstr("harvesting api", lang="en"),
        ]

        class control_de_acceso(funcionalidad):
            pass
        control_de_acceso.nombre_usual = [
            locstr("control de acceso", lang="es"),
            locstr("access control", lang="en"),
        ]

        class integracion_con_red_social(funcionalidad):
            pass
        integracion_con_red_social.nombre_usual = [
            locstr("integración con red social", lang="es"),
            locstr("social media integration", lang="en"),
        ]

        class interfaz_multilenguaje(funcionalidad):
            pass
        interfaz_multilenguaje.nombre_usual = [
            locstr("interfaz multilenguaje", lang="es"),
            locstr("multilanguage interface", lang="en"),
        ]

        class periodo_de_embargo(funcionalidad):
            pass
        periodo_de_embargo.nombre_usual = [
            locstr("período de embargo", lang="es"),
            locstr("embargo period", lang="en"),
        ]

        class servicio_de_curaduria(funcionalidad):
            pass
        servicio_de_curaduria.nombre_usual = [
            locstr("servicio de curaduría", lang="es"),
            locstr("curator service", lang="en"),
        ]

        AllDisjoint([
            exportacion_de_citas,
            api_para_cosecha,
            control_de_acceso,
            integracion_con_red_social,
            interfaz_multilenguaje,
            periodo_de_embargo,
            servicio_de_curaduria,
        ])

        class soporte_para_caracteristica_de_cdd(funcionalidad_para_cdd):
            pass

        class caracteristica_de_productor_de_datos(soporte_para_caracteristica_de_cdd):
            pass

        class utiliza_motor(ObjectProperty, FunctionalProperty):
            domain = [repositorio]
            range = [motor_de_repositorio]

        class es_cosechado_por(repositorio >> agregador):
            pass

        class relacionado_con_organizacion(repositorio >> base_onto.organizacion):
            pass

        # ToDo: quizas es mejor modelar que la relacion es comercial cuando la organizacion con la que se relaciona es un financiador
        # ToDo: quizas es mejor modelar esto como un concepto y es mejor para traducirlo
        class tipo_de_relacion_con_organizacion(Datatype):
            equivalent_to = [OneOf(["financiamiento", "técnica", "administrativa"])]

        class tiene_tipo_de_relacion_con_organizacion(DataProperty, FunctionalProperty):
            domain = [relacionado_con_organizacion]
            range = [tipo_de_relacion_con_organizacion]

        class tiene_periodo_de_relacion_con_organizacion(DataProperty, FunctionalProperty):
            domain = [relacionado_con_organizacion]
            # ToDo: Buscar un datatype nuevo que permita declarar cosas como intervalo entre fechas (y fechas con extremos indeterminados)
            #  tb permitir expresar "desde una fecha pero no se sabe hasta cuándo" como algo distinto de "desde una fecha hasta el infinito"
            range = [str]

        class tiene_nombre_politica(Datatype):
            domain = [politica]
            range = [str]

        class tiene_url_politica(Datatype):
            domain = [politica]
            # ToDo: Usar foaf:Document para referenciar a manuales o cosas que deben ser leídas por un humano
            range = [str]

        # ToDo: Quizas hacerlo un FunctionalProperty y que la politica sea un conjunto de condiciones
        class usa_politica(ObjectProperty):
            domain = [relacionado_con_organizacion]
            range = [politica]

        # ToDo: En realidad, un repositorio puede soportar más de 1 lenguaje... así que no es FunctionalProperty
        #  aunque el manejo de colecciones puede generar problemas para restringir la unicidad en esas colecciones (aunque no sé si importa)
        class usa_lenguaje(DataProperty, FunctionalProperty):
            domain = [repositorio]
            range = [base_onto.lenguaje]
        # class usa_lenguaje(repositorio >> base_onto.lenguaje):
        #     pass

        class es_catalogado_por(repositorio >> catalogo_de_repositorio):
            pass

        # ToDo: No se está diciendo el identificador en que sistema... tomamos re3data como el estándar?
        class id_de_repositorio(DataProperty, FunctionalProperty):
            domain = [es_catalogado_por]
            range = [str]


if __name__ == '__main__':
    initiate()
    import owlready2
    owlready2.JAVA_EXE = "/usr/bin/java"
    owlready2.sync_reasoner()
    if len(list(owlready2.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
