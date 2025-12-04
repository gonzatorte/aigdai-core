from jpype import *
import jpype.imports
jpype.addClassPath('HermiT/HermiT.jar')
jpype.startJVM(convertStrings=False)

# java.lang.System.out.println(jpype.getClassPath())
# from org.semanticweb.HermiT.cli import CommandLine

# import org.semanticweb.owlapi.apibinding.OWLManager;
from org.semanticweb.owlapi.apibinding import OWLManager
from java.io import BufferedOutputStream, FileOutputStream, PrintWriter, File
from org.semanticweb.HermiT import Configuration
from org.semanticweb.HermiT.Reasoner import ReasonerFactory

manager = OWLManager.createOWLOntologyManager()
inputOntologyFile = java.io.File('./onto/owl/aigdai-tbox.owl')

ontology = manager.loadOntologyFromOntologyDocument(inputOntologyFile)
configuration = Configuration()

factory = ReasonerFactory()
reasoner = factory.createReasoner(ontology, configuration)
reasoner.dumpHierarchies(ww, True, True, True)
