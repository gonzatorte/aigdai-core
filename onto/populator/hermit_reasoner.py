"""HermiT through the OWL API (not owlready2), on two subgraphs of the populated graph.

Used with populate --dl-reasoner. HermiT does not scale to the whole graph, and Jena already covers hierarchies,
domains, ranges and equality from functional properties. HermiT is only used for what Jena does not do:

- Reconciliation subgraph: the repository identifiers (type, catalog, literal and repository), the type of the
  repositories they name and of the catalogs. HermiT applies the functional id_de_repositorio_tiene_repositorio and
  returns the owl:sameAs between repositories. The HasKey axioms are removed before reasoning (see _reasoner_on).
- Chains subgraph: the triples of the properties that take part in the property chains of the TBox
  (SubObjectPropertyOf with ObjectPropertyChain). It returns the inferred values of the property each chain defines.

The owl:AllDifferent of each group, statistics, policies and data properties other than the keys are left out.
An owl:AllDifferent takes about two triples per member, but HermiT, like Jena, expands it to one inequality per pair
of members, so its reasoning cost is still quadratic in the size of the group.
Even so, on the whole graph (some 45,000 triples in the reconciliation subgraph) HermiT did not finish in more than
20 minutes, while a sample of 3,900 triples took 15 s. Without --dl-reasoner, populate applies the same two rules in
Python (reconcile_repositories and materialize_property_chains).
The TBox is the original aigdai-tbox.owl read by the OWL API, so it keeps HasKey and DatatypeDefinition.
"""
import itertools
import logging
import os
import tempfile
import time

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF

import onto.populator.rdf_types as rdf_types
from onto.populator.owlapi import ONTOLOGY_DIR, load_ontology

logger = logging.getLogger('populate')
TBOX_IRI = 'http://aigdai.tbox.owl'


def reconciliation_subgraph(graph: Graph) -> Graph:
    sub = Graph()
    for p in (rdf_types.id_de_repositorio_tiene_catalogo, rdf_types.id_de_repositorio_tiene_literal,
              rdf_types.id_de_repositorio_tiene_repositorio):
        for triple in graph.triples((None, p, None)):
            sub.add(triple)
    for cls in (rdf_types.IdDeRepositorio, rdf_types.Repositorio, rdf_types.CatalogoDeRepositorios):
        for s in graph.subjects(RDF.type, cls):
            sub.add((s, RDF.type, cls))
    return sub


def property_chains(schema: Graph) -> list[tuple[URIRef, list[tuple[URIRef, bool]]]]:
    """The property chains of the schema: (property they define, [(property, whether it is inverted), ...])."""
    chains = []
    for (prop, chain) in schema.subject_objects(OWL.propertyChainAxiom):
        members = []
        for member in Collection(schema, chain):
            if isinstance(member, BNode):
                members.append((schema.value(member, OWL.inverseOf), True))
            else:
                members.append((member, False))
        chains.append((prop, members))
    return chains


def chain_properties(schema: Graph) -> tuple[set, set]:
    """(properties defined by a chain, every property that takes part in a chain), read from the schema."""
    defined, involved = set(), set()
    for (prop, members) in property_chains(schema):
        defined.add(prop)
        involved.add(prop)
        involved.update(member_prop for (member_prop, _) in members)
    return defined, involved


def chains_subgraph(graph: Graph, involved: set) -> Graph:
    sub = Graph()
    for p in involved:
        for triple in graph.triples((None, p, None)):
            sub.add(triple)
    return sub


