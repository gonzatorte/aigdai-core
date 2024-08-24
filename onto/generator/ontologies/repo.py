from .base import onto as base_onto, initiate as base_initiate
import owlready2 as ow
# from owlready2 import *

onto = ow.get_ontology("http://test.org/repo.owl")


def initiate():
    base_initiate()
    with onto:
        class politica(ow.Thing):
            pass
        politica.nombre_usual = [
            ow.locstr("política", lang="es"),
            ow.locstr("policy", lang="en"),
        ]

        class repositorio(ow.Thing):
            pass
        repositorio.nombre_usual = [
            ow.locstr("repositorio", lang="es"),
            ow.locstr("repository", lang="en"),
        ]
        repositorio.sinonimo = [
            ow.locstr("archivo", lang="es"),
            ow.locstr("archive", lang="en"),
        ]

        class motor_de_repositorio(ow.Thing):
            pass

        class agregador(ow.Thing):
            pass
        agregador.nombre_usual = [
            ow.locstr("agregador", lang="es"),
            ow.locstr("aggregator", lang="en"),
        ]
        agregador.sinonimo = [
            ow.locstr("buscador", lang="es"),
        ]

        class catalogo_de_repositorio(ow.Thing):
            pass
        catalogo_de_repositorio.nombre_usual = [
            ow.locstr("catalogo de repositorios", lang="es"),
            ow.locstr("repository_catalog", lang="en"),
        ]
        catalogo_de_repositorio.sinonimo = [
            ow.locstr("proveedor de servicio", lang="en"),
        ]

        class funcionalidad(ow.Thing):
            pass
        funcionalidad.nombre_usual = [
            ow.locstr("funcionalidad", lang="es"),
            ow.locstr("feature", lang="en"),
        ]

        class funcionalidad_para_cdd(funcionalidad):
            pass
        funcionalidad_para_cdd.nombre_usual = [
            ow.locstr("funcionalidad para colecciones", lang="es"),
            ow.locstr("collection feature", lang="en"),
        ]

        class exportacion_de_citas(funcionalidad):
            pass
        exportacion_de_citas.nombre_usual = [
            ow.locstr("exportación de citas", lang="es"),
            ow.locstr("cite export", lang="en"),
        ]

        class api_para_cosecha(funcionalidad):
            pass
        api_para_cosecha.nombre_usual = [
            ow.locstr("api para cosecha", lang="es"),
            ow.locstr("harvesting api", lang="en"),
        ]

        class control_de_acceso(funcionalidad):
            pass
        control_de_acceso.nombre_usual = [
            ow.locstr("control de acceso", lang="es"),
            ow.locstr("access control", lang="en"),
        ]

        class integracion_con_red_social(funcionalidad):
            pass
        integracion_con_red_social.nombre_usual = [
            ow.locstr("integración con red social", lang="es"),
            ow.locstr("social media integration", lang="en"),
        ]

        class interfaz_multilenguaje(funcionalidad):
            pass
        interfaz_multilenguaje.nombre_usual = [
            ow.locstr("interfaz multilenguaje", lang="es"),
            ow.locstr("multilanguage interface", lang="en"),
        ]

        class periodo_de_embargo(funcionalidad):
            pass
        periodo_de_embargo.nombre_usual = [
            ow.locstr("período de embargo", lang="es"),
            ow.locstr("embargo period", lang="en"),
        ]

        class servicio_de_curaduria(funcionalidad):
            pass
        servicio_de_curaduria.nombre_usual = [
            ow.locstr("servicio de curaduría", lang="es"),
            ow.locstr("curator service", lang="en"),
        ]

        ow.AllDisjoint([
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

        class utiliza_motor(ow.ObjectProperty, ow.FunctionalProperty):
            domain = [repositorio]
            range = [motor_de_repositorio]

        class es_cosechado_por(repositorio >> agregador):
            pass

        class relacion_repositorio_y_organizacion(ow.Thing):
            pass

        class relacion_repositorio_y_organizacion_tiene_organizacion(ow.ObjectProperty, ow.FunctionalProperty):
            domain = [relacion_repositorio_y_organizacion]
            range = [base_onto.organizacion]

        class relacion_repositorio_y_organizacion_tiene_repositorio(ow.ObjectProperty, ow.FunctionalProperty):
            domain = [relacion_repositorio_y_organizacion]
            range = [repositorio]

        # ToDo: quizas es mejor modelar que la relacion es comercial cuando la organizacion con la que se relaciona es un financiador
        # ToDo: quizas es mejor modelar esto como un concepto y es mejor para traducirlo
        class tipo_de_relacion_con_organizacion(ow.Datatype):
            equivalent_to = [ow.OneOf(["financiamiento", "técnica", "administrativa"])]

        class tiene_tipo_de_relacion_con_organizacion(ow.DataProperty, ow.FunctionalProperty):
            domain = [relacion_repositorio_y_organizacion]
            range = [tipo_de_relacion_con_organizacion]

        class tiene_periodo_de_relacion_con_organizacion(ow.DataProperty, ow.FunctionalProperty):
            domain = [relacion_repositorio_y_organizacion]
            # ToDo: Buscar un datatype nuevo que permita declarar cosas como intervalo entre fechas (y fechas con extremos indeterminados)
            #  tb permitir expresar "desde una fecha pero no se sabe hasta cuándo" como algo distinto de "desde una fecha hasta el infinito"
            range = [str]

        class tiene_nombre_politica(ow.Datatype):
            domain = [politica]
            range = [str]

        class tiene_url_politica(ow.Datatype):
            domain = [politica]
            # ToDo: Usar foaf:Document para referenciar a manuales o cosas que deben ser leídas por un humano
            range = [str]

        # ToDo: Quizas hacerlo un FunctionalProperty y que la politica sea un conjunto de condiciones
        class usa_politica(ow.ObjectProperty):
            domain = [relacion_repositorio_y_organizacion]
            range = [politica]

        # ToDo: En realidad, un repositorio puede soportar más de 1 lenguaje... así que no es FunctionalProperty
        #  aunque el manejo de colecciones puede generar problemas para restringir la unicidad en esas colecciones (aunque no sé si importa)
        class usa_lenguaje(ow.DataProperty):
            domain = [repositorio]
            range = [base_onto.lenguaje]
        # class usa_lenguaje(repositorio >> base_onto.lenguaje):
        #     pass

        class id_de_catalogacion_de_repositorio(ow.Thing):
            pass

        class id_de_catalogacion_de_repositorio_tiene_catalogo(ow.ObjectProperty, ow.FunctionalProperty):
            domain = [id_de_catalogacion_de_repositorio]
            range = [catalogo_de_repositorio]

        class id_de_catalogacion_de_repositorio_tiene_repositorio(ow.ObjectProperty, ow.FunctionalProperty):
            domain = [id_de_catalogacion_de_repositorio]
            range = [repositorio]

        class id_de_catalogacion_de_repositorio_tiene_literal(ow.DataProperty, ow.FunctionalProperty):
            domain = [id_de_catalogacion_de_repositorio]
            range = [str]


if __name__ == '__main__':
    initiate()
    ow.JAVA_EXE = "/usr/bin/java"
    ow.sync_reasoner()
    if len(list(ow.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
