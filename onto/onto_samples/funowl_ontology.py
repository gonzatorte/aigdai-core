from rdflib import RDFS, OWL, Namespace, Graph
from funowl import OntologyDocument, Ontology

EX = Namespace("http://www.example.com/ontology1#")

o = Ontology("http://www.example.com/ontology1")
o.imports("http://www.example.com/ontology2")
o.annotation(RDFS.label, "An example")
o.annotation(EX.nombre_usual, "An example")
# (OWL.AnnotationProperty, "An example")

o.subClassOf(EX.Child, OWL.Thing)
EX.Child.nombre_usual('pepe')

doc = OntologyDocument(EX, o)
# print(str(doc))
g = Graph()
doc.to_rdf(g)
print(g.serialize(format="ttl"))
