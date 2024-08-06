import owlready2
import os


def fetch_ontology(name, url):
    # export_format = 'ntriples'
    export_format = 'rdf'
    rel_filename = "./ontology_cache/%s.%s" % (name, export_format)
    abs_filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), rel_filename)
    try:
        onto = owlready2.get_ontology('file://%s' % (abs_filename,)).initiate()
    except FileNotFoundError:
        # my_world = owlready2.World()
        # my_world.get_ontology(url).load()
        # save_as_ttl(name, my_world)
        # my_world.close()
        # onto = owlready2.get_ontology('file://%s' % (abs_filename,)).load()

        onto = owlready2.get_ontology(url).initiate()
        # onto.save(file=abs_filename, format="rdfxml")
        onto.save(file=abs_filename, format="rdfxml" if export_format == 'rdf' else 'ntriples')
    return onto


def save_as_ttl(name, world):
    rel_filename = "./ontology_cache/%s.ttl" % (name, )
    abs_filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), rel_filename)
    graph = owlready2.default_world.as_rdflib_graph()
    file = open(abs_filename, 'w')
    file.write(graph.serialize(format="ttl"))
    file.close()
