from owlready2 import *
import owlready2 as owww
from . import cts
# from . import util
from .foaf import initiate as foaf_initiate, onto as foaf_ns

onto = get_ontology("http://test.org/base.owl")

# instances_by_class = {}

class HasKeyProperty:
    pass

# class HasKeyProperty(owww.Property):
#   namespace = owww.owl
#   @classmethod
#   def is_functional_for(Prop, o): return True

def initiate():
    foaf_initiate()
    # dc_ns = get_ontology("http://purl.org/dc/elements/1.1/").load()
    # dcat_ns = util.fetch_ontology('dcat', 'http://www.w3.org/ns/dcat#').load()
    # dct_ns = util.fetch_ontology('dct', "http://purl.org/dc/terms/").load()
    # dctype_ns = util.fetch_ontology('dctype', "http://purl.org/dc/dcmitype/").load()

    # skos_ns = util.fetch_ontology('skos', "http://www.w3.org/2004/02/skos/core#").load()
    # prov_ns = util.fetch_ontology('prov', "http://www.w3.org/ns/prov#").load()

    # odrl_ns = util.fetch_ontology('odrl', "http://www.w3.org/ns/odrl/2/").load()
    # dqv_ns = util.fetch_ontology('dqv', "http://www.w3.org/ns/dqv#").load()
    # earl_ns = util.fetch_ontology('earl', "http://www.w3.org/ns/earl#").load()
    # sdmx_attribute_ns = util.fetch_ontology('sdmx_attribute', "http://purl.org/linked-data/sdmx/2009/attribute#").load()

    with onto:
        # ToDo: Usar el de foaf mejor
        url = str

        class escala(Datatype):
            equivalent_to = [OneOf(["bueno", "regular", "malo"])]

        # ToDo: Creo que en realidad is same as rdfs:label , o usar http://purl.org/vocab/vann
        class nombre_usual(AnnotationProperty):
            pass

        class sinonimo(AnnotationProperty):
            pass

        # ToDo: Agregar en la ontología la descripción de que significa cada campo (o al menos los más confusos)
        #  o usar un doc (html) externo y rdfs:isDefinedBy ?
        class description(AnnotationProperty):
            pass

        # ToDo: extender aqui la ontologia de ROR
        class organizacion(foaf_ns.Organization):
            pass
        organizacion.nombre_usual = [
            locstr("organización", lang="es"),
            locstr("organization", lang="en"),
        ]
        organizacion.sinonimo = [
            locstr("institución", lang="es"),
        ]

        class tipo_de_id_de_organizacion(Thing):
            pass

        # class lenguaje(Thing):
        #     pass
        class lenguaje(Datatype):
            equivalent_to = [OneOf(list(map(lambda xx: xx[0], cts.languages)))]
            # 	owl:onDatatype  xsd:string ;
            # 	owl:withRestrictions (  [ xsd:pattern "[a-b]{3}" ] )
        lenguaje.nombre_usual = [
            locstr("lenguaje", lang="es"),
            locstr("language", lang="en"),
        ]
        lenguaje.sinonimo = [
            locstr("idioma", lang="es"),
        ]

        class locacion(Thing):
            pass
        locacion.nombre_usual = [
            locstr("locación", lang="es"),
            locstr("location", lang="en"),
        ]

        class pais(locacion):
            pass
        pais.nombre_usual = [
            locstr("país", lang="es"),
            locstr("country", lang="en"),
        ]

        class bloque_comercial(locacion):
            pass
        bloque_comercial.nombre_usual = [
            locstr("bloque comercial", lang="es"),
            locstr("trade bloc", lang="en"),
        ]

        class planeta(locacion):
            pass
        planeta.nombre_usual = [
            locstr("planeta", lang="es"),
            locstr("planet", lang="en"),
        ]

        class disciplina(Thing):
            pass
        disciplina.nombre_usual = [
            locstr("disciplina", lang="es"),
            locstr("subject", lang="en"),
        ]

        # ToDo: El término "tipo" es muy vago para lo que se quiere representar. Más bien sería esComercial: boolean
        # ToDo: quizas es mejor modelar esto como un concepto y es mejor para traducirlo
        class tipo_de_organizacion(Datatype):
            equivalent_to = [OneOf(["comercial", "no-comercial"])]

        class tiene_tipo_de_organizacion(DataProperty, FunctionalProperty):
            domain = [organizacion]
            range = [tipo_de_organizacion]

        # class has_key_organizacion(HasKeyProperty, FunctionalProperty):
        class has_key_organizacion(DataProperty, FunctionalProperty):
            domain = [organizacion]
            range = [url]

        class nombre_de_disciplina(DataProperty, FunctionalProperty):
            domain = [disciplina]
            range = [str]

        class es_sub_disciplina_de(ObjectProperty, TransitiveProperty):
            domain = [disciplina]
            range = [disciplina]

        class es_disciplina_afin(disciplina >> disciplina):
            pass

        class alfa_3_de_pais(DataProperty, FunctionalProperty):
            domain = [pais]
            range = [str]

        class nombre_de_pais(DataProperty, FunctionalProperty):
            domain = [pais]
            range = [str]

        class nombre_de_bloque(DataProperty, FunctionalProperty):
            domain = [bloque_comercial]
            range = [str]

        class sigla_de_bloque(DataProperty, FunctionalProperty):
            domain = [bloque_comercial]
            range = [str]

        class nombre_de_bloque(DataProperty, FunctionalProperty):
            domain = [pais]
            range = [str]

        class includido_en(ObjectProperty, TransitiveProperty):
            domain = [locacion]
            range = [locacion]

        class formato_de_archivo(Thing):
            pass
        formato_de_archivo.nombre_usual = [
            locstr("formato de archivo", lang="es"),
            locstr("file format", lang="en"),
        ]

        # ToDo: el nombre de "artefacto de investigación" es más acertado quizás
        class tipo_de_dato(Thing):
            pass

        # ToDo: En realidad no me queda claro si es funcional, pues hay organizaciones multinacionales...
        #  Quizás en ese caso, cada organización tendrá su branch en cada país...
        #  De hecho aparecen los código de país AAA y EUR que comprenden varios países
        class se_ubica_en(ObjectProperty, FunctionalProperty):
            domain = [organizacion]
            range = [locacion]

        class tiene_nombre(DataProperty, FunctionalProperty):
            domain = [organizacion]
            range = [str]
            # ToDo: reactivar
            # range = [foaf_ns.ontology.name]

        class tiene_nombre_alternativo(DataProperty):
            domain = [organizacion]
            range = [str]
            # ToDo: reactivar
            # range = [foaf_ns.name]

        # class organizacion_es_identificada_por(organizacion >> tipo_de_id_de_organizacion):
        #     pass
        #
        # class id_de_organizacion(DataProperty, FunctionalProperty):
        #     domain = [organizacion_es_identificada_por]
        #     range = [str]

        class id_de_organizacion(Thing):
            pass
        id_de_organizacion.nombre_usual = [
            locstr("identificador de organizacion", lang="es"),
            locstr("organization identifier", lang="en"),
        ]
        class id_de_organizacion_tiene_tipo(ObjectProperty, FunctionalProperty):
            domain = [id_de_organizacion]
            range = [tipo_de_id_de_organizacion]
        # class id_de_organizacion_tiene_organizacion(HasKeyProperty, ObjectProperty, FunctionalProperty):
        class id_de_organizacion_tiene_organizacion(ObjectProperty, FunctionalProperty):
            domain = [id_de_organizacion]
            range = [organizacion]
        class id_de_organizacion_tiene_literal(DataProperty, FunctionalProperty):
            domain = [id_de_organizacion]
            range = [str]

        class formato_codifica_tipo_de_archivo(formato_de_archivo >> tipo_de_dato):
            pass

        formato_de_archivo_instances = list(map(formato_de_archivo, [
            'imagen',
            'texto',
            'tabla',
        ]))
        AllDifferent(formato_de_archivo_instances)
        # instances_by_class[formato_de_archivo] = {x.name: x for x in formato_de_archivo_instances}
        tipo_de_datos_instances = list(map(tipo_de_dato, [
            'articulo',
            'cuaderno_de_laboratorio',
            'entrevista',
        ]))
        AllDifferent(tipo_de_datos_instances)
        # instances_by_class[tipo_de_dato] = {x.name: x for x in tipo_de_datos_instances}

        # class escala_mayor_que(ObjectProperty, TransitiveProperty):
        #     domain = [escala]
        #     range = [escala]
        #
        # escala_mayor_que["bueno"].escala_mayor_que("regular")
        # escala_mayor_que["regular"].escala_mayor_que("malo")

        # class Hex(object):
        #   def __init__(self, value):
        #     self.value = value
        #
        # def parser(s):
        #   return Hex(int(s, 16))
        #
        # def unparser(x):
        #   h = hex(x.value)[2:]
        #   if len(h) % 2 != 0: return "0%s" % h
        #   return h
        #
        # declare_datatype(Hex, "http://www.w3.org/2001/XMLSchema#hexBinary", parser, unparser)

        # instances_by_class[disciplina] = {}
        def tree_walk_disciplina(forest, parent):
            for tr in forest:
                ds = disciplina(tr[0])
                # instances_by_class[disciplina][ds.name] = ds
                ds.nombre_de_disciplina = tr[1]
                if parent is not None:
                    ds.es_sub_disciplina_de.append(parent)
                if len(tr) >= 3:
                    children = tr[2]
                    tree_walk_disciplina(children, ds)

        tree_walk_disciplina(cts.dfg_subjects, None)

        # instances_by_class[locacion] = {}
        cys = []
        planeta_tierra = planeta('tierra')
        for country_or_block in cts.countries:
            if len(country_or_block) >= 3:
                bl = bloque_comercial(country_or_block[0])
                # instances_by_class[locacion][bl.name] = bl
                bl.sigla_de_bloque = country_or_block[0]
                bl.nombre_de_bloque = country_or_block[1]
                bl.includido_en.append(planeta_tierra)
                for country in country_or_block[2]:
                    cy = pais(country[0])
                    # instances_by_class[locacion][cy.name] = cy
                    cy.alfa_3_de_pais = country[0]
                    cy.nombre_de_pais = country[1]
                    cy.includido_en.append(bl)
                    cys.append(cy)
            else:
                cy = pais(country_or_block[0])
                # instances_by_class[locacion][cy.name] = cy
                cy.alfa_3_de_pais = country_or_block[0]
                cy.nombre_de_pais = country_or_block[1]
                cy.includido_en.append(planeta_tierra)
                cys.append(cy)
        AllDifferent(cys)

    # ToDo: relacion skos:ConceptScheme y skos:Concept son creo para modelar tesauros y clasificaciones
    #  Se le dice que una instancia es un concepto y el conceptSchema es el criterio de clasificación
    #  Pueden servir para modelar jerarquías de disciplinar con skos:broader/skos:narrower (o mejor skos:broaderTransitive)
    #   Hay que hacer restricciones de dominio de las mismas para que solo sirva entre disciplinas?
    #  Se puede usar skos:related para relaciones vagas generales... (ojo que skos:related es simetrica pero broader no)
    #  Concept Collections se puede usar para declarar recursivamente propiedades a un conjunto de cosas al mismo tiempo?
    #   Se puede usar para las funcionalidades de datasets?

    # ToDo: Mirar a fondo http://purl.org/spar/datacite:
    #  Se puede usar el datacite:Identifier y datacite:hasIdentifier para el esquema de identificador dentro de un catalogo
    #   o identificador de autor dentro de un sistema de identificadores, o lo mismo con el sistema de PI

    # ToDo: Mirar el https://www.w3.org/ns/dcat

    # https://www.w3.org/ns/prov ??
    # Que es foaf:Agent?
    # Tengo foaf:mbox para emails
    # Tengo foaf:homepage para homepages
    # Tengo foaf:Document para referenciar a manuales o cosas que deben ser leídas por un humano

    # Para lenguaje se recomienda http://purl.org/dc/terms/language
    # Para licencias se recomienda http://purl.org/dc/terms/license ?

    # Ver http://www.w3.org/ns/odrl/2 para restriciones
    #  https://www.w3.org/ns/odrl/2/ Open Digital Rights Language?

    # La ontología vieja de re3data ya maneja el concepto de restriccione (que son por eg: licencias, politicas, etc)

    # ToDo: Para location parece que tengo http://www.w3.org/ns/locn#?
    #  dice que está legacy...
    #  Se tiene de geonames la ontología https://www.geonames.org/ontology/documentation.html
    #   Es lo que usa ROR

    # http://www.w3.org/2006/time# para tiempo o hay algo mejor en DC por ejemplo?
    #  eg: https://www.w3.org/TR/owl-time/?
    #   calendarios: https://raw.githubusercontent.com/w3c/sdw/gh-pages/time/rdf/time-gregorian.ttl
    #   intervalos y eventos: https://raw.githubusercontent.com/w3c/sdw/gh-pages/time/rdf/time.ttl

    # Data Quality Vocabulary: https://www.w3.org/TR/vocab-dqv/ ?

    # Evaluation and Report Language (http://www.w3.org/ns/earl#) ?

    # http://purl.org/linked-data/sdmx/2009/attribute# me suena a las licencias
    #  https://github.com/UKGovLD/publishing-statistical-data/blob/master/specs/src/main/example/example.ttl


if __name__ == '__main__':
    initiate()
    import owlready2
    owlready2.JAVA_EXE = "/usr/bin/java"
    owlready2.sync_reasoner()
    if len(list(owlready2.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
