from owlready2 import *

# from . import util
# foaf_ns = owlready2.get_ontology("http://xmlns.com/foaf/0.1/").load()
# foaf_ns = util.fetch_ontology('foaf-2010', "http://xmlns.com/foaf/spec/20100809.rdf").load()
# foaf_ns = util.fetch_ontology('foaf-2007', "http://xmlns.com/foaf/spec/20070114.rdf").load()
# foaf_ns = util.fetch_ontology('foaf', "http://xmlns.com/foaf/spec/20140114.rdf").load()
# foaf_ns = get_ontology("http://test.org/base.owl")


onto = get_ontology('http://test.org/fake-foaf.owl')


def initiate():
    with onto:
        class Person(Thing):
            pass

        class Organization(Thing):
            pass

        class Document(Thing):
            pass

        # class name(Datatype):
        #     domain = [Thing]
        #     range = [str]

        class name(object):
            def __init__(self, value):
                self.value = value

        def name_parser(s):
            return name(s)

        def name_unparser(x):
            return x.value

        declare_datatype(name, "http://test.org/fake-foaf.owl#name", name_parser, name_unparser)

        def url_parser(s):
            return name(s)

        def url_unparser(x):
            return x.value

        class url(Datatype):
            domain = [Thing]
            range = [str]
        declare_datatype(url, "http://test.org/fake-foaf.owl#url", url_parser, url_unparser)


if __name__ == '__main__':
    initiate()
    import owlready2
    owlready2.JAVA_EXE = "/usr/bin/java"
    owlready2.sync_reasoner()
    if len(list(owlready2.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
