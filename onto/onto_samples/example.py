
aa1 = [
    'colección_de_datos',
    'exportación_de_citas',
    'motor_de_repositorio',
    'repositorio',
    'funcionalidad',
    'funcionalidad_para_colecciones',
]

aa = [
    'api_para_cosecha',
    'control_de_acceso',
    'integración_con_redes_sociales',
    'interfaz_multilenguaje',
    'periodo_de_embargo',
    'servicio_de_curaduría',
]

dd = [
    'aids_soportado',
    'disciplina_soportada',
    'esquema_de_identificador_persistente_soportado',
    'formato_de_archivo_soportado',
    'formato_de_metadatos_soportado',
    'licencia_soportada',
    'tipo_de_datos_soportado',
]

bb = [
    'authorclaim',
    'isni',
    'orcid',
    'researcherid',
    'ark',
    'articulos',
    'cc_by',
    'cc0',
    'ckan',
    'cuadernos_de_laboratorio',
    'datacite',
    'dataverse',
    'dc',
    'ddi',
    'doi',
    'dspace',
    'entrevistas',
    'gpl',
    'handle',
    'mit',
    'oai_pmh',
    'purl',
]

cc = [
    'mime-type',
    'nombre_de_repositorio',
    'home_page',
]

from owlready2 import *
import owlready2
owlready2.JAVA_EXE = "/usr/bin/java"

onto = get_ontology("http://test.org/onto.owl")

with onto:
    class Drug(Thing):
        pass

    class ActivePrinciple(Thing):
        pass

    AllDisjoint([Drug, ActivePrinciple])

    class has_for_active_principle(Drug >> ActivePrinciple):
        pass

    class Ingredient(Thing):
        pass

    class has_for_ingredient(ObjectProperty):
        domain = [Drug]
        range = [Ingredient]

    my_drug1 = Drug("my_drug1", has_for_active_principle=[])
    my_drug2 = Drug("my_drug2", has_for_active_principle=[])
    AllDifferent([my_drug1, my_drug2])

    NewClass = types.new_class("NewClass", (Thing,))

    class BloodBasedProduct(Thing):
        pass

    a_blood_based_drug = Drug()
    a_blood_based_drug.is_a.append(BloodBasedProduct)

sync_reasoner()

list(default_world.inconsistent_classes())
if Nothing in Drug.equivalent_to:
    print("Drug is inconsistent!")


default_world.set_backend(filename="../world.sqlite3")
default_world.save()
onto.save(file="../my-onto.owl", format="rdfxml")
