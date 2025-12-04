from jpype import *
import jpype.imports
jpype.addClassPath('elk/elk-owlapi-library-0.6.0.jar')
# jpype.addClassPath('HermiT/HermiT.jar')
jpype.addClassPath('./owlapi-distribution-4.5.22.jar')
# jpype.addClassPath('./owlapi-dependencypack-5.1.9.jar')
jpype.addClassPath('./slf4j-simple-1.7.36.jar')
jpype.addClassPath('./slf4j-api-1.7.36.jar')
jpype.addClassPath('./guava-31.1-jre.jar')
jpype.addClassPath('./caffeine-2.8.8.jar')
jpype.addClassPath('./javax.inject-1.jar')
jpype.addClassPath('./commons-io-2.11.0.jar')
jpype.addClassPath('./hppcrt-0.7.2.jar')
jpype.startJVM(convertStrings=False)

# java.lang.System.out.println(jpype.getClassPath())
# from org.semanticweb.HermiT.cli import CommandLine

from org.semanticweb.owlapi.apibinding import OWLManager
from org.semanticweb.elk.owlapi import ElkReasonerFactory
from org.semanticweb.owlapi.reasoner import InferenceType
from org.semanticweb.owlapi.util import InferredOntologyGenerator, SimpleIRIMapper
from java.io import BufferedOutputStream, FileOutputStream, PrintWriter, File
# from org.semanticweb.owlapi.util import AutoIRIMapper
from org.semanticweb.owlapi.model import IRI

manager = OWLManager.createOWLOntologyManager()

# mapper = AutoIRIMapper(java.io.File("./onto/owl/"), True)
imported_base_iri = IRI.create("http://aigdai.base.owl")
local_file_base_iri = IRI.create(java.io.File("./onto/owl/base.owl"))
mapper = SimpleIRIMapper(imported_base_iri, local_file_base_iri)
manager.addIRIMapper(mapper)

imported_criterios_iri = IRI.create("http://aigdai.criterios.owl")
local_file_criterios_iri = IRI.create(java.io.File("./onto/owl/criterios.owl"))
mapper = SimpleIRIMapper(imported_criterios_iri, local_file_criterios_iri)
manager.addIRIMapper(mapper)

imported_lenguajes_iri = IRI.create("http://aigdai.lenguajes.owl")
local_file_lenguajes_iri = IRI.create(java.io.File("./onto/owl/lenguajes.owl"))
mapper = SimpleIRIMapper(imported_lenguajes_iri, local_file_lenguajes_iri)
manager.addIRIMapper(mapper)

inputOntologyFile = java.io.File('./onto/owl/aigdai-tbox.owl')

ontology = manager.loadOntologyFromOntologyDocument(inputOntologyFile)

factory = ElkReasonerFactory()
reasoner = factory.createReasoner(ontology)
reasoner.precomputeInferences(InferenceType.values())
inferred_ontology = manager.createOntology()
gen = InferredOntologyGenerator(reasoner)

df = manager.getOWLDataFactory()
cls = df.getOWLClass("http://aigdai.tbox.owl/repositorio")
for s in reasoner.getInstances(cls, False).getFlattened():
    print("Instance:", s)
