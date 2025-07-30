import owlready2 as ow

onto_base_path = '../owl/'
# onto_base_path = 'onto/owl/'
# ow.onto_path.append('./%s' % (onto_base_path,))
# ow.PREDEFINED_ONTOLOGIES['http://base.owl/v0.1/'] = './%sbase.owl' % (onto_base_path,)
# ow.default_world.ontologies
onto_base = ow.get_ontology('file://%sbase.owl' % (onto_base_path,)).load(only_local=True)
onto_criterios = ow.get_ontology('file://%scriterios.owl' % (onto_base_path,)).load(only_local=True)
onto_lenguajes = ow.get_ontology('file://%slenguajes.owl' % (onto_base_path,)).load(only_local=True)
onto_tbox = ow.get_ontology('file://%saigdai-tbox.owl' % (onto_base_path,)).load(only_local=True)
onto_elements = {}
for onto_element in [
    {
        **{x.name: (x, t) for x in t.classes()},
        **{x.name: (x, t) for x in t.properties()},
    } for t in [
        onto_base,
        onto_criterios,
        onto_lenguajes,
        onto_tbox,
    ]
]:
    onto_elements.update(onto_element)

ontology_graph = ow.default_world.as_rdflib_graph()
