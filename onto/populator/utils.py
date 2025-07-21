import onto.populator.rdf_types as rdf_types
from lib.no_relational_database import get_database_client
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, OWL
import config


def owl_all_different(g, instances):
    for (idx, instance1) in enumerate(instances):
        for instance2 in instances[idx+1:]:
            g.add((instance1, OWL.differentFrom, instance2))


def refine_and_insert_on_rdf():
    g_repos = Graph()
    # g = Graph(store="BerkeleyDB")
    # g.open("/some/folder/location")
    # g.close()
    # g.parse("....")
    g_repos.bind('', rdf_types.my_ns)

    (g_criterios, ) = seed_criterios()
    (g_disciplinas, ) = seed_disciplinas()
    (g_commons, ) = seed_commons()
    (g_locaciones, ) = seed_locaciones()

    # database = get_database_async()
    database = get_database_client()
    # drepo_collection = database['drepo']
    raw_drepo_collection = database['raw_drepo']
    skip_count = 0
    limit_count = 0
    instances = raw_drepo_collection.find({}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    # instances_count = raw_drepo_collection.count_documents({})
    instance_ids = raw_drepo_collection.find({}, {'idd': True}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    instance_ids = [x['idd'] for x in instance_ids]

    # rdf_ids = {x: URIRef("repositorio/%s" % (x,), my_ns) for x in instance_ids}
    # not_repeated_ids = [x for x in instance_ids if rdf_ids[x] not in g[rdf_ids[x]]]
    not_repeated_ids = instance_ids

    repository_infos = refine_iterator(instances, not_repeated_ids, True)
    total = len(repository_infos)
    print("To process %s" % (total, ))
    counter = 0
    for r_info in repository_infos:
        process(r_info)
        counter += 1
        if counter % 10 == 0:
            print("ready %s out of %s" % (counter, total))
    return g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones


def reason_on_memory():
    # g_repos, g_commons, g_criterios, g_disciplinas, g_locaciones = refine_and_insert_on_rdf()
    # g_orgs = insert_on_rdf()
    import owlready2 as ow

    ow.JAVA_EXE = config.JAVA_EXE_PATH
    ow.onto_path.append('../owl/')

    # from io import BytesIO
    # my_str_as_bytes = str.encode(my_str)  # convert to binary
    # fobj = BytesIO(my_str_as_bytes)
    # abox = ow.get_ontology("some-random-path").load(fileobj=fobj)

    tbox = ow.get_ontology('file://../owl/aigdai-tbox.owl').load(only_local=True)

    for data_file_path in [
        'repositorios.xml',
        'criterios.xml',
        'disciplinas.xml',
        'commons.xml',
        'localizaciones.xml',
        'organizaciones.xml',
    ]:
        # ow.get_ontology('file://%s' % (data_file_path,)).load(only_local=True)
        # tbox.imported_ontologies.append(ow.get_ontology('file://../owl/%s' % (data_file_path,)))
        tbox.imported_ontologies.append(ow.get_ontology('file:///home/gonzalo/workspace/propio/AIGDAI/aigdai-core/onto/owl/%s' % (data_file_path,)))
        # tbox.imported_ontologies.append('file://%s' % (data_file_path,))

    ow.sync_reasoner([tbox], ignore_unsupported_datatypes=True, infer_property_values=True)
    # ow.sync_reasoner_pellet([tbox], infer_data_property_values=True, infer_property_values=True, debug=2)
    # with tbox:
    #     ow.sync_reasoner()

    if len(list(ow.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')

    print(list(tbox.individuals()))
    # print(list(tbox.graph.triples((None, None, None))))


def find_or_fail(ll, searcher, error_factory):
    try:
        return next(filter(searcher, ll))
    except StopIteration:
        raise error_factory()


if __name__ == '__main__':
    reason_on_memory()
