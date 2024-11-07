from .base import initiate as base_initiate
from .dataset import initiate as dataset_initiate
from .repo import initiate as repo_initiate

import owlready2 as ow

# onto = ow.get_ontology("http://test.org/full.owl")

def initiate():
    base_initiate()
    dataset_initiate()
    repo_initiate()
    # with onto:
    #     # ToDo: Functional
    #     class coleccion_de_datos_es_alojada_en_repositorio(dataset_onto.coleccion_de_datos >> repo_onto.repositorio):
    #         pass
    #
    #     # ToDo: No tiene sentido del todo tener las instancias "caracteristicas"
    #     class presenta_caracteristica_de_coleccion_de_datos(dataset_onto.coleccion_de_datos >> repo_onto.soporte_para_caracteristica_de_cdd):
    #         pass
    #
    #     # ToDo: No tiene sentido del todo tener las instancias "caracteristicas"
    #     class presenta_caracteristica_de_productor_de_datos(dataset_onto.productor_de_datos >> repo_onto.caracteristica_de_productor_de_datos):
    #         pass


if __name__ == '__main__':
    initiate()
    ow.JAVA_EXE = "/usr/bin/java"
    ow.sync_reasoner()
    if len(list(ow.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
