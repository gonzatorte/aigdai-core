import owlready2 as ow

if __name__ == '__main__':
    # from ontologies import example_world
    # example_world.initiate()

    from ontologies import full
    full.initiate()

    ow.JAVA_EXE = "/usr/bin/java"
    ow.sync_reasoner()
    if len(list(ow.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')

    # def render_using_label(entity):
    #     return entity.label.first() or entity.name
    #     return entity.iri
    # set_render_func(render_using_label)

    graph = ow.default_world.as_rdflib_graph()
    print(graph.serialize(format="ttl"))

    # owlready2.default_world.set_backend(filename="../world.sqlite3")
    # owlready2.default_world.save()
    # full_ontology.onto.save(file="full-onto.owl", format="rdfxml")