def _reasoner_on(sub: Graph, staging: str, name: str):
    """Loads the subgraph as an ontology that imports the TBox and returns (manager, ontology, reasoner)."""
    from java.io import File
    from org.semanticweb.owlapi.model import IRI
    from org.semanticweb.owlapi.util import SimpleIRIMapper
    from org.semanticweb.HermiT import Configuration, Reasoner
    abox = Graph()
    abox += sub
    ontology_iri = URIRef('http://aigdai.abox/%s' % (name,))
    abox.add((ontology_iri, RDF.type, OWL.Ontology))
    abox.add((ontology_iri, OWL.imports, URIRef(TBOX_IRI)))
    path = os.path.join(staging, '%s.owl' % (name,))
    abox.serialize(destination=path, format='xml')
    manager, _ = load_ontology('aigdai-tbox.owl')
    manager.addIRIMapper(SimpleIRIMapper(IRI.create(TBOX_IRI), IRI.create(File(ONTOLOGY_DIR + 'aigdai-tbox.owl'))))
    ontology = manager.loadOntologyFromOntologyDocument(File(path))
    # Without the HasKey of the TBox: with them, HermiT does not finish (400 records per source took 64 s to check
    # consistency instead of 2.9 s; 1,600 did not finish in 10 minutes; the whole graph ran out of memory). They add no
    # owl:sameAs today: every identifier IRI depends only on its value, so two records with the same key share the
    # identifier node, and the functional id_de_repositorio_tiene_repositorio is enough. Only HermiT loses them.
    from org.semanticweb.owlapi.model import AxiomType
    for o in manager.getImportsClosure(ontology):
        manager.removeAxioms(o, o.getAxioms(AxiomType.HAS_KEY))
    configuration = Configuration()
    configuration.ignoreUnsupportedDatatypes = True
    return manager, ontology, Reasoner(configuration, ontology)


def infer_same_repositories(graph: Graph, staging: str) -> Graph:
    from org.semanticweb.owlapi.model import IRI
    sub = reconciliation_subgraph(graph)
    started = time.perf_counter()
    manager, _, reasoner = _reasoner_on(sub, staging, 'reconciliation')
    if not reasoner.isConsistent():
        raise RuntimeError('HermiT: the reconciliation subgraph is inconsistent')
    df = manager.getOWLDataFactory()
    repositories = set(sub.subjects(RDF.type, rdf_types.Repositorio))
    # getSameIndividuals is not complete for every member of a group: on the whole graph it left out 374 to 419 pairs
    # (the count changed between runs) whose equality follows from the pairs it did return for the same group, e.g.
    # a DOI record reported equal to the DataCite record but not to the FAIRsharing record that the DataCite one is
    # equal to. So the pairs are closed transitively before asserting them.
    parent = {repo: repo for repo in repositories}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for repo in repositories:
        individual = df.getOWLNamedIndividual(IRI.create(str(repo)))
        for other in reasoner.getSameIndividuals(individual).getEntities():
            other_iri = URIRef(str(other.getIRI()))
            if other_iri in parent:
                parent[find(repo)] = find(other_iri)
    groups = {}
    for repo in repositories:
        groups.setdefault(find(repo), []).append(repo)
    inferred = Graph()
    for members in groups.values():
        for (a, b) in itertools.combinations(sorted(members), 2):
            inferred.add((a, OWL.sameAs, b))
    logger.info('hermit reconciliation: %s triples in, %s owl:sameAs between repositories, %.1f s',
                len(sub), len(inferred), time.perf_counter() - started)
    return inferred


def infer_chain_values(graph: Graph, schema: Graph, staging: str) -> Graph:
    from org.semanticweb.owlapi.model import IRI
    defined, involved = chain_properties(schema)
    sub = chains_subgraph(graph, involved)
    started = time.perf_counter()
    manager, _, reasoner = _reasoner_on(sub, staging, 'chains')
    if not reasoner.isConsistent():
        raise RuntimeError('HermiT: the chains subgraph is inconsistent')
    df = manager.getOWLDataFactory()
    inferred = Graph()
    subjects = {s for p in involved for s in sub.subjects(p, None) if isinstance(s, URIRef)}
    for prop in defined:
        owl_prop = df.getOWLObjectProperty(IRI.create(str(prop)))
        for s in subjects:
            individual = df.getOWLNamedIndividual(IRI.create(str(s)))
            for value in reasoner.getObjectPropertyValues(individual, owl_prop).getFlattened():
                triple = (s, prop, URIRef(str(value.getIRI())))
                if triple not in graph:
                    inferred.add(triple)
    logger.info('hermit chains: %s properties defined by chains, %s triples in, %s inferred values, %.1f s',
                len(defined), len(sub), len(inferred), time.perf_counter() - started)
    return inferred


def hermit_inferences(graph: Graph, schema: Graph) -> tuple[Graph, Graph]:
    """(owl:sameAs between repositories, values of the chain properties) inferred by HermiT."""
    with tempfile.TemporaryDirectory(prefix='hermit-') as staging:
        return infer_same_repositories(graph, staging), infer_chain_values(graph, schema, staging)
