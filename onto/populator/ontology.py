"""The TBox (aigdai-tbox.owl and the ontologies it imports), loaded with the OWL API.

- onto_base, onto_criterios, onto_lenguajes, onto_tbox: each ontology, with its base_iri.
- onto_elements: name of each class, property and datatype -> (None, ontology it belongs to).
- ontology_graph: the RDF of the four ontologies, which is what gets loaded in Jena as schema.

It used to be loaded with owlready2, which drops HasKey and DatatypeDefinition when it reads OWL/XML.
"""
import typing

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from onto.populator.owlapi import load_ontology, to_rdflib


class Ontology(typing.NamedTuple):
    base_iri: str
    graph: Graph


_manager, _tbox = load_ontology('aigdai-tbox.owl')
_by_iri = {str(o.getOntologyID().getOntologyIRI()): o for o in _manager.getImportsClosure(_tbox)}


def _ontology(iri: str) -> Ontology:
    return Ontology(iri + '/', to_rdflib(_manager, _by_iri[iri]))


onto_base = _ontology('http://aigdai.base.owl')
onto_criterios = _ontology('http://aigdai.criterios.owl')
onto_lenguajes = _ontology('http://aigdai.lenguajes.owl')
onto_tbox = _ontology('http://aigdai.tbox.owl')

ENTITY_TYPES = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, RDFS.Datatype)
onto_elements = {}
for _onto in (onto_base, onto_criterios, onto_lenguajes, onto_tbox):
    for _type in ENTITY_TYPES:
        for _entity in _onto.graph.subjects(RDF.type, _type):
            if isinstance(_entity, URIRef) and str(_entity).startswith(_onto.base_iri):
                onto_elements[str(_entity)[len(_onto.base_iri):]] = (None, _onto)

ontology_graph = Graph()
for _onto in (onto_base, onto_criterios, onto_lenguajes, onto_tbox):
    ontology_graph += _onto.graph
