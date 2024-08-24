from .base import onto as base_onto, initiate as base_initiate
from .dataset import onto as dataset_onto, initiate as dataset_initiate
from .repo import onto as repo_onto, initiate as repo_initiate
from .full import onto as full_onto, initiate as full_initiate

from owlready2 import *

onto = get_ontology("http://test.org/example_world.owl")


def initiate():
    base_initiate()
    dataset_initiate()
    repo_initiate()
    full_initiate()
    with onto:
        tipo_de_id_ror = base_onto.tipo_de_id_de_organizacion('ROR')
        # GRID está deprecado ¿incluirlo por completitud?
        # tipo_de_id_de_organizacion('GRID')
        base_onto.tipo_de_id_de_organizacion('ISNI')

        repo_onto.repositorio('the_world_bank_open_data')
        repo_onto.repositorio('worldwide_protein_data_bank')
        repo_onto.repositorio('4tu_researchdata')
        repo_onto.repositorio('dryad')
        rda_unr = repo_onto.repositorio('rda_unr')

        [ckan, dataverse, dspace, otro_motor] = map(lambda x: repo_onto.motor_de_repositorio(x), [
            'ckan',
            'dataverse',
            'dspace',
            # ToDo: Siempre se tiene que agregar la categoria "otro", no así para "desconocido"
            #  ojo que el motor otro no cumple ser identico a otro motor que sea "otro". Como modelamos eso?
            #   diciendo que el motor otro no puede tener ninguna feature asociada para que no se pueda inferir nada del
            #    mismo o que puedan compartir erroneamente inferencias?
            #   funciona de algún modo como el NULL en bases de datos
            'otro',
        ])

        lareferencia = repo_onto.agregador('lareferencia')
        google_datasetsearch = repo_onto.agregador('google_datasetsearch')

        re3data = repo_onto.catalogo_de_repositorio('re3data')
        fairsharing = repo_onto.catalogo_de_repositorio('fairsharing')
        opendoar = repo_onto.catalogo_de_repositorio('opendoar')

        some_dataset = dataset_onto.cdd('doi:10.57715/UNR/PEFY4Q')

        decreto_478_2013 = repo_onto.agregador('Decreto_478_2013')
        ley_104 = repo_onto.agregador('Ley104')

        unr = base_onto.organizacion('unr')
        # print('universidad_de_rosario', unr.get_properties(), base_onto.se_ubica_en.domain)
        unr.se_ubica_en = base_onto.pais('ARG')
        unr_identificacion_dada_por_ror = base_onto.id_de_organizacion('02tphfq59')
        unr_identificacion_dada_por_ror.id_de_organizacion_tiene_tipo = tipo_de_id_ror
        unr_identificacion_dada_por_ror.id_de_organizacion_tiene_literal = '02tphfq59'
        unr_identificacion_dada_por_ror.id_de_organizacion_tiene_organizacion = unr

        unr.tipo_de_organizacion = 'no-comercial'

        rda_unr.utiliza_motor = dataverse
        rda_unr.es_cosechado_por.append(lareferencia)
        relacion_unr_unrrda = repo_onto.relacion_repositorio_y_organizacion('unr_mantiene_urn_rda')
        relacion_unr_unrrda.relacion_repositorio_y_organizacion_tiene_organizacion = unr
        relacion_unr_unrrda.relacion_repositorio_y_organizacion_tiene_repositorio = rda_unr
        relacion_unr_unrrda.tiene_tipo_de_relacion_con_organizacion = "administrativa"
        rda_unr.usa_lenguaje.append('spa')
        r3d100013960 = repo_onto.id_de_catalogacion_de_repositorio('r3d100013960')
        r3d100013960.id_de_catalogacion_de_repositorio_tiene_catalogo = re3data
        r3d100013960.id_de_catalogacion_de_repositorio_tiene_repositorio = rda_unr
        r3d100013960.id_de_catalogacion_de_repositorio_tiene_literal = 'r3d100013960'


if __name__ == '__main__':
    initiate()
    import owlready2
    owlready2.JAVA_EXE = "/usr/bin/java"
    owlready2.sync_reasoner()
    if len(list(owlready2.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
