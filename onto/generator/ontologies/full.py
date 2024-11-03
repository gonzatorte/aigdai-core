from .base import onto as base_onto, initiate as base_initiate
from .dataset import onto as dataset_onto, initiate as dataset_initiate
from .repo import onto as repo_onto, initiate as repo_initiate
from .full import onto as full_onto, initiate as full_initiate

from owlready2 import *

onto = get_ontology("http://test.org/full.owl")


def initiate():
    base_initiate()
    dataset_initiate()
    repo_initiate()
    with onto:
        pass
        # # ToDo: Functional
        # class coleccion_de_datos_es_alojada_en_repositorio(dataset_onto.coleccion_de_datos >> repo_onto.repositorio):
        #     pass
        #
        # # ToDo: No tiene sentido del todo tener las instancias "caracteristicas"
        # class presenta_caracteristica_de_coleccion_de_datos(dataset_onto.coleccion_de_datos >> repo_onto.soporte_para_caracteristica_de_cdd):
        #     pass
        #
        # # ToDo: No tiene sentido del todo tener las instancias "caracteristicas"
        # class presenta_caracteristica_de_productor_de_datos(dataset_onto.productor_de_datos >> repo_onto.caracteristica_de_productor_de_datos):
        #     pass


if __name__ == '__main__':
    initiate()
    import owlready2
    owlready2.JAVA_EXE = "/usr/bin/java"
    owlready2.sync_reasoner()
    if len(list(owlready2.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
