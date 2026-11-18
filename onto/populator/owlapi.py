"""Access to the OWL API, HermiT and Jena from Python through jpype.

There is a single JVM per process, started with both jars: the OWL API is the one bundled in
reasoner/HermiT/HermiT.jar (used to load the ontology and by HermiT), and Jena is reasoner/jena (the same version as
Fuseki). Both only share a few classes of commons-logging. Unlike owlready2, the OWL API keeps every axiom of the
OWL/XML files, including HasKey and DatatypeDefinition.
"""
import os

import jpype
import jpype.imports
from rdflib import Graph

from settings import REASONER_HEAP, REASONER_JAVA_HOME

HERMIT_JAR = 'reasoner/HermiT/HermiT.jar'
JENA_JAR = 'reasoner/jena/jena-fuseki-server-5.1.0.jar'
ONTOLOGY_DIR = 'onto/owl/'
# Local files of the ontologies that aigdai-tbox.owl imports
LOCAL_IMPORTS = {
    'http://aigdai.base.owl': 'base.owl',
    'http://aigdai.criterios.owl': 'criterios.owl',
    'http://aigdai.lenguajes.owl': 'lenguajes.owl',
}


def start_jvm():
    if not jpype.isJVMStarted():
        jvm_path = os.path.join(REASONER_JAVA_HOME, 'lib', 'server', 'libjvm.so')
        if not os.path.exists(jvm_path):
            raise RuntimeError('No Java runtime at %s (REASONER_JAVA_HOME): see onto/README.md' % (REASONER_JAVA_HOME,))
        jpype.startJVM(jvm_path, '-Xmx%s' % (REASONER_HEAP,), classpath=[HERMIT_JAR, JENA_JAR], convertStrings=True)


def load_ontology(file_name: str):
    """Loads an ontology of onto/owl with its imports resolved to the local files. Returns (manager, ontology)."""
    start_jvm()
    from java.io import File
    from org.semanticweb.owlapi.apibinding import OWLManager
    from org.semanticweb.owlapi.model import IRI
    from org.semanticweb.owlapi.util import SimpleIRIMapper
    manager = OWLManager.createOWLOntologyManager()
    for iri, local_file in LOCAL_IMPORTS.items():
        manager.addIRIMapper(SimpleIRIMapper(IRI.create(iri), IRI.create(File(ONTOLOGY_DIR + local_file))))
    ontology = manager.loadOntologyFromOntologyDocument(File(ONTOLOGY_DIR + file_name))
    return manager, ontology


def to_rdflib(manager, ontology) -> Graph:
    """The ontology (without its imports) as an rdflib graph, through the OWL API RDF/XML writer.

    Not Turtle: lenguajes.owl has a list of hundreds of language codes and the rdflib Turtle parser recurses once
    per element of a list.
    """
    from java.io import ByteArrayOutputStream
    from org.semanticweb.owlapi.io import RDFXMLOntologyFormat
    out = ByteArrayOutputStream()
    manager.saveOntology(ontology, RDFXMLOntologyFormat(), out)
    graph = Graph()
    graph.parse(data=bytes(out.toByteArray()).decode('utf-8'), format='xml')
    return graph
