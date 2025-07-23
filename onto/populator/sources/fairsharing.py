from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
import onto.populator.common as common
from onto.populator.utils import owl_all_different, find_or_fail
import onto.cts as cts
import onto.populator.rdf_types as rdf_types


ENG_LNG_CODE = 'eng'
def process_repo(gg: Graph, info):
    if info['registry'] == "Standard":
        if info['type'] == "principle":
            pass
        elif info['type'] == "reporting_guideline":
            pass
        elif info['type'] == "terminology_artefact":
            pass
        elif info['type'] == "identifier_schema":
            pass
        elif info['type'] == "model_and_format":
            pass
        else:
            raise Exception()
    elif info['registry'] == "Policy":
        if info['type'] == "project":
            pass
        elif info['type'] == "funder":
            pass
        elif info['type'] == "institution":
            pass
        elif info['type'] == "journal_publisher":
            pass
        elif info['type'] == "journal":
            pass
        elif info['type'] == "society":
            pass
        else:
            raise Exception()
    elif info['registry'] == "Database":
        repositorio = URIRef("%s/%s" % (rdf_types.Repositorio.toPython(), info['_id'],), rdf_types.my_ns)
        repository_metadata = info['metadata']
        gg.set((repositorio, RDF.type, rdf_types.Repositorio))
        gg.set(
            (repositorio, rdf_types.tiene_nombre_repositorio, Literal(repository_metadata['name'], lang=ENG_LNG_CODE)))
        gg.set((repositorio, rdf_types.tiene_nombre_repositorio,
                Literal(repository_metadata['abbreviation'], lang=ENG_LNG_CODE)))
        gg.set((repositorio, rdf_types.tiene_descripcion_repositorio,
                Literal(repository_metadata['description'], lang=ENG_LNG_CODE)))
        gg.set((repositorio, rdf_types.tiene_url_repositorio, Literal(repository_metadata['homepage'])))
        if info['type'] == "knowledgebase":
            gg.set((repositorio, RDF.type, rdf_types.Agregador))
        elif info['type'] == "repository":
            gg.set((repositorio, RDF.type, rdf_types.Rdd))
        elif info['type'] == "knowledgebase_and_repository":
            gg.set((repositorio, RDF.type, rdf_types.Rdd))
            gg.set((repositorio, RDF.type, rdf_types.Agregador))
        else:
            raise Exception()
        # info['countries']
        # info['userDefinedTags']
        # info['subjects']
    else:
        raise Exception()
